from haystack.components.websearch import SerperDevWebSearch
from haystack.utils import Secret

from typing import Annotated, List
from dotenv import load_dotenv
import os

from pydantic import BaseModel
from openai import OpenAI

# Load environment variables for Keys
load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

def tool(func):
    """Decorator to automatically register functions as tools"""
    func._is_tool = True
    return func

class PerplexityResponse(BaseModel):
    content: str
    citations: List[str]

@tool
def get_sonar_pro_response(message: str) -> PerplexityResponse:
    """
    Generate a response using the Perplexity API's 'sonar-pro' model.
    

    This function sends a message to the Perplexity API and retrieves a response
    along with any citations from the 'sonar-pro' model. The response includes
    both the generated content and a list of citations.

    Args:
        message: The input message or question to send to the model.

    Returns:
        PerplexityResponse: A Pydantic model containing the generated content
                            and a list of citations.

    Example:
        response = get_sonar_pro_response("Explain quantum computing.")
        print(response.content)  # Prints the generated response
        print(response.citations)  # Prints the list of citations
    """
    client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

    messages = [
        {"role": "user", "content": message}
    ]
    response = client.chat.completions.create(model="sonar-pro", messages=messages)
    return PerplexityResponse(content=response.choices[0].message.content, citations=response.citations)

#def get_sonar_response(message: str) -> PerplexityResponse:
#    """
#    Generate a response using the Perplexity API's 'sonar' model.
#    
#    This function sends a message to the Perplexity API and retrieves a response
#    along with any citations from the 'sonar' model. The response includes both
#    the generated content and a list of citations.
#
#    Args:
#        message: The input message or question to send to the model.
#
#    Returns:
#        PerplexityResponse: A Pydantic model containing the generated content
#                           and a list of citations.
#
#    Example:
#        response = get_sonar_response("What is natural language processing?")
#        print(response.content)  # Prints the generated response
#        print(response.citations)  # Prints the list of citations
#   """
#
#    messages = [
#        {"role": "user", "content": message}
#    ]
#    response = client.chat.completions.create(model="sonar", messages=messages)
#    return PerplexityResponse(content=response.choices[0].message.content, citations=response.citations)

# from docling.document_converter import DocumentConverter
# converter = DocumentConverter()
# def parse_docs(source_path: str) -> str:
#    """
#    Convert a pdf document to markdown format.
#
#    Args:
#        source_path (str): Local file path or URL to the document
#
#    Returns:
#        str: The document content in markdown format
#    """
#
#    result = converter.convert(source_path)
#    return result.document.export_to_markdown()

# search_api_key = os.getenv("SERPERDEV_API_KEY")
# Ading a tool (adapted from e.g. https://haystack.deepset.ai/tutorials/40_building_chat_application_with_function_calling)
# This is a pipeline (you can define any other pipeline you want to give as a tool)
# https://docs.haystack.deepset.ai/v1.22/docs/nodes_overview
# Returns documents, content, metadata, and links
# websearch = SerperDevWebSearch(top_k=5, api_key=Secret.from_token(search_api_key))

# We have to create a function from the pipeline
# This has to be anotated and needs a docstring we can then use create_tool_from_function (done in the init of the ToolCallingAgent)
#def search_func(query: Annotated[str, "The query to search for"]):
#    """Search the web for a given query with the SerperDevWebSearch pipeline.
#    https://github.com/deepset-ai/haystack/blob/main/haystack/components/websearch/serper_dev.py
#
#    Args:
#        query: The search query to look up
#
#    Returns:
#        str: The search results
#    """
#    return websearch.run(query)


# Example:
# results = websearch.run(query="Who is the boyfriend of Olivia Wilde?")
# results = search_func(query="Who is the boyfriend of Olivia Wilde?")
