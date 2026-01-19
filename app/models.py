from pydantic import BaseModel

class JobAnalysisRequest(BaseModel):
    job_description: str
    current_skills: list[str] = []

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