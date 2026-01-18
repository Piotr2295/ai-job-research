from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Sample documents for RAG
SAMPLE_DOCS = [
    Document(page_content="LangGraph is a library for building stateful, multi-actor applications with LLMs. It allows you to create agent graphs with nodes and edges for complex workflows.", metadata={"title": "LangGraph Docs", "url": "https://langchain-ai.github.io/langgraph/"}),
    Document(page_content="LangChain is a framework for developing applications powered by language models. It provides components for chains, agents, and memory.", metadata={"title": "LangChain Overview", "url": "https://python.langchain.com/docs/get_started/introduction"}),
    Document(page_content="Python async programming with asyncio allows for concurrent code using async/await syntax. FastAPI is a modern web framework for building APIs with Python 3.7+ based on standard Python type hints.", metadata={"title": "Python Async & FastAPI", "url": "https://fastapi.tiangolo.com/"}),
    Document(page_content="Vector stores like FAISS or Chroma enable efficient similarity search for embeddings. They are essential for RAG (Retrieval-Augmented Generation) patterns.", metadata={"title": "Vector Stores Guide", "url": "https://python.langchain.com/docs/modules/data_connection/vectorstores/"}),
    Document(page_content="LLM agents can use tools to perform actions. Tools can be functions that the agent calls to get information or execute tasks.", metadata={"title": "Building LLM Agents", "url": "https://python.langchain.com/docs/modules/agents/"}),
    Document(page_content="OpenAI provides powerful language models like GPT-4. Claude from Anthropic and Gemini from Google are alternatives with different strengths.", metadata={"title": "LLM Providers Comparison", "url": "https://example.com/llm-comparison"}),
]

def get_vector_store():
    # Use OpenAI embeddings
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(SAMPLE_DOCS, embeddings)

vector_store = None

def retrieve_resources(query: str, k: int = 3):
    global vector_store
    if vector_store is None:
        vector_store = get_vector_store()
    docs = vector_store.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]