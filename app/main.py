from fastapi import FastAPI
from app.agent import agent
from app.models import JobAnalysisRequest, JobAnalysisResponse

app = FastAPI(title="AI Job Research & Summary Agent")

@app.post("/analyze", response_model=JobAnalysisResponse)
async def analyze_job(request: JobAnalysisRequest):
    initial_state = {
        "job_description": request.job_description,
        "current_skills": request.current_skills,
    }
    result = agent.invoke(initial_state)
    return JobAnalysisResponse(
        skills_required=result["skills_required"],
        skill_gaps=result["skill_gaps"],
        learning_plan=result["learning_plan"],
        relevant_resources=result["relevant_resources"]
    )

@app.get("/")
async def root():
    return {"message": "AI Job Research & Summary Agent API"}