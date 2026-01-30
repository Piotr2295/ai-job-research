"""
Test GitHub integration in the agent workflow
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from app.agent_tools import github_analyzer_tool, ToolType


def test_github_analyzer_tool_success():
    """Test GitHub analyzer with a real GitHub user"""
    # Use a well-known GitHub user
    result = github_analyzer_tool("torvalds")

    # Verify structure
    assert result["tool"] == ToolType.GITHUB_ANALYZER.value
    assert result["success"] is True
    assert result["error"] is None
    assert result["confidence"] > 0

    # Verify data structure
    data = result["data"]
    assert "username" in data
    assert "profile_url" in data
    assert "metrics" in data
    assert "languages" in data
    assert "proven_skills" in data

    # Verify metrics
    assert data["metrics"]["total_repos"] > 0

    # Verify proven skills structure
    proven_skills = data["proven_skills"]
    assert "programming_languages" in proven_skills
    assert "frameworks_and_tools" in proven_skills
    assert "experience_areas" in proven_skills

    # Linus should have C in his languages
    languages = [lang["name"] for lang in data["languages"]]
    assert len(languages) > 0


def test_github_analyzer_tool_invalid_user():
    """Test GitHub analyzer with invalid username"""
    result = github_analyzer_tool("this-user-definitely-does-not-exist-12345")

    # Should handle error gracefully
    assert result["tool"] == ToolType.GITHUB_ANALYZER.value
    assert result["success"] is False
    assert result["error"] is not None
    assert result["confidence"] == 0.0


def test_github_integration_in_agent():
    """Test that agent state properly includes GitHub data"""
    from app.agent import AgentState

    # Create initial state with GitHub username
    state: AgentState = {
        "job_description": "Python developer needed",
        "current_skills": ["Python"],
        "job_title": "Python Developer",
        "location": "Remote",
        "github_username": "test-user",
        "skills_required": [],
        "skill_gaps": [],
        "rag_results": None,
        "skill_validation_results": None,
        "market_research_results": None,
        "gap_analysis_results": None,
        "learning_plan_results": None,
        "github_analysis_results": None,
        "tool_call_count": 0,
        "max_tool_calls": 5,
        "executed_tools": [],
        "agent_reasoning": [],
        "learning_plan": "",
        "analysis_quality_score": 0.0,
        "rag_evaluation": {},
    }

    # Verify state has github_username
    assert "github_username" in state
    assert state["github_username"] == "test-user"
    assert "github_analysis_results" in state
