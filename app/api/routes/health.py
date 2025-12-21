"""
Health Check Routes.

API endpoints for service health monitoring.
Uses MongoDB for database health checks.
"""
import logging
from datetime import datetime

from fastapi import APIRouter

from app.services.mongodb import MongoDBService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns service status and version information.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENV,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Verifies MongoDB connectivity and LLM configuration.
    """
    checks = {
        "mongodb": False,
        "gemini_api": False,
    }
    
    # Check MongoDB connectivity
    try:
        db = MongoDBService.get_db()
        await db.client.admin.command('ping')
        checks["mongodb"] = True
    except Exception as e:
        logger.error(f"MongoDB check failed: {str(e)}")
    
    # Check Gemini API configuration
    checks["gemini_api"] = bool(settings.GOOGLE_API_KEY)
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "models": {
            "planning": settings.PLANNING_MODEL,
            "tutoring": settings.TUTORING_MODEL,
        },
        "streaming_threshold": settings.STREAMING_TOKEN_THRESHOLD,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Simple check to verify the service is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }
