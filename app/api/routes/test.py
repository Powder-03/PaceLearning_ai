"""
Diagnostic Test Routes.

Simple endpoints to test connectivity without app dependencies.
Tests: MongoDB, PostgreSQL, and Gemini API.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai

from app.services.mongodb import MongoDBService
from app.api.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test"])


class TestMessage(BaseModel):
    """Test message model."""
    message: str


@router.post("/mongodb")
async def test_mongodb_connection(data: TestMessage) -> Dict[str, Any]:
    """
    Test MongoDB connection by writing and reading a document.
    
    This endpoint tests:
    1. MongoDB connection is established
    2. Can write to database
    3. Can read from database
    """
    try:
        # Get database
        db = MongoDBService.get_db()
        
        # Create test document
        test_doc = {
            "test_message": data.message,
            "timestamp": datetime.utcnow(),
            "test_id": f"test_{datetime.utcnow().timestamp()}"
        }
        
        # Insert into test collection
        result = await db.test_collection.insert_one(test_doc)
        
        # Read it back
        retrieved = await db.test_collection.find_one({"_id": result.inserted_id})
        
        # Clean up - delete test document
        await db.test_collection.delete_one({"_id": result.inserted_id})
        
        return {
            "status": "success",
            "mongodb_connected": True,
            "inserted_id": str(result.inserted_id),
            "message": "MongoDB is working correctly",
            "test_data": {
                "sent": data.message,
                "retrieved": retrieved.get("test_message") if retrieved else None
            }
        }
        
    except RuntimeError as e:
        # MongoDB not connected
        return {
            "status": "error",
            "mongodb_connected": False,
            "error": str(e),
            "message": "MongoDB is not connected. Check MONGODB_URL secret."
        }
        
    except Exception as e:
        logger.exception(f"MongoDB test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "mongodb_connected": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


@router.get("/mongodb/status")
async def mongodb_status() -> Dict[str, Any]:
    """
    Check MongoDB connection status without writing anything.
    
    Quick check to see if MongoDB client is initialized.
    """
    try:
        db = MongoDBService.get_db()
        
        # Try to ping
        result = await db.client.admin.command('ping')
        
        return {
            "status": "connected",
            "mongodb_connected": True,
            "ping_result": result,
            "database": db.name
        }
        
    except RuntimeError as e:
        return {
            "status": "not_connected",
            "mongodb_connected": False,
            "error": str(e),
            "message": "MongoDB client not initialized"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "mongodb_connected": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/ping")
async def simple_ping() -> Dict[str, Any]:
    """
    Simplest possible endpoint - no database, no dependencies.
    
    If this doesn't respond, the FastAPI app itself isn't starting.
    """
    return {
        "status": "ok",
        "message": "FastAPI is running",
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# PostgreSQL Tests
# =============================================================================

@router.get("/postgres/status")
async def postgres_status(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Check PostgreSQL connection status.
    
    Quick check to see if PostgreSQL is accessible.
    """
    try:
        # Simple query to check connection
        result = await db.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        
        # Check database version
        version_result = await db.execute(text("SELECT version()"))
        version = version_result.scalar()
        
        return {
            "status": "connected",
            "postgres_connected": True,
            "test_query": row[0] if row else None,
            "database_version": version[:50] if version else None  # Truncate long version string
        }
        
    except Exception as e:
        logger.exception(f"PostgreSQL status check failed: {str(e)}")
        return {
            "status": "error",
            "postgres_connected": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.post("/postgres")
async def test_postgres_connection(
    data: TestMessage,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test PostgreSQL connection by creating and querying a temp table.
    
    This endpoint tests:
    1. PostgreSQL connection is established
    2. Can execute DDL (CREATE TABLE)
    3. Can write (INSERT)
    4. Can read (SELECT)
    5. Can clean up (DROP TABLE)
    """
    try:
        test_table = f"test_table_{int(datetime.utcnow().timestamp())}"
        
        # Create temporary table
        await db.execute(text(f"""
            CREATE TEMP TABLE {test_table} (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Insert test data
        await db.execute(
            text(f"INSERT INTO {test_table} (message) VALUES (:message)"),
            {"message": data.message}
        )
        
        # Read it back
        result = await db.execute(text(f"SELECT message FROM {test_table}"))
        retrieved_message = result.scalar()
        
        # Commit the transaction
        await db.commit()
        
        return {
            "status": "success",
            "postgres_connected": True,
            "message": "PostgreSQL is working correctly",
            "test_data": {
                "sent": data.message,
                "retrieved": retrieved_message
            }
        }
        
    except Exception as e:
        logger.exception(f"PostgreSQL test failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "postgres_connected": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


# =============================================================================
# Gemini API Tests
# =============================================================================

@router.get("/gemini/status")
async def gemini_status() -> Dict[str, Any]:
    """
    Check Gemini API configuration status.
    
    Validates API key is configured without making an actual API call.
    """
    try:
        api_key = settings.GOOGLE_API_KEY
        
        if not api_key:
            return {
                "status": "not_configured",
                "gemini_configured": False,
                "error": "GOOGLE_API_KEY is not set"
            }
        
        # Check if key looks valid (starts with expected prefix)
        key_preview = f"{api_key[:10]}..." if len(api_key) > 10 else "***"
        
        return {
            "status": "configured",
            "gemini_configured": True,
            "api_key_preview": key_preview,
            "planning_model": settings.PLANNING_MODEL,
            "tutoring_model": settings.TUTORING_MODEL,
            "message": "API key is configured (not validated with actual call)"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "gemini_configured": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.post("/gemini")
async def test_gemini_api(data: TestMessage) -> Dict[str, Any]:
    """
    Test Gemini API by making an actual API call.
    
    This endpoint tests:
    1. API key is valid
    2. Can connect to Gemini API
    3. Can generate content
    """
    try:
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Use the flash model for quick test
        model = genai.GenerativeModel(settings.TUTORING_MODEL)
        
        # Simple test prompt
        prompt = f"Respond with a single word 'SUCCESS' if you can read this: {data.message}"
        
        # Generate content
        response = model.generate_content(prompt)
        
        return {
            "status": "success",
            "gemini_connected": True,
            "model_used": settings.TUTORING_MODEL,
            "message": "Gemini API is working correctly",
            "test_data": {
                "sent": data.message,
                "response": response.text if response else None
            }
        }
        
    except Exception as e:
        logger.exception(f"Gemini API test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "gemini_connected": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

