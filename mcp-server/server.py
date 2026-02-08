#!/usr/bin/env python3
"""
MCP Server for AI Job Research Assistant

This MCP server provides tools for:
- File system operations (save/load job analyses)
- User profile management
- External API integrations (GitHub, job boards)
- Learning progress tracking
"""

import asyncio
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import List

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import httpx

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("job-research-mcp")

# Database setup
DB_PATH = Path(__file__).parent / "job_research.db"


def init_database():
    """Initialize SQLite database for user profiles and learning progress"""
    logger.info("Initializing SQLite database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # User profiles table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            name TEXT,
            email TEXT,
            current_skills TEXT,  -- JSON array
            career_goals TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Job analyses table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            job_title TEXT,
            company TEXT,
            skills_required TEXT,  -- JSON array
            skill_gaps TEXT,       -- JSON array
            learning_plan TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
        )
    """
    )

    # Learning progress table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            skill TEXT,
            progress_percentage INTEGER DEFAULT 0,
            completed_modules TEXT,  -- JSON array
            target_completion_date DATE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
        )
    """
    )

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)


# Initialize database on startup
init_database()

server = Server("job-research-mcp")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    logger.info("Listing available MCP tools")
    tools = [
        types.Tool(
            name="save_job_analysis",
            description="Save a job analysis to the database for future reference",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Unique identifier for the user",
                    },
                    "job_title": {
                        "type": "string",
                        "description": "Title of the analyzed job",
                    },
                    "company": {"type": "string", "description": "Company name"},
                    "skills_required": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of required skills",
                    },
                    "skill_gaps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of skill gaps identified",
                    },
                    "learning_plan": {
                        "type": "string",
                        "description": "Generated learning plan",
                    },
                },
                "required": [
                    "user_id",
                    "job_title",
                    "company",
                    "skills_required",
                    "skill_gaps",
                    "learning_plan",
                ],
            },
        ),
        types.Tool(
            name="get_user_analyses",
            description="Retrieve previous job analyses for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Unique identifier for the user",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of analyses to return",
                        "default": 10,
                    },
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="update_learning_progress",
            description="Update learning progress for a specific skill",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Unique identifier for the user",
                    },
                    "skill": {
                        "type": "string",
                        "description": "Name of the skill being learned",
                    },
                    "progress_percentage": {
                        "type": "integer",
                        "description": "Progress percentage (0-100)",
                    },
                    "completed_modules": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of completed learning modules",
                    },
                },
                "required": [
                    "user_id",
                    "skill",
                    "progress_percentage",
                    "completed_modules",
                ],
            },
        ),
        types.Tool(
            name="analyze_github_profile",
            description="Analyze a GitHub profile to extract coding skills and project experience",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "GitHub username"}
                },
                "required": ["username"],
            },
        ),
        types.Tool(
            name="search_job_postings",
            description="Search for job postings using a public job API",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Job search keyword"},
                    "location": {
                        "type": "string",
                        "description": "Location for job search",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 5,
                    },
                },
                "required": ["keyword"],
            },
        ),
        types.Tool(
            name="save_file_to_workspace",
            description="Save content to a file in the workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to create",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to save in",
                        "default": "analyses",
                    },
                },
                "required": ["filename", "content"],
            },
        ),
        types.Tool(
            name="read_file_from_workspace",
            description="Read content from a file in the workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to read",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory containing the file",
                        "default": "analyses",
                    },
                },
                "required": ["filename"],
            },
        ),
    ]
    logger.info(f"Available tools: {[tool.name for tool in tools]}")
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls using registry pattern"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    # Look up the handler function
    handler = TOOL_HANDLERS.get(name)

    if handler is None:
        logger.error(f"Unknown tool: {name}")
        raise ValueError(f"Unknown tool: {name}")

    # Call the handler with the arguments
    result = await handler(**arguments)

    logger.info(f"{name} completed successfully")
    return [types.TextContent(type="text", text=result)]


# Implementation functions
async def save_job_analysis_impl(
    user_id: str,
    job_title: str,
    company: str,
    skills_required: List[str],
    skill_gaps: List[str],
    learning_plan: str,
) -> str:
    """Save a job analysis to the database"""
    logger.info(f"Saving job analysis for user {user_id}: {job_title} at {company}")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO job_analyses
        (user_id, job_title, company, skills_required, skill_gaps, learning_plan)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            job_title,
            company,
            json.dumps(skills_required),
            json.dumps(skill_gaps),
            learning_plan,
        ),
    )

    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logger.info(f"Job analysis saved with ID: {analysis_id}")
    return f"Job analysis saved successfully with ID: {analysis_id}"


async def get_user_analyses_impl(user_id: str, limit: int = 10) -> str:
    """Retrieve previous job analyses for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, job_title, company, skills_required, skill_gaps,
               learning_plan, analysis_date
        FROM job_analyses
        WHERE user_id = ?
        ORDER BY analysis_date DESC
        LIMIT ?
    """,
        (user_id, limit),
    )

    analyses = []
    for row in cursor.fetchall():
        analyses.append(
            {
                "id": row[0],
                "job_title": row[1],
                "company": row[2],
                "skills_required": json.loads(row[3]),
                "skill_gaps": json.loads(row[4]),
                "learning_plan": row[5],
                "analysis_date": row[6],
            }
        )

    conn.close()
    return json.dumps(analyses, indent=2)


async def update_learning_progress_impl(
    user_id: str, skill: str, progress_percentage: int, completed_modules: List[str]
) -> str:
    """Update learning progress for a specific skill"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if progress record exists
    cursor.execute(
        "SELECT id FROM learning_progress WHERE user_id = ? AND skill = ?",
        (user_id, skill),
    )

    existing = cursor.fetchone()

    if existing:
        # Update existing record
        cursor.execute(
            """
            UPDATE learning_progress
            SET progress_percentage = ?, completed_modules = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND skill = ?
        """,
            (progress_percentage, json.dumps(completed_modules), user_id, skill),
        )
    else:
        # Create new record
        cursor.execute(
            """
            INSERT INTO learning_progress (user_id, skill, progress_percentage, completed_modules)
            VALUES (?, ?, ?, ?)
        """,
            (user_id, skill, progress_percentage, json.dumps(completed_modules)),
        )

    conn.commit()
    conn.close()

    return f"Learning progress updated for {skill}: {progress_percentage}% complete"


async def analyze_github_profile_impl(username: str) -> str:
    """Analyze a GitHub profile"""
    logger.info(f"Analyzing GitHub profile for user: {username}")
    try:
        async with httpx.AsyncClient() as client:
            # Get user profile
            user_response = await client.get(f"https://api.github.com/users/{username}")
            user_data = user_response.json()

            # Get user repositories
            repos_response = await client.get(
                f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
            )
            repos_data = repos_response.json()

        # Extract skills from repository languages and names
        languages = {}
        project_types = []

        for repo in repos_data:
            if repo.get("language"):
                languages[repo["language"]] = languages.get(repo["language"], 0) + 1

            # Analyze project names for technologies
            name = repo.get("name", "").lower()
            if any(keyword in name for keyword in ["api", "rest", "backend"]):
                project_types.append("API Development")
            if any(
                keyword in name for keyword in ["react", "vue", "angular", "frontend"]
            ):
                project_types.append("Frontend Development")
            if any(keyword in name for keyword in ["ml", "ai", "machine", "learning"]):
                project_types.append("Machine Learning")
            if any(keyword in name for keyword in ["fastapi", "flask", "django"]):
                project_types.append("Python Web Development")

        # Generate analysis
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]

        analysis = f"""
GitHub Profile Analysis for @{username}

**Profile Summary:**
- Public Repositories: {user_data.get('public_repos', 0)}
- Followers: {user_data.get('followers', 0)}
- Following: {user_data.get('following', 0)}

**Top Programming Languages:**
{chr(10).join(f"- {lang}: {count} repositories" for lang, count in top_languages)}

**Inferred Skills:**
{chr(10).join(f"- {skill}" for skill in list(set(project_types)))}

**Suggested Job Roles:**
Based on this profile, you would be well-suited for:
- {'Full-Stack Developer' if 'Frontend Development' in project_types and 'API Development' in project_types else ''}
- {'Backend Developer' if 'API Development' in project_types else ''}
- {'Frontend Developer' if 'Frontend Development' in project_types else ''}
- {'ML Engineer' if 'Machine Learning' in project_types else ''}
- {'Python Developer' if any(lang[0] == 'Python' for lang in top_languages) else ''}
        """.strip()

        logger.info(f"GitHub analysis completed for {username}")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing GitHub profile for {username}: {str(e)}")
        return f"Error analyzing GitHub profile: {str(e)}"


async def search_job_postings_impl(
    keyword: str, location: str = "", limit: int = 5
) -> str:
    """Search for job postings"""
    try:
        # Using a free job search API (JSearch by RapidAPI as example)
        url = "https://jsearch.p.rapidapi.com/search"

        querystring = {
            "query": f"{keyword} in {location}" if location else keyword,
            "page": "1",
            "num_pages": "1",
        }

        headers = {
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", ""),
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=querystring)
            data = response.json()

        if "data" not in data:
            return "No job postings found or API limit reached."

        jobs = data["data"][:limit]

        results = []
        for job in jobs:
            results.append(
                {
                    "title": job.get("job_title", "Unknown"),
                    "company": job.get("employer_name", "Unknown"),
                    "location": job.get("job_city", "Remote"),
                    "description": job.get("job_description", "")[:200] + "...",
                    "url": job.get("job_apply_link", ""),
                }
            )

        return json.dumps(results, indent=2)

    except Exception as e:
        return f"Error searching job postings: {str(e)}. Note: Requires RAPIDAPI_KEY environment variable."


async def save_file_to_workspace_impl(
    filename: str, content: str, directory: str = "analyses"
) -> str:
    """Save content to a file in the workspace"""
    workspace_dir = Path(__file__).parent.parent
    file_path = workspace_dir / directory / filename

    # Create directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write content to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"File saved successfully: {file_path}"


async def read_file_from_workspace_impl(
    filename: str, directory: str = "analyses"
) -> str:
    """Read content from a file in the workspace"""
    workspace_dir = Path(__file__).parent.parent
    file_path = workspace_dir / directory / filename

    if not file_path.exists():
        return f"File not found: {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return content


# Tool handler registry - maps tool names to their implementation functions
# NOTE: Must be defined AFTER all implementation functions
TOOL_HANDLERS = {
    "save_job_analysis": save_job_analysis_impl,
    "get_user_analyses": get_user_analyses_impl,
    "update_learning_progress": update_learning_progress_impl,
    "analyze_github_profile": analyze_github_profile_impl,
    "search_job_postings": search_job_postings_impl,
    "save_file_to_workspace": save_file_to_workspace_impl,
    "read_file_from_workspace": read_file_from_workspace_impl,
}


async def main():
    """Main entry point for the MCP server"""
    logger.info("Starting MCP server for AI Job Research Assistant")
    logger.info("Server capabilities: tools, database operations, external APIs")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP server ready and waiting for connections")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="job-research-mcp",
                server_version="0.1.0",
                capabilities={
                    "logging": {},
                    "tools": {"listChanged": True},
                },
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
