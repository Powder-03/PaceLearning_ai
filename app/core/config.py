from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database (MongoDB only - PostgreSQL removed)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "doclearn"
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    
    # Clerk Authentication
    # Get these from your Clerk Dashboard: https://dashboard.clerk.com
    # CLERK_SECRET_KEY is used for backend API calls (optional)
    CLERK_SECRET_KEY: Optional[str] = None
    # CLERK_JWKS_URL is your Clerk instance's JWKS endpoint for JWT verification
    # Format: https://<your-clerk-frontend-api>.clerk.accounts.dev/.well-known/jwks.json
    CLERK_JWKS_URL: Optional[str] = None
    # CLERK_ISSUER is your Clerk instance URL for JWT issuer validation
    # Format: https://<your-clerk-frontend-api>.clerk.accounts.dev
    CLERK_ISSUER: Optional[str] = None
    
    # LLM API Keys (Gemini only)
    GOOGLE_API_KEY: Optional[str] = None
    
    # LLM Model Configuration (All Gemini)
    # Available models: gemini-2.5-pro, gemini-2.5-flash, gemini-1.5-pro, gemini-1.5-flash
    PLANNING_MODEL: str = "gemini-2.5-pro"  # Powerful for curriculum generation
    TUTORING_MODEL: str = "gemini-2.5-flash"  # Fast for interactive tutoring
    
    # Streaming Configuration
    STREAMING_TOKEN_THRESHOLD: int = 100  # Use streaming if expected tokens > this
    
    # Memory Buffer Configuration
    MEMORY_BUFFER_SIZE: int = 10  # Number of messages before summarization
    
    # Service Configuration
    SERVICE_NAME: str = "generation_service"
    SERVICE_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
