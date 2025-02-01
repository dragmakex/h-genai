import json
from typing import List, Dict, Any
from haystack.dataclasses import ChatMessage
from agents import Agent, ToolCallingAgent
from tools import search_func
from prompt import tool_agent_instructions, tool_agent_prompt

class Orchestrator:
    def __init__(self):
        # Initialize different types of agents
        self.simple_agent = Agent()
        self.tool_agent = ToolCallingAgent(
            instructions=tool_agent_instructions,
            functions=[search_func])
        
        # Store conversation history
        self.conversation_history: Dict[str, List[ChatMessage]] = {}
        
        # Load data from data.json
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from data.json file"""
        try:
            with open('data.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("data.json not found in the agent directory")
    
    # def create_conversation(self, conversation_id: str) -> None:
    #     """Initialize a new conversation"""
    #     if conversation_id not in self.conversation_history:
    #         self.conversation_history[conversation_id] = []
    
    # def process_message(self, conversation_id: str, message: str, use_tools: bool = False) -> str:
    #     """Process a message and return the response"""
    #     # Create conversation if it doesn't exist
    #     self.create_conversation(conversation_id)
        
    #     # Add user message to history
    #     user_message = ChatMessage.from_user(message)
    #     self.conversation_history[conversation_id].append(user_message)
        
    #     # Select agent based on whether tools are needed
    #     agent = self.tool_agent if use_tools else self.simple_agent
        
    #     # Get response from agent
    #     new_messages = agent.run(self.conversation_history[conversation_id])
        
    #     # Add agent messages to history
    #     self.conversation_history[conversation_id].extend(new_messages)
        
    #     # Return the last message from the agent
    #     return new_messages[-1].text if new_messages else ""
    
    # def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
    #     """Get the conversation history in a serializable format"""
    #     if conversation_id not in self.conversation_history:
    #         return []
        
    #     return [
    #         {
    #             "role": msg.role.value,
    #             "content": msg.text,
    #             "timestamp": msg.metadata.get("timestamp", None)
    #         }
    #         for msg in self.conversation_history[conversation_id]
    #     ]

    def process_municipality_fields(self) -> Dict[str, str]:
        """Process municipality fields from the summary section"""
        municipality_data = {}
        
        if 'summary' not in self.data or 'municipality' not in self.data['summary']:
            return municipality_data
        
        fields = self.data['summary']['municipality']
        name = self.data['municipality_name']
        
        # Process each field in the municipality data
        for field, value in fields.items():
            print(field)
            # Initialize conversation history for this field if it doesn't exist
            if field not in self.conversation_history:
                self.conversation_history[field] = []
            
            # Create a prompt based on the field and append it to the messages
            prompt = tool_agent_prompt.format(name=name, field=field, value=value)
            self.conversation_history[field].append(ChatMessage.from_user(prompt))

            # Get response from agent and extend the conversation history with the response
            response = self.tool_agent.run(self.conversation_history[field])
            self.conversation_history[field].extend(response)

            # We call the agent again to get the final reply after the tool execution
            final_reply = self.tool_agent.run(self.conversation_history[field])
            self.conversation_history[field].extend(final_reply)
            
            # Store the response
            municipality_data[field] = self.conversation_history[field][-1].text if response else ""

        return municipality_data

    def process_all_fields(self) -> Dict[str, Any]:
        """Process all fields in data.json and save results to answer.json"""
        # Process the data
        processed_data = {
            "summary": {
                "municipality": self.process_municipality_fields()
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