# AI Job Research & Summary Agent

Simple demo app showcasing LLM-powered agents, Python async programming, LangGraph, RAG, and more.

## Overview

This agent accepts a job description, analyzes required skills, retrieves relevant learning resources using RAG, identifies skill gaps, and generates a personalized learning plan.

## Architecture

```
Job Description Input
       ↓
   FastAPI Endpoint
       ↓
   LangGraph Agent
   ├── Extract Skills (LLM)
   ├── Retrieve Resources (RAG)
   ├── Analyze Gaps (LLM)
   └── Generate Plan (LLM)
       ↓
   JSON Response
```

## Tech Stack

- **Python 3.11** with async programming
- **FastAPI** for the API service
- **LangGraph** for multi-step agent orchestration
- **LangChain** for LLM integration
- **FAISS** vector store for RAG
- **OpenAI GPT-4o-mini** (easily swappable to Gemini/Claude)
- **Docker** for containerization
- **pytest** for testing

## Quick Start

1. **Clone & Setup**:
   ```bash
   git clone <repo>
   cd ai-job-research
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Set API Key**:
   Create `.env` file:
   ```
   OPENAI_API_KEY=your-key-here
   ```

3. **Run Everything**:
   ```bash
   ./run.sh
   ```
   This starts both the backend (http://localhost:8000) and frontend (http://localhost:3000).

   Or run manually:
   ```bash
   # Terminal 1: Backend
   export KMP_DUPLICATE_LIB_OK=TRUE
   uvicorn app.main:app --reload

   # Terminal 2: Frontend
   cd frontend && npm start
   ```

## Frontend

A React TypeScript frontend is included for easy job analysis:

```bash
# Terminal 1: Start the backend
export KMP_DUPLICATE_LIB_OK=TRUE
uvicorn app.main:app --reload

# Terminal 2: Start the frontend
cd frontend
npm install
npm start
```

The frontend will be available at http://localhost:3000 and connects to the FastAPI backend at http://localhost:8000.

**Note**: Both servers must be running simultaneously for the frontend to work.

## Docker

```bash
docker build -t ai-career-agent .
docker run -p 8000:8000 ai-career-agent
```

## Testing

```bash
pytest tests/
```

## Troubleshooting

### OpenMP Library Conflicts (macOS)

If you see errors like "Initializing libomp.dylib, but found libomp.dylib already initialized":

```bash
export KMP_DUPLICATE_LIB_OK=TRUE
uvicorn app.main:app --reload
```

This is caused by multiple libraries (like FAISS) trying to use OpenMP simultaneously.

### API Key Issues

- Ensure your `.env` file exists with `OPENAI_API_KEY=your-key-here`
- Check your OpenAI account has credits
- Verify the API key is not expired

### Import Errors

If you get import errors after switching LLM providers:
```bash
pip install -r requirements.txt  # Reinstall dependencies
```

## Persistent Vector Store (Pinecone)

For production use with larger datasets and persistence across restarts:

### Setup Pinecone

1. **Create account**: https://www.pinecone.io/
2. **Get API key**: Copy from Pinecone dashboard
3. **Update `.env`**:
   ```
   PINECONE_API_KEY=your-pinecone-api-key
   PINECONE_INDEX_NAME=ai-job-research
   USE_PINECONE=true
   ```


**Development/Demo**: Use FAISS (free, local, fast)
**Production**: Use Pinecone (persistent, scalable, managed)

The code automatically switches based on `USE_PINECONE` environment variable.
