"""
Graph State Definitions.

Defines the TypedDict state structure used by the LangGraph
for managing conversation flow and lesson progress.
"""
from typing import TypedDict, Optional, Dict, Any, List, Annotated
from operator import add

from langchain_core.messages import BaseMessage


class GenerationGraphState(TypedDict):
    """
    State for the Generation Mode LangGraph.
    
    This state is passed between nodes and contains all information
    needed to generate lesson plans and conduct tutoring sessions.
    """
    # Session Identification
    session_id: str
    user_id: str
    
    # Learning Configuration
    topic: str
    total_days: int
    time_per_day: str
    mode: str  # "generation" or "quick"
    target: Optional[str]  # Target exam/goal for quick mode
    
    # Generated Content
    lesson_plan: Optional[Dict[str, Any]]
    
    # Progress Tracking
    current_day: int
    current_topic_index: int
    
    # Conversation State
    chat_history: List[BaseMessage]
    memory_summary: Optional[str]
    
    # Current Turn
    user_message: Optional[str]
    ai_response: Optional[str]
    
    # Control Flags
    is_day_complete: bool
    is_course_complete: bool
    should_advance_topic: bool


def create_initial_state(
    session_id: str,
    user_id: str,
    topic: str,
    total_days: int,
    time_per_day: str,
    lesson_plan: Optional[Dict[str, Any]] = None,
    current_day: int = 1,
    current_topic_index: int = 0,
    chat_history: Optional[List[BaseMessage]] = None,
    memory_summary: Optional[str] = None,
    mode: str = "generation",
    target: Optional[str] = None,
) -> GenerationGraphState:
    """
    Factory function to create an initial graph state.
    
    Args:
        session_id: Unique session identifier
        user_id: User identifier
        topic: Learning topic
        total_days: Total days in the plan
        time_per_day: Time commitment per day
        lesson_plan: Pre-existing lesson plan (None for new sessions)
        current_day: Current day progress
        current_topic_index: Current topic within the day
        chat_history: Previous conversation messages
        memory_summary: Compressed conversation summary
        mode: Session mode ('generation' or 'quick')
        target: Target exam/goal for quick mode
        
    Returns:
        Initialized GenerationGraphState
    """
    return GenerationGraphState(
        session_id=session_id,
        user_id=user_id,
        topic=topic,
        total_days=total_days,
        time_per_day=time_per_day,
        mode=mode,
        target=target,
        lesson_plan=lesson_plan,
        current_day=current_day,
        current_topic_index=current_topic_index,
        chat_history=chat_history or [],
        memory_summary=memory_summary,
        user_message=None,
        ai_response=None,
        is_day_complete=False,
        is_course_complete=False,
        should_advance_topic=False,
    )
