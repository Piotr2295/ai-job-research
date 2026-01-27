# AI Job Research & Career Development Platform

A comprehensive AI-powered platform for job analysis, skill development tracking, and career growth. Features LLM agents, RAG systems, MCP integration, and a unified web interface.

https://github.com/user-attachments/assets/50408ccf-6c48-4ae6-9d3c-51e74c36cd0a

## Overview

This platform provides multiple AI-powered tools for career development:

- **Job Analysis**: Analyze job descriptions to identify required skills, gaps, and learning plans
- **Advanced RAG**: Multi-stage retrieval with quality evaluation to ground learning plans and responses
- **Career Tracking**: Save and compare job analyses over time with persistent storage
- **Learning Progress**: Track skill development with progress monitoring
- **GitHub Analysis**: Extract skills and suggest roles from coding portfolios
- **Job Search**: Real-time job market intelligence and postings
- **File Management**: Save and organize analyses and learning materials

## Architecture

```
Unified Web Application
├── React TypeScript Frontend
│   ├── Job Analysis Form
│   ├── Saved Analyses Dashboard
│   ├── Learning Progress Tracker
│   ├── GitHub Profile Analyzer
│   ├── Job Search Interface
│   └── File Manager
│
└── FastAPI Backend
    ├── LangGraph Agent (Job Analysis)
    ├── MCP Tools Integration
    ├── SQLite Database
    ├── Vector Store (FAISS/Pinecone)
    └── External API Integrations
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, async programming
- **Frontend**: React TypeScript, modern UI components
- **AI/ML**: LangGraph agents, LangChain, OpenAI GPT-4o-mini
- **Data**: SQLite database, FAISS/Pinecone vector stores
- **APIs**: GitHub API, job search APIs, MCP protocol
- **Infrastructure**: Docker, MCP server for AI assistant integration

## Quick Start

1. **Clone & Setup**:

   ```bash
   git clone <repo>
   cd ai-job-research
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Set API Keys**:
   Create `.env` file:
   ```
   OPENAI_API_KEY=your-openai-key-here
   GITHUB_TOKEN=your-github-token-here  # Optional, for enhanced GitHub analysis
   ```

3. **Start the Application**:

   ```bash
   ./run.sh
   ```

   Or run manually:

   ```bash
   # Backend (Terminal 1)
   export KMP_DUPLICATE_LIB_OK=TRUE
   uvicorn app.main:app --reload

   # Frontend (Terminal 2)
   cd frontend && npm start
   ```

4. **Open your browser** to http://localhost:3000

The application provides a complete career development dashboard with all features accessible through a single web interface.

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

## MCP Server Integration

A **Model Context Protocol (MCP) server** is included for advanced AI assistant integration. All MCP functionality is also available through the web interface.

### What is MCP?

MCP allows AI assistants (like Claude) to securely access external tools and data sources through a standardized protocol.

### Features Available via Web & MCP

- **Persistent Storage**: SQLite database for user profiles and job analyses
- **Learning Progress Tracking**: Monitor skill development over time
- **GitHub Profile Analysis**: Extract skills from coding portfolios
- **Job Market Intelligence**: Search real-time job postings
- **File System Operations**: Save/load analyses and learning plans

### Web Interface (Recommended)

The React frontend provides a user-friendly interface for all features:
- Job analysis with instant results
- Saved analyses dashboard
- Learning progress tracking
- GitHub profile analysis
- Job search functionality
- File management tools

### MCP Server Setup (Optional)

For integration with AI assistants like Claude Desktop:

```bash
# Start the MCP server
cd mcp-server
pip install -r requirements.txt
python server.py
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "job-research": {
      "command": "python",
      "args": ["/path/to/project/mcp-server/server.py"]
    }
  }
}
```

## Features Guide

### Job Analysis
Paste any job description and your current skills to get:
- Required skills extraction
- Skill gap analysis
- Personalized learning plan
- Relevant resources and courses

### Advanced RAG Pipeline
- Multi-stage retrieval that combines skills-derived queries with advanced context assembly for richer answers
- Runs an evaluation step to score and surface RAG quality alongside the response
- Feeds both basic and advanced RAG outputs into the learning plan for more grounded guidance

### Saved Analyses
- Store unlimited job analyses
- Compare opportunities over time
- Track career progression
- Export and share analyses

### Learning Progress Tracking
- Monitor skill development
- Set progress goals
- Track completed modules
- Visualize learning journey

### GitHub Profile Analysis
- Analyze coding portfolios
- Extract technical skills
- Suggest job roles
- Identify areas for improvement

### Job Search
- Real-time job market data
- Filter by keywords and location
- Direct application links
- Market trend insights

### File Management
- Save analyses as files
- Organize learning materials
- Backup important documents
- Share resources across devices
