import json
from typing import List, Dict, Any
from haystack.dataclasses import ChatMessage
from agents import Agent, ToolCallingAgent
from tools import search_func, get_sonar_pro_response, get_sonar_response, parse_docs
from prompt import tool_agent_instructions, tool_agent_prompt

class Orchestrator:
    def __init__(self):
        # Initialize different types of agents
        self.simple_agent = Agent()
        self.tool_agent = ToolCallingAgent(
            instructions=tool_agent_instructions,
            functions=[get_sonar_pro_response])
        
        # Store conversation history
        self.conversation_history: Dict[str, List[ChatMessage]] = {}
        
        # Load data from data.json
        self.data = self._load_data_fields()
    
    def _load_data_fields(self) -> Dict[str, Any]:
        """Load data from data.json file"""
        try:
            with open('data.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("data.json not found in the agent directory")
    
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

    def process_summary_fields(self) -> Dict[str, str]:
        """Process municipality fields from the summary section"""
        municipality_data = {}
        
        if 'summary' not in self.data or 'municipality' not in self.data['summary']:
            return municipality_data
        
        fields = self.data['summary']['municipality']
        name = self.data['municipality_name']
        
        # Process each field in the municipality data
        for field, value in fields.items():
            print(field)
            
            conversation_id = field
            # Initialize conversation history for this area if it doesn't exist
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            # Create a prompt based on the field and append it to the messages
            prompt = tool_agent_prompt.format(name=name, field=field, value=value)
            self.conversation_history[conversation_id].append(ChatMessage.from_user(prompt))

            # Get response from agent and extend the conversation history with the response
            response = self.tool_agent.run(self.conversation_history[conversation_id])
            self.conversation_history[conversation_id].extend(response)

            # We call the agent again to get the final reply after the tool execution
            final_reply = self.tool_agent.run(self.conversation_history[conversation_id])
            self.conversation_history[conversation_id].extend(final_reply)
            
            # Store the response
            municipality_data[field] = self.conversation_history[conversation_id][-1].text if final_reply else ""

        return municipality_data

    def process_all_fields(self) -> Dict[str, Any]:
        """Process all fields in data.json and save results to answer.json"""
        # Process the data
        processed_data = {
            "summary": {
                "municipality": self.process_summary_fields()
            }
        }

        # Save to answer.json
        try:
            with open('answer.json', 'w', encoding='utf-8') as file:
                json.dump(processed_data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to answer.json: {e}")
        
        return processed_data
    
test_orchestrator = Orchestrator()
test_orchestrator.process_all_fields()