"""
Chat Routes.

API endpoints for chat interactions with the AI tutor.
All services use MongoDB for data storage.
All endpoints are protected with JWT authentication.

Supports both burst and streaming responses:
- /chat: Standard endpoint (auto-detects streaming need, returns full response)
- /chat/stream: SSE streaming endpoint for real-time token delivery
"""
import logging
import json
from uuid import UUID
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.api.deps import (
    get_chat_service, 
    get_session_service,
    require_verified_user,
    AuthUser,
)
from app.services import ChatService, SessionService
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatMessage,
    StartLessonRequest,
    StartLessonResponse,
)
from app.core.llm_factory import (
    get_tutor_llm,
    classify_expected_response,
    estimate_response_tokens,
    should_stream,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


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


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: AuthUser = Depends(require_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Send a message to the AI tutor and receive a response.
    
    This endpoint automatically determines whether to use streaming internally,
    but always returns a complete response. For real-time streaming to the client,
    use the `/chat/stream` endpoint instead.
    
    The AI will:
    - Teach concepts one at a time
    - Ask questions to verify understanding
    - Adapt to user's pace and questions
    
    **Request Body:**
    - `session_id`: Session identifier
    - `message`: User's message to the tutor
    
    **Response:**
    - `response`: AI tutor's response
    - `current_day`: Current day in the lesson plan
    - `current_topic_index`: Current topic index
    - `is_day_complete`: Whether all topics for the day are done
    - `is_course_complete`: Whether the entire course is done
    """
    # Verify ownership
    await _verify_session_ownership(request.session_id, current_user.user_id, session_service)
    
    try:
        result = await chat_service.send_message(
            session_id=request.session_id,
            message=request.message,
        )
        
        return ChatResponse(
            session_id=request.session_id,
            response=result["response"],
            current_day=result["current_day"],
            current_topic_index=result["current_topic_index"],
            is_day_complete=result["is_day_complete"],
            is_course_complete=result["is_course_complete"],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/stream")
async def send_message_stream(
    request: ChatRequest,
    current_user: AuthUser = Depends(require_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Send a message and receive streaming response via Server-Sent Events (SSE).
    
    This endpoint streams the AI response token-by-token for real-time display.
    Useful for longer explanations where immediate feedback improves UX.
    
    **Streaming Strategy:**
    - Short responses (< 100 expected tokens): Sends as single burst
    - Long responses (>= 100 expected tokens): Streams token by token
    
    **SSE Event Format:**
    - `event: token` - Individual token chunks
    - `event: done` - Final message with metadata
    - `event: error` - Error information
    
    **Example SSE Stream:**
    ```
    event: token
    data: {"content": "Let's"}
    
    event: token
    data: {"content": " explore"}
    
    event: done
    data: {"current_day": 1, "is_day_complete": false}
    ```
    """
    # Validate session exists and belongs to user
    await _verify_session_ownership(request.session_id, current_user.user_id, session_service)
    
    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            # Determine if we should stream based on expected response
            response_type = classify_expected_response(request.message)
            expected_tokens = estimate_response_tokens(response_type)
            use_streaming = should_stream(expected_tokens)
            
            if use_streaming:
                # Stream the response token by token
                async for token, metadata in chat_service.send_message_streaming(
                    session_id=request.session_id,
                    message=request.message,
                ):
                    if token:
                        yield {
                            "event": "token",
                            "data": json.dumps({"content": token})
                        }
                
                # Send completion event
                yield {
                    "event": "done",
                    "data": json.dumps(metadata)
                }
            else:
                # Burst mode - send complete response
                result = await chat_service.send_message(
                    session_id=request.session_id,
                    message=request.message,
                )
                
                # Send as single token event
                yield {
                    "event": "token",
                    "data": json.dumps({"content": result["response"]})
                }
                
                # Send completion event
                yield {
                    "event": "done",
                    "data": json.dumps({
                        "current_day": result["current_day"],
                        "current_topic_index": result["current_topic_index"],
                        "is_day_complete": result["is_day_complete"],
                        "is_course_complete": result["is_course_complete"],
                    })
                }
                
        except Exception as e:
            logger.exception(f"Streaming error: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


@router.post("/start-lesson", response_model=StartLessonResponse)
async def start_lesson(
    request: StartLessonRequest,
    current_user: AuthUser = Depends(require_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Start or resume a lesson.
    
    If no day is specified, continues from the current day.
    If a day is specified, jumps to that day.
    
    Returns a welcome message and day objectives.
    """
    # Verify ownership
    await _verify_session_ownership(request.session_id, current_user.user_id, session_service)
    
    try:
        result = await chat_service.start_lesson(
            session_id=request.session_id,
            day=request.day,
        )
        
        return StartLessonResponse(
            session_id=request.session_id,
            current_day=result["current_day"],
            day_title=result["day_title"],
            objectives=result["objectives"],
            welcome_message=result["welcome_message"],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Start lesson error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start lesson: {str(e)}"
        )


@router.get("/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: UUID,
    limit: int = 100,
    current_user: AuthUser = Depends(require_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Get chat history for a session from MongoDB.
    
    Returns summaries (compressed history) and recent messages in buffer.
    """
    try:
        # Verify ownership
        session = await _verify_session_ownership(session_id, current_user.user_id, session_service)
        
        # Fetch from MongoDB
        history_data = await chat_service.get_chat_history(session_id, limit)
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=[
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg.get("timestamp"),
                )
                for msg in history_data["recent_messages"]
            ],
            total_messages=len(history_data["recent_messages"]),
            current_day=session["current_day"],
            summaries=history_data.get("summaries", []),
            total_summaries=history_data.get("total_summaries", 0),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
