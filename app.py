# This is the base file for RAG based on: 
# ref: https://github.com/shohei1029/book-azureopenai-sample/blob/main/aoai-rag/notebooks/02_RAG_AzureAISearch_PythonSDK.ipynb

import azure.search.documents
print(f"azure search version={azure.search.documents.__version__}")