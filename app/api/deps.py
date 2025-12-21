"""
API Dependencies.

Provides dependency injection for API routes.
All services now use MongoDB instead of PostgreSQL.
"""
from app.services import SessionService, ChatService, PlanService


# Create service instances (MongoDB-based, no DB session needed)
_session_service = SessionService()


def get_session_service() -> SessionService:
    """Get SessionService instance (MongoDB-based)."""
    return _session_service


def get_chat_service() -> ChatService:
    """Get ChatService instance."""
    return ChatService(_session_service)


def get_plan_service() -> PlanService:
    """Get PlanService instance."""
    return PlanService(_session_service)
