from pydantic import BaseModel

class JobAnalysisRequest(BaseModel):
    job_description: str
    current_skills: list[str] = []

class JobAnalysisResponse(BaseModel):
    skills_required: list[str]
    skill_gaps: list[str]
    learning_plan: str
    relevant_resources: list[str]