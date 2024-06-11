import os
from dotenv import load_dotenv
import azure.search.documents
azure.search.documents.__version__
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient, SearchIndexingBufferedSender
from azure.search.documents.indexes import SearchIndexClient
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

load_dotenv()

AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
AZURE_OPENAI_API_KEY= os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_SEARCH_INDEX = os.environ.get("AZURE_OPENAI_SEARCH_INDEX") #自動構築時のデフォルト設定

credential = AzureKeyCredential(AZURE_OPENAI_API_KEY)