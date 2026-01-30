"""
Tool definitions for the reasoning agent.
Allows the agent to choose which tools to use based on the job analysis.
"""

from typing import TypedDict, Optional
from enum import Enum
from langchain_openai import ChatOpenAI
from app.rag import (
    retrieve_resources,
    query_advanced_rag,
    evaluate_rag_performance,
)
from app.prompts import (
    GAP_ANALYSIS_PROMPT,
    LEARNING_PLAN_PROMPT,
)
from dotenv import load_dotenv
import httpx

load_dotenv()


class ToolType(str, Enum):
    """Available tools the agent can choose from"""

    RAG_QUERY = "rag_query"
    SKILL_VALIDATOR = "skill_validator"
    MARKET_RESEARCH = "market_research"
    LEARNING_PATH_GENERATOR = "learning_path_generator"
    GAP_ANALYZER = "gap_analyzer"
    GITHUB_ANALYZER = "github_analyzer"


class ToolResult(TypedDict):
    """Result from a tool execution"""

    tool: str
    success: bool
    data: dict
    confidence: float
    error: Optional[str]


class AgentAction(TypedDict):
    """Action the agent decides to take"""

    reasoning: str
    selected_tools: list[ToolType]
    should_continue: bool
    next_action: Optional[str]


# TOOL IMPLEMENTATIONS
def rag_query_tool(skills_required: list[str], job_description: str) -> ToolResult:
    """
    Query the advanced RAG pipeline for learning resources and insights.
    """
    try:
        query = "Advanced learning plan for skills: " + " ".join(skills_required)
        advanced_response = query_advanced_rag(query)
        evaluation = evaluate_rag_performance(query, advanced_response)

        return ToolResult(
            tool=ToolType.RAG_QUERY.value,
            success=True,
            data={
                "rag_response": advanced_response,
                "evaluation": evaluation,
                "resources": retrieve_resources(query),
            },
            confidence=evaluation.get("relevance_score", 0.7),
            error=None,
        )
    except Exception as e:
        return ToolResult(
            tool=ToolType.RAG_QUERY.value,
            success=False,
            data={},
            confidence=0.0,
            error=str(e),
        )


def skill_validator_tool(
    required_skills: list[str], current_skills: list[str]
) -> ToolResult:
    """
    Validate skills: check relevance, identify gaps, validate prerequisites.
    """
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        prompt = f"""
        Analyze these skills from a validation perspective:

        REQUIRED SKILLS: {', '.join(required_skills)}
        CURRENT SKILLS: {', '.join(current_skills)}

        For each required skill, provide:
        1. Is it current/relevant in 2026?
        2. What are prerequisite skills?
        3. How rare/valuable is this skill?
        4. Market demand (high/medium/low)

        Format as structured JSON.
        """

        response = llm.invoke(prompt)

        # Simple confidence based on skill match
        matched = len(set(required_skills) & set(current_skills))
        confidence = matched / len(required_skills) if required_skills else 0.5

        return ToolResult(
            tool=ToolType.SKILL_VALIDATOR.value,
            success=True,
            data={
                "validation_analysis": response.content,
                "matched_skills": matched,
                "total_required": len(required_skills),
            },
            confidence=confidence,
            error=None,
        )
    except Exception as e:
        return ToolResult(
            tool=ToolType.SKILL_VALIDATOR.value,
            success=False,
            data={},
            confidence=0.0,
            error=str(e),
        )


def market_research_tool(
    job_title: str, required_skills: list[str], location: str = "Remote"
) -> ToolResult:
    """
    Research market trends, salary ranges, and competitive skills.
    """
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        prompt = f"""
        Research the job market for:
        JOB TITLE: {job_title}
        LOCATION: {location}
        REQUIRED SKILLS: {', '.join(required_skills)}

        Provide:
        1. Typical salary range for this role
        2. Most in-demand skills for this role
        3. Career progression path
        4. Market demand level (high/medium/low)
        5. Top competitors' skill profile
        6. Emerging skills to watch

        Format as structured analysis.
        """

        response = llm.invoke(prompt)

        return ToolResult(
            tool=ToolType.MARKET_RESEARCH.value,
            success=True,
            data={
                "market_analysis": response.content,
            },
            confidence=0.8,
            error=None,
        )
    except Exception as e:
        return ToolResult(
            tool=ToolType.MARKET_RESEARCH.value,
            success=False,
            data={},
            confidence=0.0,
            error=str(e),
        )


def gap_analyzer_tool(
    required_skills: list[str], current_skills: list[str]
) -> ToolResult:
    """
    Deeply analyze skill gaps with learning difficulty and priority.
    """
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        prompt = GAP_ANALYSIS_PROMPT.format(
            required_skills=", ".join(required_skills),
            current_skills=", ".join(current_skills),
        )

        response = llm.invoke(prompt)
        gaps = [gap.strip() for gap in response.content.split(",")]

        gap_analysis_prompt = f"""
        For these skill gaps, provide:
        GAPS: {', '.join(gaps)}

        For each gap:
        1. Learning difficulty (1-10)
        2. Time to learn (days/weeks/months)
        3. Priority level (critical/important/nice-to-have)
        4. Dependencies on other skills
        5. Best learning approach

        Format as prioritized learning roadmap.
        """

        detailed_response = llm.invoke(gap_analysis_prompt)

        return ToolResult(
            tool=ToolType.GAP_ANALYZER.value,
            success=True,
            data={
                "identified_gaps": gaps,
                "gap_analysis": detailed_response.content,
            },
            confidence=0.85,
            error=None,
        )
    except Exception as e:
        return ToolResult(
            tool=ToolType.GAP_ANALYZER.value,
            success=False,
            data={},
            confidence=0.0,
            error=str(e),
        )


def learning_path_generator_tool(
    job_title: str, skill_gaps: list[str], current_level: str = "intermediate"
) -> ToolResult:
    """
    Generate a personalized learning path with timeline and resources.
    """
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        prompt = LEARNING_PLAN_PROMPT.format(
            gaps=", ".join(skill_gaps),
            resources="",  # Will be filled from RAG results
        )

        response = llm.invoke(prompt)

        return ToolResult(
            tool=ToolType.LEARNING_PATH_GENERATOR.value,
            success=True,
            data={
                "learning_plan": response.content,
            },
            confidence=0.8,
            error=None,
        )
    except Exception as e:
        return ToolResult(
            tool=ToolType.LEARNING_PATH_GENERATOR.value,
            success=False,
            data={},
            confidence=0.0,
            error=str(e),
        )


def github_analyzer_tool(github_username: str) -> ToolResult:
    """
    Analyze GitHub profile to extract technologies, projects, and proven skills.
    This enriches job analysis with candidate's actual project portfolio.
    """
    try:
        import asyncio

        async def fetch_github_data():
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get user profile
                user_response = await client.get(
                    f"https://api.github.com/users/{github_username}"
                )
                user_data = user_response.json()

                # Get repositories (top 20 by update)
                repos_response = await client.get(
                    f"https://api.github.com/users/{github_username}/repos?sort=updated&per_page=20"
                )
                repos_data = repos_response.json()

                return user_data, repos_data

        # Run async fetch
        user_data, repos_data = asyncio.run(fetch_github_data())

        # Analyze languages and technologies
        languages = {}
        technologies = set()
        project_types = set()

        for repo in repos_data:
            # Count language usage
            if repo.get("language"):
                languages[repo["language"]] = languages.get(repo["language"], 0) + 1

            # Extract technologies from repo name and topics
            name = repo.get("name", "").lower()
            topics = repo.get("topics", [])

            # Analyze project patterns
            if any(kw in name for kw in ["api", "rest", "backend", "server"]):
                project_types.add("API Development")
            if any(kw in name for kw in ["react", "vue", "angular", "frontend", "ui"]):
                project_types.add("Frontend Development")
            if any(kw in name for kw in ["ml", "ai", "machine", "learning", "model"]):
                project_types.add("Machine Learning")
            if any(kw in name for kw in ["fastapi", "flask", "django"]):
                project_types.add("Python Web Development")
            if any(kw in name for kw in ["docker", "kubernetes", "k8s"]):
                project_types.add("DevOps")
            if any(kw in name for kw in ["test", "testing", "pytest", "jest"]):
                project_types.add("Testing & QA")

            # Add topics as technologies
            for topic in topics:
                technologies.add(topic)

        # Calculate activity metrics
        total_repos = user_data.get("public_repos", 0)
        followers = user_data.get("followers", 0)
        recent_activity = len([r for r in repos_data if r.get("updated_at")])

        # Calculate confidence based on activity
        confidence = min(
            1.0,
            (
                (total_repos * 0.01)
                + (followers * 0.005)
                + (recent_activity * 0.02)
                + (len(languages) * 0.05)
            ),
        )

        # Sort languages by usage
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)

        return ToolResult(
            tool=ToolType.GITHUB_ANALYZER.value,
            success=True,
            data={
                "username": github_username,
                "profile_url": f"https://github.com/{github_username}",
                "metrics": {
                    "total_repos": total_repos,
                    "followers": followers,
                    "following": user_data.get("following", 0),
                    "recent_activity": recent_activity,
                },
                "languages": [
                    {"name": lang, "repos": count} for lang, count in top_languages
                ],
                "technologies": sorted(list(technologies)),
                "project_types": sorted(list(project_types)),
                "proven_skills": {
                    "programming_languages": [lang for lang, _ in top_languages[:5]],
                    "frameworks_and_tools": sorted(list(technologies))[:10],
                    "experience_areas": sorted(list(project_types)),
                },
            },
            confidence=confidence,
            error=None,
        )

    except Exception as e:
        return ToolResult(
            tool=ToolType.GITHUB_ANALYZER.value,
            success=False,
            data={},
            confidence=0.0,
            error=f"GitHub analysis failed: {str(e)}",
        )


# TOOL EXECUTOR


def execute_tool(tool_type: ToolType, **kwargs) -> ToolResult:
    """
    Execute a tool and return the result.
    """
    if tool_type == ToolType.RAG_QUERY:
        return rag_query_tool(
            skills_required=kwargs.get("skills_required", []),
            job_description=kwargs.get("job_description", ""),
        )
    elif tool_type == ToolType.SKILL_VALIDATOR:
        return skill_validator_tool(
            required_skills=kwargs.get("required_skills", []),
            current_skills=kwargs.get("current_skills", []),
        )
    elif tool_type == ToolType.MARKET_RESEARCH:
        return market_research_tool(
            job_title=kwargs.get("job_title", ""),
            required_skills=kwargs.get("required_skills", []),
            location=kwargs.get("location", "Remote"),
        )
    elif tool_type == ToolType.GAP_ANALYZER:
        return gap_analyzer_tool(
            required_skills=kwargs.get("required_skills", []),
            current_skills=kwargs.get("current_skills", []),
        )
    elif tool_type == ToolType.LEARNING_PATH_GENERATOR:
        return learning_path_generator_tool(
            job_title=kwargs.get("job_title", ""),
            skill_gaps=kwargs.get("skill_gaps", []),
            current_level=kwargs.get("current_level", "intermediate"),
        )
    elif tool_type == ToolType.GITHUB_ANALYZER:
        return github_analyzer_tool(
            github_username=kwargs.get("github_username", ""),
        )
    else:
        return ToolResult(
            tool=tool_type.value,
            success=False,
            data={},
            confidence=0.0,
            error=f"Unknown tool: {tool_type}",
        )
