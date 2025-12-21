"""
Generation Mode Microservice - Main Application.

AI-powered curriculum generation and interactive tutoring service.
Uses MongoDB for all data storage (sessions, chat history, etc.).
"""
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routers import get_all_routers
from app.services.mongodb import MongoDBService

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Manages startup and shutdown tasks.
    """
    import asyncio
    
    # =========================================================================
    # STARTUP
    # =========================================================================
    log.info("=" * 60)
    log.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    log.info("=" * 60)
    
    # Log configuration
    log.info(f"Environment: {settings.ENV}")
    log.info(f"Planning Model: {settings.PLANNING_MODEL} (Gemini Pro)")
    log.info(f"Tutoring Model: {settings.TUTORING_MODEL} (Gemini Flash)")
    log.info(f"Streaming Threshold: {settings.STREAMING_TOKEN_THRESHOLD} tokens")
    log.info(f"Memory Buffer Size: {settings.MEMORY_BUFFER_SIZE} messages")
    log.info(f"Database: MongoDB (PostgreSQL removed)")
    
    # Initialize MongoDB
    try:
        await asyncio.wait_for(MongoDBService.connect(), timeout=10.0)
        log.info(f"MongoDB connected: {settings.MONGODB_DB_NAME}")
    except asyncio.TimeoutError:
        log.error("MongoDB connection timeout (10s) - service may not work properly")
    except Exception as e:
        log.error(f"MongoDB connection failed: {str(e)[:100]}")
    
    # Check LLM configuration (Gemini only)
    if not settings.GOOGLE_API_KEY:
        log.warning("⚠️  GOOGLE_API_KEY not configured - AI features will not work!")
    else:
        log.info("✓ Google API key configured (Gemini)")
    
    log.info("=" * 60)
    log.info("Service is ready to accept requests")
    log.info("=" * 60)
    
    yield
    
    # =========================================================================
    # SHUTDOWN
    # =========================================================================
    log.info("Shutting down...")
    
    # Close MongoDB connection
    await MongoDBService.disconnect()
    log.info("MongoDB connection closed")
    
    log.info("Shutdown complete")


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app() -> FastAPI:
    """
    Application factory.
    
    Creates and configures the FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="Generation Mode Microservice",
        description="""
## AI-Powered Personalized Learning Platform

This service provides:

- **Dynamic Plan Generation**: Creates personalized, multi-day lesson plans
- **Interactive Tutoring**: Socratic-method teaching with understanding checks
- **Progress Tracking**: Stateful learning across multiple sessions

### Key Endpoints

- `POST /api/v1/sessions` - Create a new learning plan
- `POST /api/v1/chat` - Chat with the AI tutor
- `GET /api/v1/sessions/{id}/plan` - Get lesson plan details
        """,
        version=settings.SERVICE_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    api_router, health_router, test_router = get_all_routers()
    app.include_router(api_router)
    app.include_router(health_router)
    app.include_router(test_router)
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with service information."""
        return {
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "status": "running",
            "environment": settings.ENV,
            "docs": "/docs",
        }
    
    return app


# Create the application instance
app = create_app()
