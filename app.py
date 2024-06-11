# This is the base file for RAG based on:
# ref: https://github.com/shohei1029/book-azureopenai-sample/blob/main/aoai-rag/notebooks/02_RAG_AzureAISearch_PythonSDK.ipynb

from tenacity import retry, wait_random_exponential, stop_after_attempt
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
)
from openai import AzureOpenAI
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

load_dotenv()

# load Azure AI search settings
service_endpoint: str = os.environ.get("AI_SEARCH_ENDPOINT")
service_query_key: str = os.environ.get("AI_SEARCH_QUERY_KEY")
index_name: str = os.environ.get("INDEX_NAME")
credential = AzureKeyCredential(service_query_key)

# Azure OpenAI settings
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.environ.get(
    "AZURE_OPENAI_CHATGPT_DEPLOYMENT")
AZURE_OPENAI_EMB_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMB_DEPLOYMENT")

openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
# function which create title field and contents field's embeddings
def generate_embeddings(text, model=AZURE_OPENAI_EMB_DEPLOYMENT):
    return openai_client.embeddings.create(input=[text], model=model).data[0].embedding


# create query for Azure AI search
# Query generation prompt
query_prompt_template = """
以下は、日本の世界遺産についてナレッジベースを検索して回答する必要のあるユーザーからの新しい質問です。
会話と新しい質問に基づいて、検索クエリを作成してください。
検索クエリには、引用されたファイルや文書の名前（例:info.txtやdoc.pdf）を含めないでください。
検索クエリには、括弧 []または<<>>内のテキストを含めないでください。
検索クエリを生成できない場合は、数字 0 だけを返してください。
"""
messages = [{'role': 'system', 'content': query_prompt_template}]
