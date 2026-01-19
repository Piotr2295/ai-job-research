# MCP Server Configuration for AI Job Research

This MCP server provides tools for the AI Job Research Assistant to interact with external data sources and persist information.

## Available Tools

### Database Tools
- `save_job_analysis`: Save job analysis results to SQLite database
- `get_user_analyses`: Retrieve previous job analyses for a user
- `update_learning_progress`: Track learning progress for skills

### External API Tools
- `analyze_github_profile`: Analyze GitHub profiles for skill inference
- `search_job_postings`: Search for job postings (requires RapidAPI key)

### File System Tools
- `save_file_to_workspace`: Save content to files in the workspace
- `read_file_from_workspace`: Read content from workspace files

## Setup

1. Install dependencies:
   ```bash
   cd mcp-server
   pip install -r requirements.txt
   ```

2. Set environment variables (optional):
   ```bash
   export RAPIDAPI_KEY=your-rapidapi-key  # For job search
   ```

3. Run the MCP server:
   ```bash
   python server.py
   ```

## Integration with Claude Desktop

To use this MCP server with Claude Desktop:

1. Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Add the server configuration:

```json
{
  "mcpServers": {
    "job-research-mcp": {
      "command": "python",
      "args": ["/Users/piotrciszek/Desktop/Repositories/ai-job-research/mcp-server/server.py"],
      "env": {
        "PYTHONPATH": "/Users/piotrciszek/Desktop/Repositories/ai-job-research"
      }
    }
  }
}

```
    "env": {
        "RAPIDAPI_KEY": "your-rapidapi-key"
      }
    }
  }
}
```

## Use Cases for Job Research

### 1. Persistent Job Analysis History
- Save all job analyses to database
- Track career progression over time
- Compare skill requirements across roles

### 2. Learning Progress Tracking
- Monitor completion of learning modules
- Set target completion dates
- Generate progress reports

### 3. GitHub Portfolio Analysis
- Automatically analyze candidate's coding skills
- Extract technology stack from repositories
- Generate skill assessments

### 4. Real-time Job Market Intelligence
- Search current job postings
- Compare salary ranges
- Identify trending skills

### 5. Document Management
- Save learning plans as files
- Load previous analyses
- Export reports

## Database Schema

The server creates three SQLite tables:

- `user_profiles`: User information and career goals
- `job_analyses`: Saved job analysis results
- `learning_progress`: Skill learning tracking

## Example Usage

Once connected to Claude, you can ask:

- "Save this job analysis for user123"
- "What jobs has user123 analyzed before?"
- "Update my Python learning progress to 75%"
- "Analyze the GitHub profile of octocat"
- "Find Python developer jobs in San Francisco"
- "Save this learning plan to a file"