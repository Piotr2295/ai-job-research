"""
Main FastAPI application - refactored for professional structure.

This file now serves as the application entry point with minimal logic.
All routes are organized in the routers/ directory.
All business logic is in the services/ directory.
"""

import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.database import DatabaseManager
from app.error_handlers import register_error_handlers
from app.logging_config import setup_logging

# Import all routers
from app.routers import job_analysis

# Load environment variables
load_dotenv()

# Setup structured logging
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    json_logs=settings.json_logs,
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered job analysis and career development platform",
    version=settings.app_version,
)

# Register centralized error handlers
register_error_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration (per-client IP)
limiter = Limiter(
    key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_hour}/hour"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Initialize database manager with proper error handling
db_manager = DatabaseManager(settings.db_path, timeout=settings.db_timeout)


@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources on startup"""
    from app.services.database_service import DatabaseService

    db_service = DatabaseService(db_manager)
    db_service.init_db()
    logger.info(f"{settings.app_name} v{settings.app_version} started successfully")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": f"{settings.app_name} API",
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include routers
app.include_router(job_analysis.router)

# NOTE: Add other routers as they are created
# app.include_router(resume.router)
# app.include_router(github.router)
# app.include_router(learning.router)
# app.include_router(rag.router)
# app.include_router(jobs.router)
