import hashlib
import logging
from typing import Dict
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.models import (
    JobAnalysisRequest,
    JobAnalysisResponse,
    SaveJobAnalysisRequest,
    UpdateLearningProgressRequest,
    SaveFileRequest,
    AddUserExperienceRequest,
    ResumeOptimizationRequest,
    EnhancedJobAnalysisRequest,
    SpecificJobAnalysisRequest,
    EnhancedJobAnalysisResponse,
)
import sqlite3
import json
import os
from pathlib import Path
import httpx
from app.agent import agent
from app.rag import retrieve_resources

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Job Research & Summary Agent")

# CORS configuration - supports both local dev and production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Configure via ALLOWED_ORIGINS env variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration (per-client IP)
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Database setup
DB_PATH = Path(__file__).parent.parent / "mcp-server" / "job_research.db"
CV_STORAGE_PATH = Path(__file__).parent.parent / "cv_storage"

# Create CV storage directory if it doesn't exist
CV_STORAGE_PATH.mkdir(exist_ok=True)


def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create job_analyses table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            skills_required TEXT NOT NULL,
            skill_gaps TEXT NOT NULL,
            learning_plan TEXT NOT NULL,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, job_title, company)
        )
        """
    )

    # Create learning_progress table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            skill TEXT NOT NULL,
            progress_percentage INTEGER DEFAULT 0,
            completed_modules TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, skill)
        )
        """
    )

    # Create parsed_resumes table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS parsed_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            full_text TEXT NOT NULL,
            sections TEXT,
            extracted_experiences TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT
        )
        """
    )

    # Add file_path column if it doesn't exist (migration for existing databases)
    cursor.execute("PRAGMA table_info(parsed_resumes)")
    columns = [column[1] for column in cursor.fetchall()]
    if "file_path" not in columns:
        cursor.execute("ALTER TABLE parsed_resumes ADD COLUMN file_path TEXT")
        logger.info("Added file_path column to parsed_resumes table")

    # Create cv_metadata table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cv_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER,
            file_hash TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            notes TEXT,
            version INTEGER DEFAULT 1,
            FOREIGN KEY (resume_id) REFERENCES parsed_resumes(id),
            UNIQUE(user_id, file_hash)
        )
        """
    )

    conn.commit()
    conn.close()


def compute_file_hash(file_content: bytes) -> str:
    """Compute SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()


def save_cv_file(user_id: str, file_content: bytes, original_filename: str) -> str:
    """Save CV file to local storage and return the path"""
    # Create user-specific directory
    user_cv_dir = CV_STORAGE_PATH / user_id
    user_cv_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{original_filename}"
    file_path = user_cv_dir / safe_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)

    return str(file_path)


def _suggest_roles_from_skills(skills: Dict[str, list]) -> list:
    """Suggest job roles based on extracted skills"""
    technical_skills = skills.get("technical_skills", [])
    tools = skills.get("tools", [])

    all_skills = set([s.lower() for s in technical_skills + tools])

    suggested_roles = []

    # Role mapping based on common skill combinations
    role_mappings = {
        "Python Developer": ["python", "django", "flask", "fastapi"],
        "Full Stack Developer": ["javascript", "react", "node", "python", "typescript"],
        "Frontend Developer": [
            "react",
            "vue",
            "angular",
            "javascript",
            "typescript",
            "css",
        ],
        "Backend Developer": ["python", "java", "node", "api", "database"],
        "DevOps Engineer": [
            "docker",
            "kubernetes",
            "aws",
            "jenkins",
            "ci/cd",
            "terraform",
        ],
        "Data Engineer": ["python", "sql", "spark", "airflow", "kafka"],
        "Machine Learning Engineer": [
            "python",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "ml",
        ],
        "Data Scientist": [
            "python",
            "pandas",
            "numpy",
            "machine learning",
            "statistics",
        ],
        "Cloud Engineer": ["aws", "azure", "gcp", "cloud", "terraform"],
        "Mobile Developer": [
            "react native",
            "flutter",
            "ios",
            "android",
            "swift",
            "kotlin",
        ],
        "QA Engineer": ["selenium", "pytest", "testing", "automation"],
        "Software Engineer": ["programming", "software", "development"],
    }

    # Score each role
    role_scores = {}
    for role, required_skills in role_mappings.items():
        matches = sum(1 for skill in required_skills if skill in all_skills)
        if matches > 0:
            role_scores[role] = matches

    # Sort by score and return top 5
    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    suggested_roles = [role for role, score in sorted_roles[:5]]

    # Always include "Software Engineer" if we have technical skills but no specific matches
    if not suggested_roles and technical_skills:
        suggested_roles = ["Software Engineer", "Developer"]

    return suggested_roles


# Initialize database on startup
init_db()


@app.get("/")
async def root():
    return {"message": "AI Job Research & Summary Agent API"}


@app.post("/analyze", response_model=JobAnalysisResponse)
@limiter.limit("20/hour")
async def analyze_job(request: Request, payload: JobAnalysisRequest):
    """Analyze a job using the agentic reasoning loop"""
    try:
        # Initialize agent state with required fields
        initial_state = {
            "job_description": payload.job_description,
            "current_skills": payload.current_skills,
            "job_title": getattr(payload, "job_title", ""),
            "location": getattr(payload, "location", "Remote"),
            "skills_required": [],
            "skill_gaps": [],
            "rag_results": None,
            "skill_validation_results": None,
            "market_research_results": None,
            "gap_analysis_results": None,
            "learning_plan_results": None,
            "tool_call_count": 0,
            "max_tool_calls": 5,
            "executed_tools": [],
            "agent_reasoning": [],
            "learning_plan": "",
            "analysis_quality_score": 0.0,
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
    except Exception as e:
        logger.error(f"Error in analyze_job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# MCP Server functionality integrated into FastAPI


@app.post("/api/save-job-analysis")
@limiter.limit("40/hour")
async def save_job_analysis(request: Request, payload: SaveJobAnalysisRequest):
    """Save a job analysis to the database"""
    conn = None
    try:
        conn = get_db_connection()
        # Set timeout to handle database locks
        conn.execute("PRAGMA busy_timeout = 5000")
        cursor = conn.cursor()

        # First, check if analysis already exists
        cursor.execute(
            """
            SELECT id FROM job_analyses
            WHERE user_id = ? AND job_title = ? AND company = ?
            """,
            (payload.user_id, payload.job_title, payload.company),
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing analysis instead of inserting
            cursor.execute(
                """
                UPDATE job_analyses
                SET skills_required = ?, skill_gaps = ?, learning_plan = ?,
                    analysis_date = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    json.dumps(payload.skills_required),
                    json.dumps(payload.skill_gaps),
                    payload.learning_plan,
                    existing[0],
                ),
            )
            analysis_id = existing[0]
            message = f"Job analysis updated successfully (ID: {analysis_id})"
        else:
            # Insert new analysis
            cursor.execute(
                """
                INSERT INTO job_analyses
                (user_id, job_title, company, skills_required, skill_gaps, learning_plan)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.user_id,
                    payload.job_title,
                    payload.company,
                    json.dumps(payload.skills_required),
                    json.dumps(payload.skill_gaps),
                    payload.learning_plan,
                ),
            )
            analysis_id = cursor.lastrowid
            message = f"Job analysis saved successfully (ID: {analysis_id})"

        conn.commit()
        return {"message": message, "id": analysis_id, "updated": existing is not None}
    except sqlite3.IntegrityError:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=409,
            detail="This job analysis already exists. Please use a different job title or company name.",
        )
    except sqlite3.OperationalError as e:
        if conn:
            conn.rollback()
        if "locked" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="Database is temporarily busy. Please try again in a moment.",
            )
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error saving job analysis: {str(e)}"
        )
    finally:
        if conn:
            conn.close()


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
        languages: Dict[str, int] = {}
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
@limiter.limit("60/hour")
async def search_job_postings(
    request: Request, keyword: str, location: str = "", limit: int = 5
):
    """Search for job postings"""
    try:
        # Using JSearch API (requires RAPIDAPI_KEY environment variable)
        url = "https://jsearch.p.rapidapi.com/search"
        api_key = os.getenv("RAPIDAPI_KEY")

        if not api_key:
            logger.warning("RAPIDAPI_KEY not set in environment")
            return {
                "error": True,
                "message": "Job search is currently unavailable",
                "reason": "Missing API Key Configuration",
                "details": "The RapidAPI key for job search is not configured on the server. Please contact the administrator to set up the RAPIDAPI_KEY environment variable.",
                "jobs": [],
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

        logger.info(
            f"Searching jobs: keyword={keyword}, location={location}, limit={limit}"
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers, params=querystring)

            if response.status_code == 401 or response.status_code == 403:
                logger.error(
                    f"JSearch API authentication failed: status={response.status_code}"
                )
                return {
                    "error": True,
                    "message": "Job search is currently unavailable",
                    "reason": "Invalid API Key",
                    "details": "The RapidAPI key is invalid, expired, or has insufficient permissions. Please verify the key is correct and has access to the JSearch API.",
                    "jobs": [],
                }

            if response.status_code == 429:
                logger.error(
                    f"JSearch API rate limit exceeded: status={response.status_code}"
                )
                return {
                    "error": True,
                    "message": "Job search temporarily unavailable",
                    "reason": "Rate Limit Exceeded",
                    "details": "The job search service has reached its request limit. Please try again in a few moments.",
                    "jobs": [],
                }

            if response.status_code != 200:
                logger.error(
                    f"JSearch API error: status={response.status_code}, "
                    f"body={response.text}"
                )
                return {
                    "error": True,
                    "message": "Job search service error",
                    "reason": f"API Error (Status {response.status_code})",
                    "details": "An error occurred while searching for jobs. Please try again later.",
                    "jobs": [],
                }

            data = response.json()

        if "data" not in data or not data["data"]:
            logger.info("No jobs found matching the search criteria")
            return {
                "error": False,
                "message": "No jobs found",
                "reason": "No Results",
                "details": f"No job postings found matching '{keyword}' {f'in {location}' if location else ''}. Try different keywords or check the spelling.",
                "jobs": [],
            }

        jobs = data["data"][:limit]
        logger.info(f"Found {len(jobs)} jobs from JSearch API")

        results = []
        for job in jobs:
            results.append(
                {
                    "title": job.get("job_title", "Unknown"),
                    "company": job.get("employer_name", "Unknown"),
                    "location": job.get("job_city", "Remote"),
                    "description": job.get("job_description", ""),
                    "url": job.get("job_apply_link", ""),
                }
            )

        return {"error": False, "message": "Success", "jobs": results}

    except httpx.TimeoutException:
        logger.error("JSearch API request timed out")
        return {
            "error": True,
            "message": "Job search request timed out",
            "reason": "Connection Timeout",
            "details": "The job search service took too long to respond. Please try again.",
            "jobs": [],
        }
    except Exception as e:
        logger.error(f"Error searching job postings: {str(e)}", exc_info=True)
        return {
            "error": True,
            "message": "Job search service error",
            "reason": "Unexpected Error",
            "details": "An unexpected error occurred while searching for jobs. Please try again later.",
            "jobs": [],
        }


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
@limiter.limit("20/hour")
async def optimize_resume(request: Request, payload: ResumeOptimizationRequest):
    """Generate resume optimization suggestions based on job requirements and user experience"""
    try:
        logger.info("Starting optimize_resume endpoint")
        logger.info("Retrieving user experience")
        # Retrieve user's relevant experience
        user_experience_query = f"experience {payload.user_id} {payload.target_role}"
        relevant_experiences = retrieve_resources(user_experience_query, k=5)
        logger.info(f"Retrieved {len(relevant_experiences)} experiences")

        # Create optimization prompt
        optimization_state = {
            "job_description": payload.job_description,
            "target_role": payload.target_role,
            "target_company": payload.target_company,
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
@limiter.limit("20/hour")
async def upload_resume(
    request: Request, user_id: str = Form(...), file: UploadFile = File(...)
):
    """Upload and parse a resume PDF file"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Read file content
        file_content = await file.read()
        file_hash = compute_file_hash(file_content)

        # Check for duplicate CV
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT cm.id, cm.resume_id, cm.original_filename, cm.upload_date, pr.full_text, pr.sections
            FROM cv_metadata cm
            JOIN parsed_resumes pr ON cm.resume_id = pr.id
            WHERE cm.user_id = ? AND cm.file_hash = ?
            ORDER BY cm.upload_date DESC
            LIMIT 1
            """,
            (user_id, file_hash),
        )

        existing_cv = cursor.fetchone()

        if existing_cv:
            # Return existing resume data with suggestion roles
            from app.skill_extractor import extract_skills_from_resume

            resume_text = existing_cv[4]
            sections = json.loads(existing_cv[5])

            # Extract skills to suggest roles
            skills = extract_skills_from_resume(resume_text, sections)
            suggested_roles = _suggest_roles_from_skills(skills)

            conn.close()

            return {
                "message": "This resume has already been uploaded",
                "is_duplicate": True,
                "resume_id": existing_cv[1],
                "original_upload_date": existing_cv[3],
                "file_path": None,
                "file_hash": file_hash,
                "file_size": len(file_content),
                "parsed_resume": {
                    "user_id": user_id,
                    "filename": existing_cv[2],
                    "sections": sections,
                    "extracted_experiences": [],
                    "full_text_preview": (
                        resume_text[:500] + "..."
                        if len(resume_text) > 500
                        else resume_text
                    ),
                },
                "suggested_roles": suggested_roles,
            }

        # Parse the resume (new upload)
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

        # Save CV file locally
        file_path = save_cv_file(user_id, file_content, file.filename)
        file_size = len(file_content)
        file_hash = compute_file_hash(file_content)

        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.info(f"Saving resume for user: {user_id}, filename: {file.filename}")
        logger.info(f"Full text length: {len(parsed_data['full_text'])}")
        logger.info(f"Sections: {list(parsed_data['sections'].keys())}")
        logger.info(f"Experiences: {len(parsed_data['extracted_experiences'])}")

        # Insert into parsed_resumes
        cursor.execute(
            """
            INSERT INTO parsed_resumes
            (user_id, filename, full_text, sections, extracted_experiences, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                file.filename,
                parsed_data["full_text"],
                json.dumps(parsed_data["sections"]),
                json.dumps(
                    [exp.dict() for exp in parsed_data["extracted_experiences"]]
                ),
                file_path,
            ),
        )

        resume_id = cursor.lastrowid
        logger.info(f"Resume inserted with ID: {resume_id}")

        # Insert into cv_metadata
        cursor.execute(
            """
            INSERT INTO cv_metadata
            (resume_id, user_id, file_path, original_filename, file_size, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (resume_id, user_id, file_path, file.filename, file_size, file_hash),
        )

        conn.commit()
        conn.close()

        # Extract skills and suggest roles
        from app.skill_extractor import extract_skills_from_resume

        skills = extract_skills_from_resume(
            parsed_data["full_text"], parsed_data["sections"]
        )
        suggested_roles = _suggest_roles_from_skills(skills)

        # Return parsed resume data
        return {
            "message": "Resume uploaded and parsed successfully",
            "is_duplicate": False,
            "resume_id": resume_id,
            "file_path": file_path,
            "file_hash": file_hash,
            "file_size": file_size,
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
            "suggested_roles": suggested_roles,
        }

    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")


@app.get("/api/cv-metadata/{user_id}")
async def get_cv_metadata(user_id: str):
    """Retrieve CV metadata for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, resume_id, original_filename, file_size, file_hash,
                   upload_date, is_active, notes, version
            FROM cv_metadata
            WHERE user_id = ?
            ORDER BY upload_date DESC
            """,
            (user_id,),
        )

        columns = [description[0] for description in cursor.description]
        cvs = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()

        return {"user_id": user_id, "cv_count": len(cvs), "cvs": cvs}
    except Exception as e:
        logger.error(f"Error retrieving CV metadata: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving CV metadata: {str(e)}"
        )


@app.get("/api/parsed-resumes/{user_id}")
async def get_parsed_resumes(user_id: str):
    """Get all parsed resumes for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, user_id, filename, upload_date, file_path
            FROM parsed_resumes
            WHERE user_id = ?
            ORDER BY upload_date DESC
            """,
            (user_id,),
        )

        columns = [description[0] for description in cursor.description]
        resumes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"Found {len(resumes)} parsed resumes for user {user_id}")
        return {"user_id": user_id, "count": len(resumes), "resumes": resumes}
    except Exception as e:
        logger.error(f"Error retrieving parsed resumes: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving parsed resumes: {str(e)}"
        )


@app.put("/api/cv-metadata/{metadata_id}")
async def update_cv_metadata(metadata_id: int, notes: str = "", is_active: int = 1):
    """Update CV metadata (notes, active status)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE cv_metadata
            SET notes = ?, is_active = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (notes, is_active, metadata_id),
        )

        conn.commit()
        conn.close()

        return {
            "message": "CV metadata updated successfully",
            "metadata_id": metadata_id,
        }
    except Exception as e:
        logger.error(f"Error updating CV metadata: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating CV metadata: {str(e)}"
        )


@app.get("/api/resume/{resume_id}")
async def get_resume(resume_id: int):
    """Retrieve parsed resume data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, user_id, filename, full_text, sections,
                   extracted_experiences, upload_date, file_path
            FROM parsed_resumes
            WHERE id = ?
            """,
            (resume_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Resume not found")

        columns = [description[0] for description in cursor.description]
        resume_data = dict(zip(columns, row))

        # Parse JSON fields
        resume_data["sections"] = json.loads(resume_data["sections"])
        resume_data["extracted_experiences"] = json.loads(
            resume_data["extracted_experiences"]
        )

        return resume_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving resume: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving resume: {str(e)}"
        )


@app.post("/api/advanced-rag-query")
@limiter.limit("30/hour")
async def advanced_rag_query(request: Request, payload: dict):
    """Query using advanced RAG pipeline with evaluation"""
    try:
        question = payload.get("question", "")
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


@app.post("/api/enhanced-job-analysis", response_model=EnhancedJobAnalysisResponse)
@limiter.limit("20/hour")
async def enhanced_job_analysis(request: Request, payload: EnhancedJobAnalysisRequest):
    """
    Enhanced job analysis: Extract skills from resume, search jobs, analyze matches

    This endpoint:
    1. Retrieves the user's resume from database
    2. Extracts skills from the resume
    3. Searches JustJoin.it for matching jobs
    4. Analyzes each job against user's skills
    5. Returns ranked job matches with gap analysis and learning plans
    """
    try:
        from app.enhanced_workflow import analyze_job_opportunities_from_resume

        # Get resume from database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT full_text, sections
            FROM parsed_resumes
            WHERE id = ? AND user_id = ?
            """,
            (payload.resume_id, payload.user_id),
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Resume not found for user {payload.user_id} with ID {payload.resume_id}",
            )

        resume_text = result[0]
        sections = json.loads(result[1])

        # Run enhanced analysis
        logger.info(f"Starting enhanced job analysis for user {payload.user_id}")
        analysis_result = await analyze_job_opportunities_from_resume(
            resume_text=resume_text,
            resume_sections=sections,
            location=payload.location,
            experience_level=payload.experience_level,
            num_jobs=payload.num_jobs,
            specific_role=payload.specific_role,
        )

        logger.info(
            f"Analysis complete. Found {analysis_result['jobs_analyzed']} job matches"
        )

        return EnhancedJobAnalysisResponse(**analysis_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhanced job analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error in enhanced job analysis: {str(e)}"
        )


@app.post("/api/analyze-specific-job")
@limiter.limit("20/hour")
async def analyze_specific_job(request: Request, payload: SpecificJobAnalysisRequest):
    """
    Analyze a specific job description against user's resume

    This endpoint:
    1. Retrieves the user's resume
    2. Extracts skills from resume
    3. Analyzes the provided job description
    4. Compares skills and identifies gaps
    5. Generates learning plan
    """
    try:
        from app.enhanced_workflow import analyze_specific_job_with_resume

        # Get resume from database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT full_text, sections
            FROM parsed_resumes
            WHERE id = ? AND user_id = ?
            """,
            (payload.resume_id, payload.user_id),
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Resume not found for user {payload.user_id} with ID {payload.resume_id}",
            )

        resume_text = result[0]
        sections = json.loads(result[1])

        # Analyze specific job
        logger.info(f"Analyzing specific job for user {payload.user_id}")
        analysis_result = await analyze_specific_job_with_resume(
            resume_text=resume_text,
            resume_sections=sections,
            job_description=payload.job_description,
            job_title=payload.job_title,
            company=payload.company,
        )

        logger.info("Specific job analysis complete")

        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing specific job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error analyzing specific job: {str(e)}"
        )


@app.get("/api/extract-skills/{resume_id}")
async def extract_skills_from_resume_endpoint(resume_id: int, user_id: str):
    """
    Extract structured skills from a resume

    Returns categorized skills: technical_skills, soft_skills, tools, languages
    """
    try:
        from app.skill_extractor import extract_skills_from_resume

        # Get resume from database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT full_text, sections
            FROM parsed_resumes
            WHERE id = ? AND user_id = ?
            """,
            (resume_id, user_id),
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Resume not found for user {user_id} with ID {resume_id}",
            )

        resume_text = result[0]
        sections = json.loads(result[1])

        # Extract skills
        skills = extract_skills_from_resume(resume_text, sections)

        return {"resume_id": resume_id, "user_id": user_id, "skills": skills}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting skills: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error extracting skills: {str(e)}"
        )
