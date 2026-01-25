"""
Generation Mode Microservice - Main Application.

AI-powered curriculum generation and interactive tutoring service.
Uses MongoDB for all data storage (sessions, chat history, etc.).
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    
    # Add production frontend URL
    if settings.FRONTEND_URL:
        allowed_origins.append(settings.FRONTEND_URL)
        if settings.FRONTEND_URL.endswith("/"):
            allowed_origins.append(settings.FRONTEND_URL.rstrip("/"))
        else:
            allowed_origins.append(settings.FRONTEND_URL + "/")
    
    log.info(f"CORS allowed origins: {allowed_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    api_router, health_router, test_router = get_all_routers()
    app.include_router(api_router)
    app.include_router(health_router)
    app.include_router(test_router)
    
    # Static files directory (for production frontend)
    static_dir = Path(__file__).parent.parent / "static"
    
    # Serve static files if the directory exists (production build)
    if static_dir.exists():
        log.info(f"Serving static files from: {static_dir}")
        
        # Mount static assets (JS, CSS, images)
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
        
        # Serve index.html for SPA routes (must be after API routes)
        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(request: Request, full_path: str):
            """Serve the SPA for all non-API routes."""
            # Skip API routes
            if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
                return None
            
            # Check if file exists in static dir
            file_path = static_dir / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            
            # Return index.html for SPA routing
            return FileResponse(static_dir / "index.html")
    else:
        log.info("No static directory found - running in API-only mode")
        
        # Root endpoint (only when no frontend)
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
