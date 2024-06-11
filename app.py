# This is the base file for RAG based on: 
# ref: https://github.com/shohei1029/book-azureopenai-sample/blob/main/aoai-rag/notebooks/02_RAG_AzureAISearch_PythonSDK.ipynb

import azure.search.documents
print(f"azure search version={azure.search.documents.__version__}")
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