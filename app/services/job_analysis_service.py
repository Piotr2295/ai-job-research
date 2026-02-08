"""
Job analysis service - business logic for job analysis.
"""

import logging

from app.agent import agent
from app.models import JobAnalysisRequest, JobAnalysisResponse
from app.validators import (
    validate_github_username,
    validate_optional_string,
    validate_required_string,
    validate_skill_list,
)

logger = logging.getLogger(__name__)


class JobAnalysisService:
    """Service for handling job analysis operations"""

    async def analyze_job(self, payload: JobAnalysisRequest) -> JobAnalysisResponse:
        """
        Analyze a job using the agentic reasoning loop

        Args:
            payload: Job analysis request with job description and skills

        Returns:
            JobAnalysisResponse with analysis results
        """
        # Validate inputs
        validate_skill_list(payload.current_skills)
        if payload.github_username:
            payload.github_username = validate_github_username(payload.github_username)

        # Initialize agent state with required fields
        initial_state = {
            "job_description": validate_required_string(
                payload.job_description, "job_description", max_length=20000
            ),
            "current_skills": validate_skill_list(payload.current_skills),
            "job_title": validate_optional_string(
                getattr(payload, "job_title", ""), "job_title"
            )
            or "",
            "location": validate_optional_string(
                getattr(payload, "location", "Remote"), "location"
            )
            or "Remote",
            "github_username": payload.github_username,
            "skills_required": [],
            "skill_gaps": [],
            "rag_results": None,
            "skill_validation_results": None,
            "market_research_results": None,
            "gap_analysis_results": None,
            "learning_plan_results": None,
            "github_analysis_results": None,
            "validation_report": None,
            "reflection_feedback": None,
            "tool_call_count": 0,
            "max_tool_calls": 5,
            "executed_tools": [],
            "agent_reasoning": [],
            "reflection_iterations": 0,
            "learning_plan": "",
            "analysis_quality_score": 0.0,
            "analysis_confidence_score": 0.0,
            "rag_evaluation": {},
        }

        # Run the agentic workflow
        result = agent.invoke(initial_state)

        return JobAnalysisResponse(
            skills_required=result["skills_required"],
            skill_gaps=result["skill_gaps"],
            learning_plan=result["learning_plan"],
            relevant_resources=result.get("rag_results", {}).get("resources", []),
        )
