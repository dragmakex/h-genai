from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.components.tools import ToolInvoker
from haystack.tools import create_tool_from_function

from dataclasses import dataclass, field
from typing import Callable, Tuple

from dotenv import load_dotenv
import os

#MODEL_ID = "mistral.mistral-large-2407-v1:0"
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

# Load environment variables for Keys
load_dotenv()
aws_access_key_id = os.getenv("BR_AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("BR_AWS_SECRET_ACCESS_KEY")
aws_region_name = os.getenv("BR_AWS_DEFAULT_REGION")
search_api_key = os.getenv("SERPERDEV_API_KEY")

# Implementations adapted from https://haystack.deepset.ai/cookbook/swarm

# Simple Agent without tools
@dataclass
class Agent:
    name: str = "Agent"
    llm: object = AmazonBedrockChatGenerator(model=MODEL_ID)
    instructions: str = (
        "You are a helpful assistant tasked with finding answers to questions. Keep the answers as short as possible, never longer than one sentence and idealy only one words if it is just a fact."
    )

    def __post_init__(self):
        self._system_message = ChatMessage.from_system(self.instructions)

    def run(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        new_message = self.llm.run(messages=[self._system_message] + messages)[
            "replies"
        ][0]

        if new_message.text:
            print(f"{self.name}: {new_message.text}")

        return [new_message]

# Agent with tools
@dataclass
class ToolCallingAgent:
    name: str = "ToolCallingAgent"
    llm: object = AmazonBedrockChatGenerator(model=MODEL_ID)
    instructions: str = (
        "You are a helpful assistant with tools at your disposal tasked with finding answers to questions. Keep the answres as short as possible, never longer than one sentence and idealy only one words if it is just a fact."
    )
    functions: list[Callable] = field(default_factory=list)

    def __post_init__(self):
        self._system_message = ChatMessage.from_system(self.instructions)
        # We just give the function to the agent. Otherwise we could create all the tools individually and just give a list of tool objects
        self.tools = (
            [create_tool_from_function(fun) for fun in self.functions]
            if self.functions
            else None
        )
        self._tool_invoker = (
            ToolInvoker(tools=self.tools, raise_on_failure=False)
            if self.tools
            else None
        )

    def run(self, messages: list[ChatMessage]) -> Tuple[str, list[ChatMessage]]:
        # generate response
        agent_message = self.llm.run(
            messages=[self._system_message] + messages, tools=self.tools
        )["replies"][0]
        new_messages = [agent_message]

        if agent_message.text:
            print(f"{self.name}: {agent_message.text}")

        
        if not agent_message.tool_calls:
            return new_messages

        # handle tool calls
        print(f"{self.name}: {agent_message.tool_calls}")
        tool_results = self._tool_invoker.run(messages=[agent_message])["tool_messages"]
        new_messages.extend(tool_results)

        return new_messages
    
# Example:
# from haystack.dataclasses import ChatRole

# Simple_Agent = Agent()  # Can define name and special instructions for every agent
# messages = []
# print("Type 'quit' to exit")

# while True:
#     if not messages or messages[-1].role == ChatRole.ASSISTANT:
#         user_input = input("User: ")
#         if user_input.lower() == "quit":
#             break
#         messages.append(ChatMessage.from_user(user_input))

#     new_messages = Simple_Agent.run(messages)
#     messages.extend(new_messages)