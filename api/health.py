"""
Health check endpoint for service monitoring.
"""
import time
from fastapi import APIRouter
from pydantic import BaseModel

from core.config import settings

router = APIRouter()

# Track service start time
START_TIME = time.time()


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    uptime: float
    version: str


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    Returns service status, uptime, and version.
    No authentication required.
    
    Returns:
        HealthResponse with status, uptime in seconds, and version
    """
    uptime = time.time() - START_TIME
    
    return HealthResponse(
        status="ok",
        uptime=round(uptime, 2),
        version=settings.APP_VERSION
    )

