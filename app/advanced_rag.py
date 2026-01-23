"""
Advanced RAG Pipeline Implementation
Demonstrates LangChain pipeline building and RAG flows for job requirements
"""

import os
from typing import List, Dict, Any
from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_core.runnables.base import Runnable
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_community.retrievers import BM25Retriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv

load_dotenv()

# Initialize components
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def get_env_int(name: str, default: int) -> int:
    """Read an int env var with a safe fallback."""
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def get_retriever_mode() -> str:
    """Return selected retriever mode (hybrid or expansion)."""
    return os.getenv("RAG_RETRIEVER_MODE", "hybrid").lower()


# Environment knobs (defaults):
# - RAG_RETRIEVER_MODE: "hybrid" (BM25+semantic) or "expansion" (LLM query expansion)
# - RAG_HYBRID_K: 10 (docs fetched by hybrid retriever)
# - RAG_EXPANSION_K: 10 (docs fetched per expanded query)
# - RAG_RERANK_K: 5 (docs kept after cross-encoder rerank)


class QueryExpansionRetriever:
    """Advanced retriever with query expansion capabilities"""

    def __init__(self, vectorstore: VectorStore, llm: ChatOpenAI, k: int = 5):
        self.vectorstore = vectorstore
        self.llm = llm
        self.k = k

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve documents with query expansion"""
        # Expand the query using LLM
        expanded_queries = self._expand_query(query)

        all_docs = []
        for expanded_query in expanded_queries:
            docs = self.vectorstore.similarity_search(expanded_query, k=self.k)
            all_docs.extend(docs)

        # Remove duplicates and return top results
        seen_content = set()
        unique_docs = []
        for doc in all_docs:
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                unique_docs.append(doc)
                if len(unique_docs) >= self.k * 2:  # Get more for re-ranking
                    break

        return unique_docs

    def _expand_query(self, query: str) -> List[str]:
        """Expand query using LLM to generate related search terms"""
        expansion_prompt = PromptTemplate.from_template(
            """
            Given the following query, generate 3 related search queries that
            would help find more comprehensive information.
            Focus on synonyms, related concepts, and broader/narrower terms.

            Original Query: {query}

            Generate 3 expanded queries:
            1.
            2.
            3.
            """
        )

        chain = expansion_prompt | self.llm | StrOutputParser()
        expanded = chain.invoke({"query": query})

        # Parse the response
        lines = expanded.strip().split("\n")
        queries = [query]  # Include original query

        for line in lines:
            if line.strip() and any(line.startswith(f"{i}.") for i in range(1, 4)):
                # Extract the query after the number
                query_text = line.split(".", 1)[1].strip()
                if query_text:
                    queries.append(query_text)

        return queries[:4]  # Original + 3 expanded


class RerankingRetriever:
    """Retriever with cross-encoder re-ranking"""

    def __init__(self, base_retriever, top_k: int = 5):
        self.base_retriever = base_retriever
        self.top_k = top_k
        self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve and re-rank documents"""
        # Get initial candidates
        candidates = self.base_retriever.get_relevant_documents(query)

        if len(candidates) <= self.top_k:
            return candidates

        # Prepare pairs for cross-encoder
        pairs = [[query, doc.page_content] for doc in candidates]

        # Get relevance scores
        scores = self.cross_encoder.predict(pairs)

        # Sort by scores and return top_k
        scored_docs = list(zip(candidates, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, score in scored_docs[: self.top_k]]


class HybridRetriever:
    """Hybrid retriever combining BM25 and semantic search"""

    def __init__(
        self,
        vectorstore: VectorStore,
        documents: List[Document],
        k: int = 5,
    ):
        self.vectorstore = vectorstore
        self.documents = documents
        self.k = k
        # Initialize BM25 retriever
        self.bm25_retriever = BM25Retriever.from_documents(self.documents)
        self.bm25_retriever.k = self.k

        # Initialize semantic retriever
        self.semantic_retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": self.k}
        )

        # Simple combination without EnsembleRetriever
        self.retrievers = [self.bm25_retriever, self.semantic_retriever]

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve using hybrid approach"""
        all_docs = []
        for retriever in self.retrievers:
            docs = retriever.invoke(query)
            all_docs.extend(docs)

        # Remove duplicates and return top results
        seen_content = set()
        unique_docs = []
        for doc in all_docs:
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                unique_docs.append(doc)
                if len(unique_docs) >= self.k * 2:
                    break

        return unique_docs[: self.k]


def create_advanced_rag_chain(vectorstore: VectorStore, documents: List[Document]):
    """Create an advanced RAG chain using LCEL"""

    # Create advanced retriever pipeline with configurable mode
    retriever_mode = get_retriever_mode()
    k_hybrid = get_env_int("RAG_HYBRID_K", 10)
    k_expansion = get_env_int("RAG_EXPANSION_K", 10)
    k_rerank = get_env_int("RAG_RERANK_K", 5)

    print(
        f"RAG retriever mode={retriever_mode} "
        f"k_hybrid={k_hybrid} k_expansion={k_expansion} "
        f"k_rerank={k_rerank}"
    )

    if retriever_mode == "expansion":
        base_retriever = QueryExpansionRetriever(
            vectorstore=vectorstore,
            llm=llm,
            k=k_expansion,
        )
    else:
        base_retriever = HybridRetriever(
            vectorstore=vectorstore,
            documents=documents,
            k=k_hybrid,
        )

    reranking_retriever = RerankingRetriever(
        base_retriever=base_retriever,
        top_k=k_rerank,
    )

    # RAG Prompt
    rag_prompt = PromptTemplate.from_template(
        """
        You are an expert career advisor helping with job search and skill
        development. Use the following context to provide accurate, helpful
        information.

        Context:
        {context}

        Question: {question}

        Provide a comprehensive answer based on the context. Include specific
        examples and actionable advice.
        """
    )

    # Create LCEL chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def retrieve_and_format(question):
        docs = reranking_retriever.get_relevant_documents(question)
        return format_docs(docs)

    rag_chain: Runnable = (
        {
            "context": RunnableLambda(retrieve_and_format),
            "question": RunnablePassthrough(),
        }
        | rag_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def create_conversational_rag_chain(vectorstore: VectorStore):
    """Create a conversational RAG chain with memory"""

    # from langchain.memory import ConversationBufferWindowMemory
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # Create a simple conversational chain without
    # deprecated ConversationalRetrievalChain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    conversational_prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful AI assistant for job research and career advice.

        Context from previous conversation:
        {chat_history}

        Current question: {question}

        Relevant information: {context}

        Provide a helpful, conversational response based on the context and
        previous conversation.
        """
    )

    # Simple chain without memory for now (can be enhanced later)
    rag_chain: Runnable = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
            "chat_history": lambda x: "",
        }
        | conversational_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


class RAGEvaluator:
    """Evaluate RAG pipeline performance"""

    def __init__(self, vectorstore: VectorStore):
        self.vectorstore = vectorstore
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def evaluate_retrieval(
        self, query: str, ground_truth_docs: List[str], k: int = 5
    ) -> Dict[str, float]:
        """Evaluate retrieval quality"""
        retrieved_docs = self.vectorstore.similarity_search(query, k=k)
        retrieved_content = [doc.page_content for doc in retrieved_docs]

        # Calculate metrics
        precision = (
            len(set(retrieved_content) & set(ground_truth_docs))
            / len(retrieved_content)
            if retrieved_content
            else 0
        )
        recall = (
            len(set(retrieved_content) & set(ground_truth_docs))
            / len(ground_truth_docs)
            if ground_truth_docs
            else 0
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "retrieved_count": len(retrieved_docs),
        }

    def evaluate_generation(
        self,
        question: str,
        generated_answer: str,
        context_docs: List[Document],
    ) -> Dict[str, Any]:
        """Evaluate generation quality using LLM-as-judge"""

        evaluation_prompt = PromptTemplate.from_template(
            """
            Evaluate the quality of this AI-generated answer
            based on the question and context.

            Question: {question}
            Generated Answer: {generated_answer}
            Context Documents: {context}

            Rate the answer on a scale of 1-5 for:
            1. Relevance to the question
            2. Accuracy based on context
            3. Completeness of information
            4. Clarity and helpfulness

            Provide scores and brief reasoning for each criterion.
            """
        )

        context_text = "\n".join([doc.page_content for doc in context_docs])

        chain = evaluation_prompt | self.llm | StrOutputParser()
        evaluation = chain.invoke(
            {
                "question": question,
                "generated_answer": generated_answer,
                "context": context_text,
            }
        )

        return {
            "evaluation": evaluation,
            "answer_length": len(generated_answer),
            "context_docs_used": len(context_docs),
        }


def create_document_processing_pipeline():
    """Create a document processing pipeline for ingestion"""

    # Text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    # Create processing chain
    def process_documents(documents: List[Document]) -> List[Document]:
        """Process documents through the pipeline"""
        processed_docs = []

        for doc in documents:
            # Split text
            chunks = text_splitter.split_text(doc.page_content)

            # Create chunk documents
            for i, chunk in enumerate(chunks):
                chunk_doc = Document(
                    page_content=chunk,
                    metadata={
                        **doc.metadata,
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                        "source_document": doc.metadata.get("title", "Unknown"),
                    },
                )
                processed_docs.append(chunk_doc)

        return processed_docs

    return process_documents


# Example usage and testing functions
def test_advanced_rag_pipeline():
    """Test function for the advanced RAG pipeline"""

    # Sample documents for testing
    test_docs = [
        Document(
            page_content=(
                "LangChain is a framework for building applications with "
                "LLMs. It provides components for chains, agents, and "
                "memory management."
            ),
            metadata={"title": "LangChain Overview", "type": "framework"},
        ),
        Document(
            page_content=(
                "Retrieval-Augmented Generation (RAG) combines retrieval "
                "systems with generative models to provide accurate, "
                "up-to-date responses."
            ),
            metadata={"title": "RAG Explanation", "type": "technique"},
        ),
        Document(
            page_content=(
                "Vector databases like Pinecone and FAISS enable efficient "
                "similarity search for embeddings in production applications."
            ),
            metadata={"title": "Vector Databases", "type": "infrastructure"},
        ),
    ]

    # Create vectorstore for testing
    from langchain_community.vectorstores import FAISS

    vectorstore = FAISS.from_documents(test_docs, embeddings)

    # Test query expansion
    query_expander = QueryExpansionRetriever(vectorstore=vectorstore, llm=llm, k=3)
    expanded_results = query_expander.get_relevant_documents("What is LangChain?")

    # Test re-ranking
    reranker = RerankingRetriever(base_retriever=query_expander, top_k=2)
    reranked_results = reranker.get_relevant_documents("What is LangChain?")

    # Test full RAG chain
    rag_chain = create_advanced_rag_chain(vectorstore, test_docs)
    answer = rag_chain.invoke("Explain how RAG works")

    print("Advanced RAG Pipeline Test Results:")
    print(f"Query Expansion Results: {len(expanded_results)} documents")
    print(f"Re-ranked Results: {len(reranked_results)} documents")
    print(f"RAG Answer: {answer[:200]}...")

    return {
        "expanded_results": expanded_results,
        "reranked_results": reranked_results,
        "rag_answer": answer,
    }


if __name__ == "__main__":
    # Run tests
    test_advanced_rag_pipeline()
