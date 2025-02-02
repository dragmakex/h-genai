# https://haystack.deepset.ai/tutorials/40_building_chat_application_with_function_calling#creating-a-function-calling-tool-from-a-haystack-pipeline

from haystack import Pipeline, Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder

from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator


from dotenv import load_dotenv
import os

MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

# Load environment variables for Keys
load_dotenv()
aws_access_key_id = os.getenv("BR_AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("BR_AWS_SECRET_ACCESS_KEY")
aws_region_name = os.getenv("BR_AWS_DEFAULT_REGION")
search_api_key = os.getenv("SERPERDEV_API_KEY")

documents = [
    Document(content="My name is Jean and I live in Paris."),
    Document(content="My name is Mark and I live in Berlin."),
    Document(content="My name is Giorgio and I live in Rome."),
    Document(content="My name is Marta and I live in Madrid."),
    Document(content="My name is Harry and I live in London."),
]
document_store = InMemoryDocumentStore()

template = [
    ChatMessage.from_user(
        """
    Answer the questions based on the given context.

    Context:
    {% for document in documents %}
        {{ document.content }}
    {% endfor %}
    Question: {{ question }}
    Answer:
    """)
]

# Document Indexing Pipeline
indexing_pipeline = Pipeline()
indexing_pipeline.add_component("doc_embedder", instance=SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"))
indexing_pipeline.add_component("doc_writer", instance=DocumentWriter(document_store=document_store))
indexing_pipeline.connect("doc_embedder.documents", "doc_writer.documents")
indexing_pipeline.run({"doc_embedder": {"documents": documents}})

# Query Embedding and RAG Pipeline
rag_pipe = Pipeline()
rag_pipe.add_component("embedder", SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"))
rag_pipe.add_component("retriever", InMemoryEmbeddingRetriever(document_store=document_store))
rag_pipe.add_component("prompt_builder", ChatPromptBuilder(template=template))
rag_pipe.add_component("llm", AmazonBedrockChatGenerator(
    model=MODEL_ID,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_region_name=aws_region_name
))
rag_pipe.connect("embedder.embedding", "retriever.query_embedding")
rag_pipe.connect("retriever", "prompt_builder.documents")
rag_pipe.connect("prompt_builder.prompt", "llm.messages")

def rag_pipeline_func(query: str):
    """Search your documents with the RAG pipeline.
    https://haystack.deepset.ai/tutorials/40_building_chat_application_with_function_calling#creating-a-function-calling-tool-from-a-haystack-pipeline
    
    Args:
        query: The search query to look up

    Returns:
        str: The search results
    """
    result = rag_pipe.run({"embedder": {"text": query}, "prompt_builder": {"question": query}})
    return {"reply": result["llm"]["replies"][0].text}

# # Running the Pipeline
# query = "Where does Mark live?"
# result = rag_pipe.run({"embedder": {"text": query}, "prompt_builder": {"question": query}})
# print(result["llm"]["replies"][0].text)
