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

###
# load environment variables
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


###
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

# setting Few-shot Samples
query_prompt_few_shots = [
    {'role': 'user', 'content': '屋久島の歴史を教えて  '},
    {'role': 'assistant', 'content': '屋久島　歴史'},
    {'role': 'user', 'content': '清水寺にはどう行きますか？'},
    {'role': 'assistant', 'content': '清水寺　行き方'}
]

for shot in query_prompt_few_shots:
    messages.append({'role': shot.get('role'), 'content': shot.get('content')})

# User query
user_q = "屋久島はどこに行く？"
messages.append({'role': 'user', 'content': user_q})

# check messages
print(messages)

# create search query
chat_completion: ChatCompletion = openai_client.chat.completions.create(
    messages=messages,
    model=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
    temperature=0.0,
    max_tokens=100,
    n=1)

query_text = chat_completion.choices[0].message.content
print(query_text)

###
# Retrieve by hybrid search


def nonewlines(s: str) -> str:
    return s.replace('\n', ' ').replace('\r', ' ').replace('[', '【').replace(']', '】')


search_client = SearchClient(
    service_endpoint, index_name, credential=credential)
docs = search_client.search(
    search_text=query_text,
    filter=None,
    top=3,
    vector_queries=[VectorizedQuery(vector=generate_embeddings(
        query_text), k_nearest_neighbors=10, fields="contentVector")]
)
docs.get_answers()
results = [" SOURCE:" + doc['title'] + ": " +
           nonewlines(doc['content']) for doc in docs]
print(results)

###
# Generate answers
# System message
system_message_chat_conversation = """
あなたは日本の世界遺産に関する観光ガイドです。
If you cannot guess the answer to a question from the SOURCE, answer "I don't know".
Answers must be in Japanese.

# Restrictions
- The SOURCE prefix has a colon and actual information after the filename, and each fact used in the response must include the name of the source.
- To reference a source, use a square bracket. For example, [info1.txt]. Do not combine sources, but list each source separately. For example, [info1.txt][info2.pdf].
"""

messages = [{'role': 'system', 'content': system_message_chat_conversation}]

# context augmentation
