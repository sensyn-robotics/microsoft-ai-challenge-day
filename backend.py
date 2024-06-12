# This is the RAG implementation based on:
# ref: https://github.com/shohei1029/book-azureopenai-sample/blob/main/aoai-rag/notebooks/02_RAG_AzureAISearch_PythonSDK.ipynb

from azure.core.exceptions import IncompleteReadError
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


class ChatBot:
    def __init__(self):
        # load environment variables
        load_dotenv()

        # load Azure AI search settings
        self.service_endpoint: str = os.environ.get("AI_SEARCH_ENDPOINT")
        service_query_key: str = os.environ.get("AI_SEARCH_QUERY_KEY")
        self.index_name: str = os.environ.get("INDEX_NAME")
        self.credential = AzureKeyCredential(service_query_key)

        # Azure OpenAI settings
        AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
        AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.environ.get(
            "AZURE_OPENAI_CHATGPT_DEPLOYMENT")
        self.AZURE_OPENAI_EMB_DEPLOYMENT = os.environ.get(
            "AZURE_OPENAI_EMB_DEPLOYMENT")

        self.openai_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

        ###
        # create query for Azure AI search
        # Query generation prompt
        self.query_prompt_template = """
        以下は、日本の世界遺産についてナレッジベースを検索して回答する必要のあるユーザーからの新しい質問です。
        会話と新しい質問に基づいて、検索クエリを作成してください。
        検索クエリには、引用されたファイルや文書の名前（例:info.txtやdoc.pdf）を含めないでください。
        検索クエリには、括弧 []または<<>>内のテキストを含めないでください。
        検索クエリを生成できない場合は、数字 0 だけを返してください。
        """
        self.messages = [
            {'role': 'system', 'content': self.query_prompt_template}]

        # setting Few-shot Samples
        self.query_prompt_few_shots = [
            {'role': 'user', 'content': '屋久島の歴史を教えて  '},
            {'role': 'assistant', 'content': '屋久島　歴史'},
            {'role': 'user', 'content': '清水寺にはどう行きますか？'},
            {'role': 'assistant', 'content': '清水寺　行き方'}
        ]

        for shot in self.query_prompt_few_shots:
            self.messages.append({'role': shot.get('role'),
                                  'content': shot.get('content')})

        self.search_client = SearchClient(
            self.service_endpoint, self.index_name, credential=self.credential)

        # System message
        self.system_message_chat_conversation = """
        あなたは日本の世界遺産に関する観光ガイドです。
        If you cannot guess the answer to a question from the SOURCE, answer "I don't know".
        Answers must be in Japanese.

        # Restrictions
        - The SOURCE prefix has a colon and actual information after the filename, and each fact used in the response must include the name of the source.
        - To reference a source, use a square bracket. For example, [info1.txt]. Do not combine sources, but list each source separately. For example, [info1.txt][info2.pdf].
        """

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    # function which create title field and contents field's embeddings
    def generate_embeddings(self, text, model):
        return self.openai_client.embeddings.create(input=[text], model=model).data[0].embedding

    def nonewlines(self, s: str) -> str:
        return s.replace('\n', ' ').replace('\r', ' ').replace('[', '【').replace(']', '】')

    def respond(self, user_q: str):
        self.messages.append({'role': 'user', 'content': user_q})

        # create search query
        chat_completion: ChatCompletion = self.openai_client.chat.completions.create(
            messages=self.messages,
            model=self.AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            temperature=0.0,
            max_tokens=100,
            n=1)

        query_text = chat_completion.choices[0].message.content
        print(f"revised query={query_text}")

        ###
        # Retrieve by hybrid search
        docs = self.search_client.search(
            search_text=query_text,
            filter=None,
            top=3,
            vector_queries=[VectorizedQuery(vector=self.generate_embeddings(
                query_text, self.AZURE_OPENAI_EMB_DEPLOYMENT), k_nearest_neighbors=10, fields="contentVector")]
        )
        docs.get_answers()
        reference_results = [" SOURCE:" + doc['title'] + ": " +
                             self.nonewlines(doc['content']) for doc in docs]
        print(f"reference result={reference_results}")

        ###
        # Generate answers
        # refresh messages for answer LLM.
        self.messages = [
            {'role': 'system', 'content': self.system_message_chat_conversation}]

        # context augmentation
        # Context from Azure AI Search
        context = "\n".join(reference_results)
        self.messages.append(
            {'role': 'user', 'content': user_q + "\n\n" + context})

        # generate answers
        chat_coroutine = self.openai_client.chat.completions.create(
            model=self.AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            messages=self.messages,
            temperature=0.0,
            max_tokens=1024,
            n=1,
            stream=False
        )

        responce = chat_coroutine.choices[0].message.content

        return responce


if __name__ == "__main__":
    try:
        bot = ChatBot()

        # User query
        user_q = "屋久島はどこに行く？"
        responce = bot.respond(user_q)
        print(responce)
    except IncompleteReadError as e:
        print(f"An error occurred while making the request: {e}")
