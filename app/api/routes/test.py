"""
Diagnostic Test Routes.

Simple endpoints to test connectivity without app dependencies.
Tests: MongoDB, Gemini API, and Email Service.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import google.generativeai as genai

from app.services.mongodb import MongoDBService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test"])


class TestMessage(BaseModel):
    """Test message model."""
    message: str


class TestEmailRequest(BaseModel):
    """Test email request model."""
    to_email: EmailStr


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


# =============================================================================
# Email Service Tests
# =============================================================================

@router.get("/email/status")
async def email_status() -> Dict[str, Any]:
    """
    Check email service configuration status.
    
    Shows which settings are configured without revealing secrets.
    """
    from app.services.email_service import email_service
    
    logger.info("=== EMAIL STATUS CHECK ===")
    logger.info(f"SMTP_HOST: {settings.SMTP_HOST}")
    logger.info(f"SMTP_PORT: {settings.SMTP_PORT}")
    logger.info(f"SMTP_USER configured: {bool(settings.SMTP_USER)}")
    logger.info(f"SMTP_PASSWORD configured: {bool(settings.SMTP_PASSWORD)}")
    logger.info(f"EMAIL_FROM_ADDRESS: {settings.EMAIL_FROM_ADDRESS}")
    logger.info(f"FRONTEND_URL: {settings.FRONTEND_URL}")
    
    smtp_user_preview = None
    if settings.SMTP_USER:
        smtp_user_preview = f"{settings.SMTP_USER[:5]}***@{settings.SMTP_USER.split('@')[1] if '@' in settings.SMTP_USER else '***'}"
    
    return {
        "status": "configured" if email_service._is_configured() else "not_configured",
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_user_preview": smtp_user_preview,
        "smtp_user_set": bool(settings.SMTP_USER),
        "smtp_password_set": bool(settings.SMTP_PASSWORD),
        "smtp_password_length": len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 0,
        "email_from_address": settings.EMAIL_FROM_ADDRESS,
        "frontend_url": settings.FRONTEND_URL,
        "is_configured": email_service._is_configured(),
    }


@router.post("/email/send")
async def test_send_email(request: TestEmailRequest) -> Dict[str, Any]:
    """
    Test sending an actual email.
    
    Sends a test email to verify SMTP configuration works end-to-end.
    """
    from app.services.email_service import email_service
    
    logger.info("=== EMAIL SEND TEST ===")
    logger.info(f"Attempting to send test email to: {request.to_email}")
    logger.info(f"Email service configured: {email_service._is_configured()}")
    
    if not email_service._is_configured():
        logger.error("Email service is NOT configured!")
        logger.error(f"  SMTP_HOST: {settings.SMTP_HOST}")
        logger.error(f"  SMTP_PORT: {settings.SMTP_PORT}")
        logger.error(f"  SMTP_USER set: {bool(settings.SMTP_USER)}")
        logger.error(f"  SMTP_PASSWORD set: {bool(settings.SMTP_PASSWORD)}")
        logger.error(f"  EMAIL_FROM_ADDRESS: {settings.EMAIL_FROM_ADDRESS}")
        
        return {
            "status": "not_configured",
            "success": False,
            "message": "Email service is not configured. Check SMTP secrets.",
            "config": {
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
                "smtp_user_set": bool(settings.SMTP_USER),
                "smtp_password_set": bool(settings.SMTP_PASSWORD),
            }
        }
    
    try:
        logger.info("Calling email_service.send_email()...")
        
        success = await email_service.send_email(
            to_email=request.to_email,
            subject="🧪 DocLearn Email Test",
            html_content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
                    .success {{ color: #10B981; font-size: 24px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎓 DocLearn</h1>
                    </div>
                    <div class="content">
                        <p class="success">✅ Email Test Successful!</p>
                        <p>This is a test email from DocLearn.</p>
                        <p>If you received this, your email configuration is working correctly!</p>
                        <hr>
                        <p><small>Sent at: {datetime.utcnow().isoformat()}</small></p>
                    </div>
                </div>
            </body>
            </html>
            """,
            text_content="DocLearn Email Test - If you received this, your email configuration is working!",
        )
        
        logger.info(f"Email send result: {success}")
        
        if success:
            return {
                "status": "success",
                "success": True,
                "message": f"Email sent successfully to {request.to_email}",
                "sent_to": request.to_email,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            return {
                "status": "failed",
                "success": False,
                "message": "Email send returned False. Check Cloud Run logs for details.",
                "sent_to": request.to_email,
            }
            
    except Exception as e:
        logger.exception(f"Email send test failed: {str(e)}")
        return {
            "status": "error",
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.post("/email/verification")
async def test_verification_email(request: TestEmailRequest) -> Dict[str, Any]:
    """
    Test sending a verification email (same format as registration).
    """
    from app.services.email_service import email_service
    
    logger.info("=== VERIFICATION EMAIL TEST ===")
    logger.info(f"Sending verification email to: {request.to_email}")
    
    if not email_service._is_configured():
        return {
            "status": "not_configured",
            "success": False,
            "message": "Email service is not configured",
        }
    
    try:
        # Use a fake token for testing
        test_token = "test-token-abc123xyz"
        
        success = await email_service.send_verification_email(
            to_email=request.to_email,
            user_name="Test User",
            verification_token=test_token,
        )
        
        logger.info(f"Verification email send result: {success}")
        
        return {
            "status": "success" if success else "failed",
            "success": success,
            "message": f"Verification email {'sent' if success else 'failed'} to {request.to_email}",
            "sent_to": request.to_email,
            "test_token": test_token,
            "verification_url": f"{settings.FRONTEND_URL}/verify-email?token={test_token}",
        }
        
    except Exception as e:
        logger.exception(f"Verification email test failed: {str(e)}")
        return {
            "status": "error",
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
