import json
from typing import Any, Dict, List

from agents import Agent, ToolCallingAgent
from haystack.dataclasses import ChatMessage
from prompt import tool_agent_instructions, tool_agent_prompt
from tools import get_sonar_pro_response, get_sonar_response, parse_docs, search_func


class Orchestrator:
    def __init__(self):
        # Initialize different types of agents
        self.simple_agent = Agent()
        self.tool_agent = ToolCallingAgent(
            instructions=tool_agent_instructions, functions=[get_sonar_pro_response]
        )

        # Store conversation history
        self.conversation_history: Dict[str, List[ChatMessage]] = {}

        # Load data from data.json
        self.data = self._load_data_fields()
        self.data_example = self._load_data_example()

    def _load_data_fields(self) -> Dict[str, Any]:
        """Load data from data_template.json file"""
        try:
            with open("data_template.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(
                "data_template.json not found in the agent directory"
            )

    def _load_data_example(self) -> Dict[str, Any]:
        """Load data from data_example.json file"""
        try:
            with open("data_example.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(
                "data_example.json not found in the agent directory"
            )

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

    def process_summary_municipality_fields(self) -> None:
        """Process municipality fields from the summary section"""
        fields = self.data["summary"]["municipality"]
        examples = self.data_example["summary"]["municipality"]

        name = input("Which Municipality do you want to get data for: ")
        self.data["municipality_name"]["content"] = name

        # Process each field in the municipality data
        for field, value in fields.items():
            # E.g. field = 'population'
            # E.g. value = {'type': 'number', 'content': null}
            print(field)
            type = value["type"]
            example = examples[field]["content"]

            conversation_id = field
            # Initialize conversation history for this area if it doesn't exist
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []

            # Create a prompt based on the field and append it to the messages
            prompt = tool_agent_prompt.format(
                name=name, field=field, type=type, example=example
            )
            self.conversation_history[conversation_id].append(
                ChatMessage.from_user(prompt)
            )

            # Get response from agent and extend the conversation history with the response
            response = self.tool_agent.run(self.conversation_history[conversation_id])
            self.conversation_history[conversation_id].extend(response)

            # We call the agent again to get the final reply after the tool execution
            final_reply = self.tool_agent.run(
                self.conversation_history[conversation_id]
            )
            self.conversation_history[conversation_id].extend(final_reply)

            # Store the response
            self.data["summary"]["municipality"][field]["content"] = (
                self.conversation_history[conversation_id][-1].text
                if final_reply
                else ""
            )

    def process_all_fields(self) -> Dict[str, Any]:
        """Process all fields in data_template.json and save results to data_answer.json"""
        self.process_summary_municipality_fields()

        # Save to answer.json
        try:
            with open("data_answer.json", "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to answer.json: {e}")

        return self.data


test_orchestrator = Orchestrator()
test_orchestrator.process_all_fields()
