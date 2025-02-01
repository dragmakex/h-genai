import json
import inspect
from typing import List, Dict, Any
from haystack.dataclasses import ChatMessage, ChatRole
from agents import Agent, ToolCallingAgent
from tools import *
from prompt import tool_agent_instructions, tool_agent_prompt

api_fields = ['population', 'data_from_year', 'total_budget', 'total_budget_per_person', 'debt_repayment_capacity', 'debt_ratio', 'debt_duration']

def get_all_tools():
    """Get all functions marked as tools from tools module"""
    import tools
    return [obj for name, obj in inspect.getmembers(tools) 
            if inspect.isfunction(obj) and hasattr(obj, '_is_tool')]

class Orchestrator:
    def __init__(self):
        # Initialize different types of agents
        self.simple_agent = Agent()
        self.tool_agent = ToolCallingAgent(
            instructions=tool_agent_instructions,
            functions=get_all_tools())

        # Store conversation history
        self.conversation_history: Dict[str, List[ChatMessage]] = {}
        
        # Load data from data.json
        self.data = self._load_data_fields()
        self.data_example = self._load_data_example()

        self.municipality_name = self._get_municipality_name()
        self.inter_municipality_name = self._get_inter_municipality_name()

        self.numeric_api_data = self._get_numeric_api_data(self.municipality_name, self.inter_municipality_name)
     
    def _load_data_fields(self) -> Dict[str, Any]:
        """Load data from data_template.json file"""
        try:
            with open('data_template.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("data_template.json not found in the agent directory")
        
    def _load_data_example(self) -> Dict[str, Any]:
        """Load data from data_example.json file"""
        try:
            with open('data_example.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("data_example.json not found in the agent directory")
        
    def _get_municipality_name(self):
        """Get the input from the user"""
        return input("Municipality: ")
    
    def _get_inter_municipality_name(self):
        """Get the input from the user"""
        return input("Inter-Municipality: ")
    
    def _get_numeric_api_data(self, municipality_name: str, inter_municipality_name: str):
        """Get the data from the API
        Return a dictionary with the data:
        Example:
        {"Dijon": {"population": 159346, "data_from_year": 2023, "total_budget": 110000000, "total_budget_per_person": 679, "debt_repayment_capacity": 3.4, "debt_ratio": 0.5, "debt_duration": 10},
        "Dijon Métropole": {"population": 159346, "data_from_year": 2023, "total_budget": 110000000, "total_budget_per_person": 679, "debt_repayment_capacity": 3.4, "debt_ratio": 0.5, "debt_duration": 10}}"""
        return {}


    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the conversation history in a serializable format"""

        if conversation_id not in self.conversation_history:
            return []
        
        return [
            {
                "role": msg.role.value,
                "content": msg.text,
                "timestamp": msg.metadata.get("timestamp", None)
            }
            for msg in self.conversation_history[conversation_id]
        ]

    def process_summary_fields(self, inter=False) -> None:
        """Process fields from the summary section"""
        if inter:
            identifier = 'inter_municipality'
            name = self.inter_municipality_name
        else:
            identifier = 'municipality'
            name = self.municipality_name


        fields = self.data['summary'][identifier]
        examples = self.data_example['summary'][identifier]

        name_id = f"{identifier}_name"
        self.data[name_id]['content'] = name

        # Process each field in the municipality data
        for field, value in fields.items():
            # E.g. field = 'population'
            # E.g. value = {'type': 'number', 'content': null, 'instruction': 'Enter the total population of the municipality'}
            print("Field: " + name + " " + field)
            type = value['type']
            instruction = value['instruction']
            example = examples[field]['content']

            # if field != 'historical_milestones':
            #     continue

            conversation_id = identifier + "_" + field
            if conversation_id not in self.conversation_history:

                self.conversation_history[conversation_id] = []

            if type == 'array':             
                # Create the overall array instructions
                array_prompt = tool_agent_prompt.format(
                    identifier=identifier,
                    name=name,
                    field=field,
                    instruction=instruction,
                    type=type,
                    example=example
                )
                
                # Process each item in the array sequentially
                for idx, item in enumerate(value['content']):
                    for subfield, subvalue in item.items():                       
                        # Create prompt for this specific array item
                        item_prompt = f"For item {idx+1} of the array:\n"
                        item_prompt += tool_agent_prompt.format(identifier=identifier, name=name, field=subfield, instruction=subvalue['instruction'], type=subvalue['type'], example=example)
                        # if idx == 0:
                        #     item_prompt = array_prompt + item_prompt
                        self.conversation_history[conversation_id].append(ChatMessage.from_user(item_prompt))
                        
                        # Get response for this item
                        response = self.tool_agent.run(self.conversation_history[conversation_id])
                        self.conversation_history[conversation_id].extend(response)

                        # We call the agent again to get the final reply after the tool execution
                        if self.conversation_history[conversation_id][-1].role != ChatRole.ASSISTANT:
                            final_reply = self.tool_agent.run(self.conversation_history[conversation_id])
                            self.conversation_history[conversation_id].extend(final_reply)
                        
                        # Store the response for this item
                        self.data['summary'][identifier][field]['content'][idx][subfield]['content'] = self.conversation_history[conversation_id][-1].text #if final_reply else "unknown"           
            else: 
                # Create a prompt based on the field and append it to the messages
                prompt = tool_agent_prompt.format(identifier=identifier, name=name, field=field, instruction=instruction, type=type, example=example)
                self.conversation_history[conversation_id].append(ChatMessage.from_user(prompt))
                # print(self.conversation_history[conversation_id][-1])
                
                # Get response from agent and extend the conversation history with the response
                response = self.tool_agent.run(self.conversation_history[conversation_id])
                self.conversation_history[conversation_id].extend(response)
                #print(self.conversation_history[conversation_id][-1])

                # We call the agent again to get the final reply after the tool executions
                final_reply = self.tool_agent.run(self.conversation_history[conversation_id])
                self.conversation_history[conversation_id].extend(final_reply)
                # print(self.conversation_history[conversation_id][-1])

                # Store the response
                self.data['summary'][identifier][field]['content'] = self.conversation_history[conversation_id][-1].text if final_reply else "unknown"

            print("--------------------------------")
            print(self.conversation_history[conversation_id])
            print("--------------------------------")

    def process_all_sections(self) -> Dict[str, Any]:
        """Process all fields in data_template.json and save results to data_answer.json"""
        self.process_summary_fields(inter=False)
        self.process_summary_fields(inter=True)

        # Save to answer.json
        try:
            with open('data_answer.json', 'w', encoding='utf-8') as file:
                json.dump(self.data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to answer.json: {e}")
        
        return self.data
    
test_orchestrator = Orchestrator()
test_orchestrator.process_all_sections()
