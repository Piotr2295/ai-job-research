from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.agent import agent
from app.models import JobAnalysisRequest, JobAnalysisResponse

app = FastAPI(title="AI Job Research & Summary Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Job Research & Summary Agent API"}

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