# This is the base file for RAG based on:
# ref: https://github.com/shohei1029/book-azureopenai-sample/blob/main/aoai-rag/notebooks/02_RAG_AzureAISearch_PythonSDK.ipynb

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient, SearchIndexingBufferedSender
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import (
    QueryAnswerType,
    QueryCaptionType,
    QueryCaptionResult,
    QueryAnswerResult,
    SemanticErrorMode,
    SemanticErrorReason,
    SemanticSearchResultsType,
    QueryType,
    VectorizedQuery,
    VectorQuery,
    VectorFilterMode,
)
import os
from dotenv import load_dotenv
import azure.search.documents
print(f"azure search version={azure.search.documents.__version__}")

# load Azure AI search settings
service_endpoint: str = os.environ.get("AI_SEARCH_ENDPOINT")
service_query_key: str = os.environ.get("AI_SEARCH_QUERY_KEY")
index_name: str = os.environ.get("INDEX_NAME")

credential = AzureKeyCredential(service_query_key)
