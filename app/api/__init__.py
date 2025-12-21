"""
API Package.

Contains all API-related modules including routes, dependencies, and routers.
All services now use MongoDB (PostgreSQL removed).
"""
from app.api.routers import create_api_router, get_all_routers
from app.api.deps import get_session_service, get_chat_service, get_plan_service

__all__ = [
    "create_api_router",
    "get_all_routers",
    "get_session_service",
    "get_chat_service",
    "get_plan_service",
]
