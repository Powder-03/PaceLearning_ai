"""
API Router Configuration.

Aggregates all route modules into a single router.
"""
from fastapi import APIRouter

from app.api.routes import sessions_router, chat_router, health_router, test_router, auth_router
from app.api.routes.pdf import router as pdf_router


def create_api_router() -> APIRouter:
    """
    Create and configure the main API router.
    
    Includes all route modules with proper prefixes.
    
    Returns:
        Configured APIRouter instance
    """
    api_router = APIRouter(prefix="/api/v1")
    
    # Include route modules
    api_router.include_router(auth_router)
    api_router.include_router(sessions_router)
    api_router.include_router(chat_router)
    api_router.include_router(pdf_router)
    
    return api_router


def get_all_routers():
    """
    Get all routers for the application.
    
    Returns:
        Tuple of (api_router, health_router, test_router)
    """
    api_router = create_api_router()
    return api_router, health_router, test_router
