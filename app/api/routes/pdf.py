"""
PDF Routes.

API endpoints for generating PDF documents:
- Daily Practice Problems (DPP)
- Session Notes
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.deps import (
    get_session_service,
    require_verified_user,
    AuthUser,
)
from app.services import SessionService
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pdf", tags=["PDF Generation"])


async def _verify_session_ownership(
    session_id: UUID,
    user_id: str,
    session_service: SessionService,
) -> dict:
    """Helper to verify session exists and belongs to the user."""
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    return session


@router.get("/{session_id}/dpp/{day}")
async def generate_dpp(
    session_id: UUID,
    day: int,
    current_user: AuthUser = Depends(require_verified_user),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Generate Daily Practice Problems (DPP) PDF for a specific day.
    
    Returns a PDF file with practice questions and answers.
    
    **Path Parameters:**
    - `session_id`: Session identifier
    - `day`: Day number (1-based)
    
    **Returns:**
    - PDF file download
    """
    session = await _verify_session_ownership(session_id, current_user.user_id, session_service)
    
    try:
        pdf_bytes = await pdf_service.generate_dpp(session, day)
        
        filename = f"DPP_Day{day}_{session['topic'].replace(' ', '_')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error generating DPP: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate DPP")


@router.get("/{session_id}/notes/{day}")
async def generate_notes(
    session_id: UUID,
    day: int,
    current_user: AuthUser = Depends(require_verified_user),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Generate study notes PDF for a specific day.
    
    Returns a PDF file with comprehensive notes for the day's topics.
    
    **Path Parameters:**
    - `session_id`: Session identifier
    - `day`: Day number (1-based)
    
    **Returns:**
    - PDF file download
    """
    session = await _verify_session_ownership(session_id, current_user.user_id, session_service)
    
    try:
        pdf_bytes = await pdf_service.generate_notes(session, day)
        
        filename = f"Notes_Day{day}_{session['topic'].replace(' ', '_')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error generating notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate notes")
