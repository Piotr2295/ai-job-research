from pydantic import BaseModel
from typing import Optional


class JobAnalysisRequest(BaseModel):
    job_description: str
    current_skills: list[str] = []
    github_username: Optional[str] = (
        None  # Optional GitHub profile for enriched analysis
    )


class JobAnalysisResponse(BaseModel):
    skills_required: list[str]
    skill_gaps: list[str]
    learning_plan: str
    relevant_resources: list[str]


class SaveJobAnalysisRequest(BaseModel):
    user_id: str
    job_title: str
    company: str
    skills_required: list[str]
    skill_gaps: list[str]
    learning_plan: str


class UpdateLearningProgressRequest(BaseModel):
    user_id: str
    skill: str
    progress_percentage: int
    completed_modules: list[str]


class SaveFileRequest(BaseModel):
    filename: str
    content: str
    directory: str = "analyses"


class UserExperience(BaseModel):
    role: str
    company: str
    duration: str
    achievements: list[str]
    skills: list[str]


class AddUserExperienceRequest(BaseModel):
    user_id: str
    experiences: list[UserExperience]


class ResumeOptimizationRequest(BaseModel):
    user_id: str
    job_description: str
    target_role: str
    target_company: str


class UploadResumeRequest(BaseModel):
    user_id: str


class ParsedResume(BaseModel):
    user_id: str
    full_text: str
    sections: dict[
        str, str
    ]  # e.g., {"experience": "...", "skills": "...", "education": "..."}
    extracted_experiences: list[UserExperience]
    filename: str


class EnhancedJobAnalysisRequest(BaseModel):
    """Request for enhanced job analysis from resume"""

    user_id: str
    resume_id: int  # ID of uploaded resume
    location: str = "remote"
    experience_level: Optional[str] = None  # junior, mid, senior
    num_jobs: int = 5
    specific_role: Optional[str] = None  # e.g., "Python Developer"


class SpecificJobAnalysisRequest(BaseModel):
    """Analyze a specific job description against resume"""

    user_id: str
    resume_id: int
    job_description: str
    job_title: Optional[str] = None
    company: Optional[str] = None


class JobMatchResult(BaseModel):
    """Single job match result"""

    job_info: dict
    requirements: dict
    skill_match: dict
    gap_analysis: str
    learning_resources: list[str]
    recommendation: str


class EnhancedJobAnalysisResponse(BaseModel):
    """Response from enhanced job analysis"""

    user_skills: dict
    jobs_analyzed: int
    job_matches: list[dict]  # List of JobMatchResult dicts
    overall_recommendations: dict = {}  # Make optional with default
    search_criteria: dict = {}  # Make optional with default
    error_message: Optional[str] = None  # For when search fails
