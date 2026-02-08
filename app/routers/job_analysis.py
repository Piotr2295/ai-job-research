"""
Job analysis router - handles job analysis requests.
"""

import logging
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api_helpers import with_error_logging
from app.config import settings
from app.logging_config import PerformanceLogger
from app.models import JobAnalysisRequest, JobAnalysisResponse
from app.services.job_analysis_service import JobAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["job-analysis"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/analyze", response_model=JobAnalysisResponse)
@limiter.limit(f"{settings.rate_limit_analyze}/hour")
@with_error_logging
async def analyze_job(request: Request, payload: JobAnalysisRequest):
    """Analyze a job using the agentic reasoning loop"""
    with PerformanceLogger(logger, "Job analysis"):
        service = JobAnalysisService()
        return await service.analyze_job(payload)
