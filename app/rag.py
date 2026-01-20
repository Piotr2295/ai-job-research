from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
import os

# Sample documents for RAG
SAMPLE_DOCS = [
    Document(page_content="LangGraph is a library for building stateful, multi-actor applications with LLMs. It allows you to create agent graphs with nodes and edges for complex workflows.", metadata={"title": "LangGraph Docs", "url": "https://langchain-ai.github.io/langgraph/"}),
    Document(page_content="LangChain is a framework for developing applications powered by language models. It provides components for chains, agents, and memory.", metadata={"title": "LangChain Overview", "url": "https://python.langchain.com/docs/get_started/introduction"}),
    Document(page_content="Python async programming with asyncio allows for concurrent code using async/await syntax. FastAPI is a modern web framework for building APIs with Python 3.7+ based on standard Python type hints.", metadata={"title": "Python Async & FastAPI", "url": "https://fastapi.tiangolo.com/"}),
    Document(page_content="Vector stores like FAISS or Chroma enable efficient similarity search for embeddings. They are essential for RAG (Retrieval-Augmented Generation) patterns.", metadata={"title": "Vector Stores Guide", "url": "https://python.langchain.com/docs/modules/data_connection/vectorstores/"}),
    Document(page_content="LLM agents can use tools to perform actions. Tools can be functions that the agent calls to get information or execute tasks.", metadata={"title": "Building LLM Agents", "url": "https://python.langchain.com/docs/modules/agents/"}),
    Document(page_content="OpenAI provides powerful language models like GPT-4. Claude from Anthropic and Gemini from Google are alternatives with different strengths.", metadata={"title": "LLM Providers Comparison", "url": "https://example.com/llm-comparison"}),
]

def get_faiss_vector_store():
    """Local FAISS vector store"""
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(SAMPLE_DOCS, embeddings)

def get_pinecone_vector_store():
    """Pinecone vector store"""
    embeddings = OpenAIEmbeddings()
    index_name = os.getenv("PINECONE_INDEX_NAME", "ai-job-research")

    # Check if index exists, if not create it
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI embeddings dimension
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}
        )

    # Create vector store from documents
    vectorstore = PineconeVectorStore.from_documents(
        SAMPLE_DOCS, embeddings, index_name=index_name
    )
    return vectorstore

def get_vector_store():
    """Factory function that chooses vector store based on environment"""
    use_pinecone = os.getenv("USE_PINECONE", "false").lower() == "true"

    if use_pinecone and os.getenv("PINECONE_API_KEY"):
        print("Using Pinecone vector store (persistent)")
        return get_pinecone_vector_store()
    else:
        print("Using FAISS vector store (local)")
        return get_faiss_vector_store()

vector_store = None

def retrieve_resources(query: str, k: int = 3):
    global vector_store
    if vector_store is None:
        vector_store = get_vector_store()
    docs = vector_store.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]

def add_document(content: str, metadata: dict = None):
    """Add a new document to the vector store"""
    global vector_store
    if vector_store is None:
        vector_store = get_vector_store()

    doc = Document(page_content=content, metadata=metadata or {})
    vector_store.add_documents([doc])
    print(f"Added document: {content[:50]}...")

def add_documents_to_store(documents: list[Document]):
    """Add multiple documents to the vector store"""
    global vector_store
    if vector_store is None:
        vector_store = get_vector_store()

    vector_store.add_documents(documents)
    print(f"Added {len(documents)} documents to vector store")
