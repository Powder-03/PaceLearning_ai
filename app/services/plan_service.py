"""
Plan Service.

Business logic for creating and managing lesson plans.
Orchestrates the plan generation process using MongoDB.
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from app.services.session_service import SessionService, SessionStatus
from app.graphs import invoke_generation_graph, create_initial_state

logger = logging.getLogger(__name__)


class PlanService:
    """
    Service class for managing lesson plans.
    
    Handles plan generation using the LangGraph planner node.
    Uses MongoDB for session storage.
    """
    
    def __init__(self, session_service: SessionService):
        """
        Initialize the plan service.
        
        Args:
            session_service: SessionService instance for data access
        """
        self.session_service = session_service
    
    async def create_plan(
        self,
        user_id: UUID,
        topic: str,
        total_days: int,
        time_per_day: str,
        mode: str = "generation",
        target: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new learning plan.
        
        This method:
        1. Creates a new session in PLANNING status
        2. Invokes the LangGraph to generate the curriculum
        3. Updates the session with the generated plan
        4. Returns the session info and welcome message
        
        Args:
            user_id: User identifier
            topic: Topic to learn
            total_days: Number of days for the plan
            time_per_day: Daily time commitment
            mode: Learning mode ('generation' or 'quick')
            target: Target exam or goal (for quick mode)
            
        Returns:
            Dictionary containing:
                - session_id: Created session ID
                - status: Session status
                - message: Welcome/status message
                - lesson_plan: Generated curriculum (if successful)
                
        Raises:
            Exception: If plan generation fails
        """
        # Force single day for quick mode
        if mode == "quick":
            total_days = 1
        
        # Create the session (async)
        session = await self.session_service.create_session(
            user_id=user_id,
            topic=topic,
            total_days=total_days,
            time_per_day=time_per_day,
            mode=mode,
            target=target,
        )
        
        session_id = session["session_id"]
        logger.info(f"Created session {session_id}, starting plan generation (mode={mode})")
        
        # Build initial state for the graph
        initial_state = create_initial_state(
            session_id=session_id,
            user_id=str(user_id),
            topic=topic,
            total_days=total_days,
            time_per_day=time_per_day,
            lesson_plan=None,  # No plan yet - triggers planning node
            mode=mode,
            target=target,
        )
        
        try:
            # Run the graph (will route to plan_generator_node)
            result = await invoke_generation_graph(initial_state)
            
            lesson_plan = result.get("lesson_plan")
            ai_response = result.get("ai_response", "Your plan is ready!")
            
            # Check if plan generation was successful
            if lesson_plan and "error" not in lesson_plan:
                # Update session with the plan (async)
                await self.session_service.update_lesson_plan(
                    session_id=UUID(session_id),
                    lesson_plan=lesson_plan,
                    status=SessionStatus.READY.value,
                )
                
                # Note: Chat history is now stored in MongoDB
                # The welcome message will be stored when user starts the lesson
                
                logger.info(f"Successfully generated plan for session {session_id}")
                
                return {
                    "session_id": UUID(session_id),
                    "status": SessionStatus.READY.value,
                    "message": ai_response,
                    "lesson_plan": lesson_plan,
                }
            else:
                # Plan generation failed
                error_msg = lesson_plan.get("error", "Unknown error") if lesson_plan else "No plan generated"
                
                await self.session_service.update_lesson_plan(
                    session_id=UUID(session_id),
                    lesson_plan={"error": error_msg},
                    status=SessionStatus.FAILED.value,
                )
                
                logger.error(f"Plan generation failed for session {session_id}: {error_msg}")
                
                return {
                    "session_id": UUID(session_id),
                    "status": SessionStatus.FAILED.value,
                    "message": f"Failed to generate plan: {error_msg}",
                    "lesson_plan": None,
                }
                
        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error during plan generation: {str(e)}")
            
            await self.session_service.update_lesson_plan(
                session_id=UUID(session_id),
                lesson_plan={"error": str(e)},
                status=SessionStatus.FAILED.value,
            )
            
            raise
    
    async def get_plan(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get the lesson plan for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with plan details
            
        Raises:
            ValueError: If session not found or plan not ready
        """
        session = await self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.get("lesson_plan"):
            raise ValueError("Lesson plan not yet generated")
        
        progress = self.session_service.calculate_progress_percentage(session)
        
        return {
            "session_id": UUID(session["session_id"]),
            "topic": session["topic"],
            "lesson_plan": session["lesson_plan"],
            "current_day": session["current_day"],
            "total_days": session["total_days"],
            "progress_percentage": progress,
        }
    
    async def get_day_content(self, session_id: UUID, day: int) -> Dict[str, Any]:
        """
        Get content for a specific day.
        
        Args:
            session_id: Session identifier
            day: Day number (1-indexed)
            
        Returns:
            Dictionary with day content
            
        Raises:
            ValueError: If session not found or invalid day
        """
        session = await self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.get("lesson_plan"):
            raise ValueError("Lesson plan not yet generated")
        
        days = session["lesson_plan"].get("days", [])
        if day < 1 or day > len(days):
            raise ValueError(f"Day must be between 1 and {len(days)}")
        
        day_content = days[day - 1]
        
        return {
            "session_id": UUID(session["session_id"]),
            "day": day,
            "total_days": session["total_days"],
            "is_current_day": day == session["current_day"],
            "is_completed": day < session["current_day"],
            **day_content,
        }
