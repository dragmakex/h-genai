from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from haystack.dataclasses import ChatMessage
from dotenv import load_dotenv
import os

load_dotenv()

aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region_name=os.getenv("AWS_DEFAULT_REGION") 

generator = AmazonBedrockChatGenerator(model="mistral.mistral-large-2407-v1:0")
messages = [ChatMessage.from_system("You are a helpful assistant that answers question."), ChatMessage.from_user("What's Natural Language Processing? Be brief.")]
    
response = generator.run(messages)
print(response)