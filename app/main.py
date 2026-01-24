import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.models import (
    JobAnalysisRequest,
    JobAnalysisResponse,
    SaveJobAnalysisRequest,
    UpdateLearningProgressRequest,
    SaveFileRequest,
    AddUserExperienceRequest,
    ResumeOptimizationRequest,
)
import sqlite3
import json
import os
from pathlib import Path
import httpx
from app.agent import agent

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Job Research & Summary Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = Path(__file__).parent.parent / "mcp-server" / "job_research.db"


def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)


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
        relevant_resources=result["relevant_resources"],
    )


# MCP Server functionality integrated into FastAPI


@app.post("/api/save-job-analysis")
async def save_job_analysis(request: SaveJobAnalysisRequest):
    """Save a job analysis to the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO job_analyses
            (user_id, job_title, company, skills_required, skill_gaps, learning_plan)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request.user_id,
                request.job_title,
                request.company,
                json.dumps(request.skills_required),
                json.dumps(request.skill_gaps),
                request.learning_plan,
            ),
        )

        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {"message": (f"Job analysis saved successfully with ID: {analysis_id}")}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error saving job analysis: {str(e)}"
        )


@app.get("/api/user-analyses/{user_id}")
async def get_user_analyses(user_id: str, limit: int = 10):
    """Retrieve previous job analyses for a user"""
    try:
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
        return {"analyses": analyses}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving analyses: {str(e)}"
        )


@app.post("/api/update-learning-progress")
async def update_learning_progress(request: UpdateLearningProgressRequest):
    """Update learning progress for a specific skill"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if progress record exists
        cursor.execute(
            "SELECT id FROM learning_progress WHERE user_id = ? AND skill = ?",
            (request.user_id, request.skill),
        )

        existing = cursor.fetchone()

        if existing:
            # Update existing record
            cursor.execute(
                """
                UPDATE learning_progress
                SET progress_percentage = ?, completed_modules = ?, \
                updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND skill = ?
            """,
                (
                    request.progress_percentage,
                    json.dumps(request.completed_modules),
                    request.user_id,
                    request.skill,
                ),
            )
        else:
            # Create new record
            cursor.execute(
                """
                INSERT INTO learning_progress (user_id, skill, progress_percentage, completed_modules)
                VALUES (?, ?, ?, ?)
            """,
                (
                    request.user_id,
                    request.skill,
                    request.progress_percentage,
                    json.dumps(request.completed_modules),
                ),
            )

        conn.commit()
        conn.close()

        return {
            "message": (
                f"Learning progress updated for {request.skill}: "
                f"{request.progress_percentage}% complete"
            )
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating progress: {str(e)}"
        )


@app.get("/api/analyze-github/{username}")
async def analyze_github_profile(username: str):
    """Analyze a GitHub profile"""
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

        analysis = {
            "username": username,
            "profile_summary": {
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
            },
            "top_languages": [
                {"language": lang, "count": count} for lang, count in top_languages
            ],
            "inferred_skills": list(set(project_types)),
            "suggested_roles": [
                (
                    "Full-Stack Developer"
                    if (
                        "Frontend Development" in project_types
                        and "API Development" in project_types
                    )
                    else ""
                ),
                "Backend Developer" if "API Development" in project_types else "",
                "Frontend Developer" if "Frontend Development" in project_types else "",
                "ML Engineer" if "Machine Learning" in project_types else "",
                (
                    "Python Developer"
                    if any(lang[0] == "Python" for lang in top_languages)
                    else ""
                ),
            ],
        }

        # Filter out empty strings
        analysis["suggested_roles"] = [
            role for role in analysis["suggested_roles"] if role
        ]

        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing GitHub profile: {str(e)}"
        )


@app.get("/api/search-jobs")
async def search_job_postings(keyword: str, location: str = "", limit: int = 5):
    """Search for job postings"""
    try:
        # Using JSearch API (requires RAPIDAPI_KEY environment variable)
        url = "https://jsearch.p.rapidapi.com/search"
        api_key = os.getenv("RAPIDAPI_KEY")

        if not api_key:
            return {
                "error": "RAPIDAPI_KEY environment variable not set. Job search unavailable."
            }

        querystring = {
            "query": f"{keyword} in {location}" if location else keyword,
            "page": "1",
            "num_pages": "1",
        }

        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=querystring)
            data = response.json()

        if "data" not in data:
            return {
                "jobs": [],
                "message": "No job postings found or API limit reached.",
            }

        jobs = data["data"][:limit]

        results = []
        for job in jobs:
            results.append(
                {
                    "title": job.get("job_title", "Unknown"),
                    "company": job.get("employer_name", "Unknown"),
                    "location": job.get("job_city", "Remote"),
                    "description": (job.get("job_description", "")[:200] + "..."),
                    "url": job.get("job_apply_link", ""),
                }
            )

        return {"jobs": results}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error searching job postings: {str(e)}"
        )


@app.post("/api/save-file")
async def save_file_to_workspace(request: SaveFileRequest):
    """Save content to a file in the workspace"""
    try:
        workspace_dir = Path(__file__).parent.parent
        file_path = workspace_dir / request.directory / request.filename

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)

        return {"message": f"File saved successfully: {file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@app.get("/api/read-file")
async def read_file_from_workspace(filename: str, directory: str = "analyses"):
    """Read content from a file in the workspace"""
    try:
        workspace_dir = Path(__file__).parent.parent
        file_path = workspace_dir / directory / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {"content": content, "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


# Resume Optimization Platform Features


@app.post("/api/add-user-experience")
async def add_user_experience(request: AddUserExperienceRequest):
    """Add user resume/experience data to the knowledge base"""
    try:
        from app.rag import add_document

        for experience in request.experiences:
            content = f"""
            User Experience: {experience.role} at {experience.company}
            Duration: {experience.duration}
            Achievements: {', '.join(experience.achievements)}
            Skills Used: {', '.join(experience.skills)}
            """

            add_document(
                content,
                {
                    "type": "user_experience",
                    "user_id": request.user_id,
                    "role": experience.role,
                    "company": experience.company,
                    "skills": experience.skills,
                },
            )

        return {
            "message": (
                f"Added {len(request.experiences)} experience(s) to knowledge base "
                f"for user {request.user_id}"
            )
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding user experience: {str(e)}"
        )


@app.post("/api/optimize-resume")
async def optimize_resume(request: ResumeOptimizationRequest):
    """Generate resume optimization suggestions based on job requirements and user experience"""
    try:
        logger.info("Starting optimize_resume endpoint")
        from app.rag import retrieve_resources

        # from app.agent import agent  # Already imported at top

        logger.info("Retrieving user experience")
        # Retrieve user's relevant experience
        user_experience_query = f"experience {request.user_id} {request.target_role}"
        relevant_experiences = retrieve_resources(user_experience_query, k=5)
        logger.info(f"Retrieved {len(relevant_experiences)} experiences")

        # Create optimization prompt
        optimization_state = {
            "job_description": request.job_description,
            "target_role": request.target_role,
            "target_company": request.target_company,
            "user_experiences": relevant_experiences,
            "task": "resume_optimization",
        }
        logger.info("Created optimization state")

        # Use the agent to generate optimization suggestions
        logger.info("Invoking agent")
        result = agent.invoke(optimization_state)
        logger.info("Agent completed successfully")

        return {
            "optimized_resume_sections": result.get("resume_sections", []),
            "keyword_suggestions": result.get("keywords", []),
            "tailoring_recommendations": result.get("recommendations", []),
            "experience_matches": relevant_experiences,
        }
    except Exception as e:
        logger.error(f"Error in optimize_resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error optimizing resume: {str(e)}"
        )


@app.post("/api/upload-resume")
async def upload_resume(user_id: str = Form(...), file: UploadFile = File(...)):
    """Upload and parse a resume PDF file"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Read file content
        file_content = await file.read()

        # Parse the resume
        from app.resume_parser import parse_resume

        parsed_data = parse_resume(file_content, file.filename)

        # Store parsed data in vector store for future retrieval
        from app.rag import add_documents_to_store
        from langchain_core.documents import Document

        # Create documents from parsed sections
        documents = []
        for section_name, section_content in parsed_data["sections"].items():
            if section_content.strip():
                doc = Document(
                    page_content=(f"Resume section: {section_name}\n{section_content}"),
                    metadata={
                        "user_id": user_id,
                        "filename": file.filename,
                        "section": section_name,
                        "type": "resume",
                    },
                )
                documents.append(doc)

        # Add experiences as separate documents
        for exp in parsed_data["extracted_experiences"]:
            exp_content = f"Experience: {exp.role} at {exp.company} ({exp.duration})"
            if exp.achievements:
                exp_content += f"\nAchievements: {'; '.join(exp.achievements)}"
            if exp.skills:
                exp_content += f"\nSkills: {'; '.join(exp.skills)}"

            doc = Document(
                page_content=exp_content,
                metadata={
                    "user_id": user_id,
                    "filename": file.filename,
                    "type": "experience",
                    "role": exp.role,
                    "company": exp.company,
                },
            )
            documents.append(doc)

        # Add to vector store
        add_documents_to_store(documents)

        # Return parsed resume data
        return {
            "message": "Resume uploaded and parsed successfully",
            "parsed_resume": {
                "user_id": user_id,
                "filename": file.filename,
                "sections": parsed_data["sections"],
                "extracted_experiences": [
                    exp.dict() for exp in parsed_data["extracted_experiences"]
                ],
                "full_text_preview": (
                    parsed_data["full_text"][:500] + "..."
                    if len(parsed_data["full_text"]) > 500
                    else parsed_data["full_text"]
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")


@app.post("/api/advanced-rag-query")
async def advanced_rag_query(request: dict):
    """Query using advanced RAG pipeline with evaluation"""
    try:
        question = request.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")

        from app.rag import query_advanced_rag, evaluate_rag_performance

        # Get advanced RAG response
        answer = query_advanced_rag(question)

        # Evaluate performance
        evaluation = evaluate_rag_performance(question, answer)

        return {
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
            "pipeline_used": "Advanced RAG with query expansion and re-ranking",
        }

    except Exception as e:
        logger.error(f"Error in advanced RAG query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error in advanced RAG query: {str(e)}"
        )


@app.get("/api/rag-performance-metrics")
async def get_rag_performance_metrics():
    """Get RAG performance metrics and pipeline information"""
    try:
        from app.advanced_rag import test_advanced_rag_pipeline

        # Run a test to demonstrate the pipeline
        test_results = test_advanced_rag_pipeline()

        return {
            "pipeline_status": "active",
            "components": [
                "QueryExpansionRetriever",
                "RerankingRetriever",
                "LCEL-based RAG Chain",
                "RAG Evaluator",
            ],
            "capabilities": [
                "Multi-step retrieval with query expansion",
                "Cross-encoder re-ranking",
                "Performance evaluation metrics",
                "Conversational memory support",
            ],
            "test_results": {
                "expanded_results_count": len(test_results.get("expanded_results", [])),
                "reranked_results_count": len(test_results.get("reranked_results", [])),
                "answer_preview": (test_results.get("rag_answer", "")[:200] + "..."),
            },
        }

    except Exception as e:
        logger.error(f"Error getting RAG metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error getting RAG metrics: {str(e)}"
        )
