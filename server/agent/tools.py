from haystack.components.websearch import SerperDevWebSearch
from haystack.utils import Secret

from typing import Annotated
from dotenv import load_dotenv
import os

# Load environment variables for Keys
load_dotenv()
search_api_key = os.getenv("SERPERDEV_API_KEY")

###############
# SEARCH TOOL #
###############

# Ading a tool (adapted from e.g. https://haystack.deepset.ai/tutorials/40_building_chat_application_with_function_calling)
# This is a pipeline (you can define any other pipeline you want to give as a tool)
# Returns documents, content, metadata, and links
websearch = SerperDevWebSearch(top_k=5, api_key=Secret.from_token(search_api_key))

# We have to create a function from the pipeline
# This has to be anotated and needs a docstring we can then use create_tool_from_function (done in the init of the ToolCallingAgent)
def search_func(query: Annotated[str, "The query to search for"]):
    """Search the web for a given query with the SerperDevWebSearch pipeline.
    https://github.com/deepset-ai/haystack/blob/main/haystack/components/websearch/serper_dev.py

    Args:
        query: The search query to look up

    Returns:
        str: The search results
    """
    return websearch.run(query)


# Example:
# results = websearch.run(query="Who is the boyfriend of Olivia Wilde?")
# results = search_func(query="Who is the boyfriend of Olivia Wilde?")
