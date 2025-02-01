# Imports
from haystack.dataclasses import ChatMessage

from agents import ToolCallingAgent
from tools import get_sonar_pro_response
from rag_pipeline import rag_pipeline_func

Tool_Agent = ToolCallingAgent(functions=[get_sonar_pro_response, rag_pipeline_func])  # Can define name and special instructions & tools for every agent

# Create Messages List to store
messages = []


# Query User
user_input = input("User: ")
messages.append(ChatMessage.from_user(user_input))

# Call Agent
# Our agent alrady calls the tool, so we dont need to do it manually with toolinvoker
new_messages = Tool_Agent.run(messages)
messages.extend(new_messages)

# We call the agent again to get the final reply after the tool execution
final_replie = Tool_Agent.run(messages)