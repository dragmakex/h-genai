import json
import inspect
from typing import List, Dict, Any
from haystack.dataclasses import ChatMessage, ChatRole
from agents import Agent, ToolCallingAgent
from tools import *
from concurrent.futures import ThreadPoolExecutor
from prompt import (
    tool_agent_instructions,
    tool_agent_prompt,
    contact_agent_prompt,
    logo_agent_prompt,
    budget_agent_prompt,
    project_agent_prompt
)
from util import get_commune_finances_by_siren, get_epci_finances_by_code

summary_fields = [
    "population",
    "data_from_year",
    "total_budget",
    "total_budget_per_person",
    "debt_repayment_capacity",
    "debt_ratio",
    "debt_duration",
]
financial_data_fields = [
    "management_savings_per_capita",
    "gross_savings_per_capita",
    "net_savings_per_capita",
    "management_savings_ratio",
    "gross_savings_ratio",
    "net_savings_ratio",
    "debt_service_to_operating_revenue_ratio",
]
comparitive_fields = [
    "municipality",
    "inter_municipality",
    "population",
    "data_from_year",
    "total_budget",
    "total_budget_per_person",
    "debt_repayment_capacity",
    "debt_ratio",
    "debt_duration",
]


def get_all_tools():
    """Get all functions marked as tools from tools module"""
    import tools

    return [
        obj
        for name, obj in inspect.getmembers(tools)
        if inspect.isfunction(obj) and hasattr(obj, "_is_tool")
    ]


class Orchestrator:
    def __init__(self, city_info):
        # Initialize different types of agents
        self.simple_agent = Agent()
        self.tool_agent = ToolCallingAgent(
            instructions=tool_agent_instructions, functions=get_all_tools()
        )

        # Store conversation history
        self.conversation_history: Dict[str, List[ChatMessage]] = {}

        # Load data from data.json
        self.data = self._load_data_fields()

        self.municipality_name = city_info.municipality_name
        self.inter_municipality_name = city_info.inter_municipality_name
        self.municipality_siren = city_info.siren
        self.inter_municipality_epci = city_info.inter_municipality_code
        self.reference_sirens = city_info.reference_sirens

        self.financial_api_data = self._get_numeric_api_data()

    def _load_data_fields(self) -> Dict[str, Any]:
        """Load data from data_template.json file"""
        try:
            with open("data_template.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(
                "data_template.json not found in the agent directory"
            )

    # def _get_municipality_name(self):
    #     """Get the input from the user"""
    #     return "Dijon"

    # def _get_inter_municipality_name(self):
    #     """Get the input from the user"""
    #     return input("Inter-Municipality: ")

    # def _get_inter_municipality_siren(self):
    #     """Get the input from the user"""
    #     return 212102313
    #     return "Dijon Metropole"

    # def _get_municipality_siren(self):
    #     """Get the input from the user"""
    #     return 212102313

    # def _get_inter_municipality_epci(self):
    #     """Get the input from the user"""
    #     return 242100410

    def _get_numeric_api_data(self):
        """Get the data from the API
        Return a dictionary with the data:
        Example:
        {"Dijon": {"population": 159346, "data_from_year": 2023, "total_budget": 110000000, "total_budget_per_person": 679, "debt_repayment_capacity": 3.4, "debt_ratio": 0.5, "debt_duration": 10},
        "Dijon Métropole": {"population": 159346, "data_from_year": 2023, "total_budget": 110000000, "total_budget_per_person": 679, "debt_repayment_capacity": 3.4, "debt_ratio": 0.5, "debt_duration": 10}}
        """
        _, _, municipality_finances = get_commune_finances_by_siren(
            self.municipality_siren)
        _, _, epci_finances = get_epci_finances_by_code(
            self.inter_municipality_epci)

        reference_finances = []
        for element in self.reference_sirens:
            _, _, ref = get_commune_finances_by_siren(element["siren"])
            reference_finances.append(ref)

        return {
            f"{self.municipality_name}": municipality_finances,
            f"{self.inter_municipality_name}": epci_finances,
            "reference_finances": reference_finances,
        }

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the conversation history in a serializable format"""

        if conversation_id not in self.conversation_history:
            return []

        return [
            {
                "role": msg.role.value,
                "content": msg.text,
                "timestamp": msg.metadata.get("timestamp", None),
            }
            for msg in self.conversation_history[conversation_id]
        ]

    def process_logo_field(self) -> None:
        conversation_id = "logo_retrieval"
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        # Create a prompt based on the field and append it to the messages
        prompt = logo_agent_prompt.format(name=self.municipality_name)
        self.conversation_history[conversation_id].append(
            ChatMessage.from_user(prompt))
        # print(self.conversation_history[conversation_id][-1])

        # Get response from agent and extend the conversation history with the response
        response = self.tool_agent.run(
            self.conversation_history[conversation_id])
        self.conversation_history[conversation_id].extend(response)
        # print(self.conversation_history[conversation_id][-1])

        # We call the agent again to get the final reply after the tool executions
        final_reply = self.tool_agent.run(
            self.conversation_history[conversation_id])
        self.conversation_history[conversation_id].extend(final_reply)
        # print(self.conversation_history[conversation_id][-1])

        # Store the response
        self.data["logo"]["content"] = (
            self.conversation_history[conversation_id][-1].text
            if final_reply
            else "unknown"
        )

        print("--------------------------------")
        print(self.conversation_history[conversation_id])
        print("--------------------------------")

        return ""

    def process_summary_fields(self, inter=False) -> None:
        """Process fields from the summary section"""
        if inter:
            identifier = "inter_municipality"
            name = self.inter_municipality_name
        else:
            identifier = "municipality"
            name = self.municipality_name

        fields = self.data["summary"][identifier]

        name_id = f"{identifier}_name"
        self.data[name_id]["content"] = name

        # Process each field in the municipality data
        for field, value in fields.items():
            # E.g. field = 'population'
            # E.g. value = {'type': 'number', 'content': null, 'instruction': 'Enter the total population of the municipality'}
            print("Field: " + name + " " + field)
            type = value["type"]
            instruction = value["instruction"]

            if field in summary_fields:
                self.data["summary"][identifier][field]["content"] = self.financial_api_data[name][field]
                print("Populated from API")
            else:
                conversation_id = identifier + "_" + field
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []

                if type == "array":
                    # Create the overall array instructions
                    array_prompt = tool_agent_prompt.format(
                        identifier=identifier,
                        name=name,
                        field=field,
                        instruction=instruction,
                        type=type,
                        example="",
                    )

                    # Process each item in the array sequentially
                    for idx, item in enumerate(value["content"]):
                        for subfield, subvalue in item.items():
                            # Create prompt for this specific array item
                            item_prompt = f"For item {idx+1} of the array:\n"
                            item_prompt += tool_agent_prompt.format(
                                identifier=identifier,
                                name=name,
                                field=subfield,
                                instruction=subvalue["instruction"],
                                type=subvalue["type"],
                                example=subvalue["example"],
                            )
                            if idx == 0:
                                item_prompt = array_prompt + item_prompt
                            self.conversation_history[conversation_id].append(
                                ChatMessage.from_user(item_prompt)
                            )

                            # print("--------------------------------")
                            # print(self.conversation_history[conversation_id])
                            # print("--------------------------------")

                            # Get response for this item
                            response = self.tool_agent.run(
                                self.conversation_history[conversation_id]
                            )
                            self.conversation_history[conversation_id].extend(
                                response)

                            # We call the agent again to get the final reply after the tool execution
                            if (
                                self.conversation_history[conversation_id][-1].role
                                != ChatRole.ASSISTANT
                            ):
                                final_reply = self.tool_agent.run(
                                    self.conversation_history[conversation_id]
                                )
                                self.conversation_history[conversation_id].extend(
                                    final_reply
                                )

                            # Store the response for this item
                            self.data["summary"][identifier][field]["content"][idx][
                                subfield
                            ]["content"] = self.conversation_history[conversation_id][
                                -1
                            ].text  # if final_reply else "unknown"
                else:
                    # Create a prompt based on the field and append it to the messages
                    prompt = tool_agent_prompt.format(
                        identifier=identifier,
                        name=name,
                        field=field,
                        instruction=instruction,
                        type=type,
                        example=value["example"],
                    )
                    self.conversation_history[conversation_id].append(
                        ChatMessage.from_user(prompt)
                    )
                    # print(self.conversation_history[conversation_id][-1])

                    # Get response from agent and extend the conversation history with the response
                    response = self.tool_agent.run(
                        self.conversation_history[conversation_id]
                    )
                    self.conversation_history[conversation_id].extend(response)
                    # print(self.conversation_history[conversation_id][-1])

                    # We call the agent again to get the final reply after the tool executions
                    final_reply = self.tool_agent.run(
                        self.conversation_history[conversation_id]
                    )
                    self.conversation_history[conversation_id].extend(
                        final_reply)
                    # print(self.conversation_history[conversation_id][-1])

                    # Store the response
                    self.data["summary"][identifier][field]["content"] = (
                        self.conversation_history[conversation_id][-1].text
                        if final_reply
                        else "unknown"
                    )

                print("--------------------------------")
                print(self.conversation_history[conversation_id])
                print("--------------------------------")

    def process_projects_fields(self, inter=False) -> None:
        """Process fields from the projects section"""
        if inter:
            identifier = "inter_municipality"
            name = self.inter_municipality_name
        else:
            identifier = "municipality"
            name = self.municipality_name

        fields = self.data["projects"][identifier]

        # Process each field in the project data
        for field, value in fields.items():
            print("Field: " + name + " " + field)
            type = value["type"]
            instruction = value["instruction"]

            conversation_id = identifier + "_" + field
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []

            if type == "array":
                # Create the overall array instructions
                array_prompt = project_agent_prompt.format(
                    identifier=identifier,
                    name=name,
                    field=field,
                    instruction=instruction,
                    type=type,
                    example="",
                )

                # Process each item in the array sequentially
                for idx, item in enumerate(value["content"]):
                    for subfield, subvalue in item.items():
                        # Create prompt for this specific array item
                        item_prompt = f"For item {idx+1} of the array:\n"
                        item_prompt += project_agent_prompt.format(
                            identifier=identifier,
                            name=name,
                            field=subfield,
                            instruction=subvalue["instruction"],
                            type=subvalue["type"],
                            example=subvalue["example"],
                        )
                        if idx == 0:
                            item_prompt = array_prompt + item_prompt
                        self.conversation_history[conversation_id].append(
                            ChatMessage.from_user(item_prompt)
                        )

                        # Get response for this item
                        response = self.tool_agent.run(
                            self.conversation_history[conversation_id]
                        )
                        self.conversation_history[conversation_id].extend(
                            response)

                        # We call the agent again to get the final reply after the tool execution
                        if (
                            self.conversation_history[conversation_id][-1].role
                            != ChatRole.ASSISTANT
                        ):
                            final_reply = self.tool_agent.run(
                                self.conversation_history[conversation_id]
                            )
                            self.conversation_history[conversation_id].extend(
                                final_reply
                            )

                        # Store the response for this item
                        self.data["projects"][identifier][field]["content"][idx][
                            subfield
                        ]["content"] = self.conversation_history[conversation_id][
                            -1
                        ].text  # if final_reply else "unknown"
            else:
                # Create a prompt based on the field and append it to the messages
                prompt = project_agent_prompt.format(
                    identifier=identifier,
                    name=name,
                    field=field,
                    instruction=instruction,
                    type=type,
                    example=value["example"],
                )
                self.conversation_history[conversation_id].append(
                    ChatMessage.from_user(prompt)
                )
                # print(self.conversation_history[conversation_id][-1])

                # Get response from agent and extend the conversation history with the response
                response = self.tool_agent.run(
                    self.conversation_history[conversation_id]
                )
                self.conversation_history[conversation_id].extend(response)
                # print(self.conversation_history[conversation_id][-1])

                # We call the agent again to get the final reply after the tool executions
                final_reply = self.tool_agent.run(
                    self.conversation_history[conversation_id]
                )
                self.conversation_history[conversation_id].extend(final_reply)
                # print(self.conversation_history[conversation_id][-1])

                # Store the response
                self.data["projects"][identifier][field]["content"] = (
                    self.conversation_history[conversation_id][-1].text
                    if final_reply
                    else "unknown"
                )

            print("--------------------------------")
            print(self.conversation_history[conversation_id])
            print("--------------------------------")

    def process_contact_fields(self) -> None:
        """Process fields from the contacts section"""
        fields = self.data["contacts"]

        array_prompt = contact_agent_prompt.format(
            municipality=self.municipality_name,
            field="contacts",
            instruction=fields["instruction"],
            type=fields["type"],
            example="",
        )
        conversation_id = "contacts"
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []

        # Process each item in the array sequentially
        for idx, item in enumerate(fields["content"]):
            for subfield, subvalue in item.items():
                # Create prompt for this specific array item
                item_prompt = contact_agent_prompt.format(
                    municipality=self.municipality_name,
                    field=subfield,
                    instruction=subvalue["instruction"],
                    type=subvalue["type"],
                    example=subvalue["example"],
                )
                if idx == 0:
                    item_prompt = array_prompt + item_prompt
                self.conversation_history[conversation_id].append(
                    ChatMessage.from_user(item_prompt)
                )

                # Get response for this item
                response = self.tool_agent.run(
                    self.conversation_history[conversation_id]
                )
                self.conversation_history[conversation_id].extend(response)

                # We call the agent again to get the final reply after the tool execution
                if (
                    self.conversation_history[conversation_id][-1].role
                    != ChatRole.ASSISTANT
                ):
                    final_reply = self.tool_agent.run(
                        self.conversation_history[conversation_id]
                    )
                    self.conversation_history[conversation_id].extend(
                        final_reply)

                # Store the response for this item
                self.data["contacts"]["content"][idx][subfield][
                    "content"
                ] = self.conversation_history[conversation_id][
                    -1
                ].text  # if final_reply else "unknown"

        print("--------------------------------")
        print(self.conversation_history[conversation_id])
        print("--------------------------------")

    def process_budget_fields(self) -> None:
        identifiers = ["municipality", "inter_municipality"]
        for identifier in identifiers:
            if identifier == "inter_municipality":
                name = self.inter_municipality_name
            else:
                name = self.municipality_name
            
            fields = self.data["budget"][identifier]
            # Process each field in the municipality data
            for field, value in fields.items():
                # E.g. field = 'population'
                # E.g. value = {'type': 'number', 'content': null, 'instruction': 'Enter the total population of the municipality'}
                print("Field: " + name + " " + field)
                type = value["type"]
                instruction = value["instruction"]

                conversation_id = identifier + "_budegt_" + field
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []

                # Create a prompt based on the field and append it to the messages
                prompt = budget_agent_prompt.format(
                    identifier=identifier,
                    name=name,
                    field=field,
                    instruction=instruction,
                    type=type,
                    example=value["example"],
                )
                self.conversation_history[conversation_id].append(
                    ChatMessage.from_user(prompt)
                )
                # print(self.conversation_history[conversation_id][-1])

                # Get response from agent and extend the conversation history with the response
                response = self.tool_agent.run(
                    self.conversation_history[conversation_id]
                )
                self.conversation_history[conversation_id].extend(response)
                # print(self.conversation_history[conversation_id][-1])

                # We call the agent again to get the final reply after the tool executions
                final_reply = self.tool_agent.run(
                    self.conversation_history[conversation_id]
                )
                self.conversation_history[conversation_id].extend(
                    final_reply)
                # print(self.conversation_history[conversation_id][-1])

                # Store the response
                self.data["budget"][identifier][field]["content"] = (
                    self.conversation_history[conversation_id][-1].text
                    if final_reply
                    else "unknown"
                )

                print("--------------------------------")
                print(self.conversation_history[conversation_id])
                print("--------------------------------")

    def process_financial_data(self) -> None:
        """Process fields from the financial data section"""
        municipality = self.data["financial_data"]["municipality"]
        inter_municipality = self.data["financial_data"]["inter_municipality"]

        for field, value in municipality.items():
            if field in financial_data_fields:
                municipality[field]["content"] = self.financial_api_data[self.municipality_name][field]

        for field, value in inter_municipality.items():
            if field in financial_data_fields:
                inter_municipality[field]["content"] = self.financial_api_data[self.inter_municipality_name][field]

    def process_comparative_data(self) -> None:
        """Process fields from the comparative data section"""
        for i, ref_municipality in enumerate(self.data["comparative_data"]['content']):
            for field, value in ref_municipality.items():
                if field in comparitive_fields:
                    ref_municipality[field]["content"] = self.financial_api_data["reference_finances"][i][field]

    def process_all_sections(self) -> Dict[str, Any]:
        """Process all fields in data_template.json and save results to data_answer.json"""
        self.process_summary_fields(inter=False)
        self.process_summary_fields(inter=True)
        self.process_projects_fields(inter=False)
        self.process_projects_fields(inter=True)
        self.process_contact_fields()
        self.process_budget_fields()
        self.process_financial_data()
        self.process_comparative_data()

        # Save to answer.json
        try:
            with open("data_answer.json", "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to answer.json: {e}")

        return self.data

    def parallel_process_all_sections(self) -> Dict[str, Any]:
        """Process all fields in data_template.json and save results to data_answer.json"""
        # Define the tasks we want to run in parallel
        tasks = [
            (self.process_summary_fields, (False,)),
            (self.process_summary_fields, (True,)),
            (self.process_projects_fields, (False,)),
            (self.process_projects_fields, (True,)),
            (self.process_contact_fields, ()),
            (self.process_budget_fields, ()),
            (self.process_financial_data, ()),
            (self.process_comparative_data, ())
        ]

        # Run tasks in parallel
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(func, *args) for func, args in tasks]

            # Wait for all tasks to complete
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in parallel execution: {e}")

        # Save to answer.json
        try:
            with open("data_answer.json", "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to answer.json: {e}")

        return self.data


class city_info:
    municipality_name = "Le Havre"
    inter_municipality_name = "CU Le Havre Seine Métropole"
    siren = 217603513
    inter_municipality_code = 200084952
    reference_sirens = [
        {"siren": "217605401"},
        {"siren": "211401187"},
        {"siren": "200056844"},
    ]

# class city_info:
#     municipality_name = "Dijon"
#     inter_municipality_name = "Dijon Métropole"
#     siren = 212102313
#     inter_municipality_code = 242100410
#     reference_sirens = [
#         {"siren": "212500565"},
#         {"siren": "217100767"},
#         {"siren": "219000106"},
#     ]


test_orchestrator = Orchestrator(city_info)
test_orchestrator.parallel_process_all_sections()
