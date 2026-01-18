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

3. **Run**:
   ```bash
   # On macOS, you may need to set this environment variable to avoid OpenMP conflicts
   export KMP_DUPLICATE_LIB_OK=TRUE
   uvicorn app.main:app --reload
   ```

4. **Test API**:
   ```bash
   curl -X POST "http://localhost:8000/analyze" \
        -H "Content-Type: application/json" \
        -d '{"job_description": "Python developer with LangChain experience", "current_skills": ["Python"]}'
   ```

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
