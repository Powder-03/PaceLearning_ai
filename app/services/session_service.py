"""
Session Service - MongoDB Implementation.

Business logic for managing learning sessions using MongoDB.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum as PyEnum

from app.services.mongodb import MongoDBService

logger = logging.getLogger(__name__)


class SessionStatus(str, PyEnum):
    """Status of a learning session."""
    PLANNING = "PLANNING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SessionMode(str, PyEnum):
    """Mode of learning session."""
    GENERATION = "generation"
    RAG = "rag"


class SessionService:
    """
    Service class for managing learning sessions with MongoDB.
    
    Handles all CRUD operations and business logic related to sessions.
    """
    
    COLLECTION_NAME = "learning_sessions"
    
    def __init__(self):
        """Initialize the session service."""
        pass
    
    def _get_collection(self):
        """Get the sessions collection."""
        db = MongoDBService.get_db()
        return db[self.COLLECTION_NAME]
    
    # =========================================================================
    # CREATE OPERATIONS
    # =========================================================================
    
    async def create_session(
        self,
        user_id: uuid.UUID,
        topic: str,
        total_days: int,
        time_per_day: str,
        mode: str = SessionMode.GENERATION.value,
    ) -> Dict[str, Any]:
        """
        Create a new learning session.
        
        Args:
            user_id: User identifier
            topic: Learning topic
            total_days: Total days for the plan
            time_per_day: Daily time commitment
            mode: Session mode (generation or rag)
            
        Returns:
            Created session document
        """
        try:
            collection = self._get_collection()
            
            session_doc = {
                "session_id": str(uuid.uuid4()),
                "user_id": str(user_id),
                "mode": mode,
                "status": SessionStatus.PLANNING.value,
                "topic": topic,
                "total_days": total_days,
                "time_per_day": time_per_day,
                "lesson_plan": None,
                "current_day": 1,
                "current_topic_index": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "completed_at": None,
            }
            
            await collection.insert_one(session_doc)
            
            logger.info(f"Created session {session_doc['session_id']} for user {user_id}")
            return session_doc
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    async def get_session(self, session_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session document if found, None otherwise
        """
        collection = self._get_collection()
        return await collection.find_one({"session_id": str(session_id)})
    
    async def get_session_or_raise(self, session_id: uuid.UUID) -> Dict[str, Any]:
        """
        Retrieve a session by ID or raise an exception.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session document
            
        Raises:
            ValueError: If session not found
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return session
    
    async def get_user_sessions(
        self, 
        user_id: uuid.UUID,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user with optional filtering.
        
        Args:
            user_id: User identifier
            mode: Filter by mode (optional)
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of session documents
        """
        collection = self._get_collection()
        
        query = {"user_id": str(user_id)}
        
        if mode:
            query["mode"] = mode
        
        if status:
            query["status"] = status
        
        cursor = collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def count_user_sessions(
        self, 
        user_id: uuid.UUID,
        mode: Optional[str] = None,
    ) -> int:
        """Count total sessions for a user."""
        collection = self._get_collection()
        
        query = {"user_id": str(user_id)}
        
        if mode:
            query["mode"] = mode
        
        return await collection.count_documents(query)
    
    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================
    
    async def update_lesson_plan(
        self,
        session_id: uuid.UUID,
        lesson_plan: Dict[str, Any],
        status: str = SessionStatus.READY.value,
    ) -> Optional[Dict[str, Any]]:
        """
        Update the lesson plan for a session.
        
        Args:
            session_id: Session identifier
            lesson_plan: Generated lesson plan JSON
            status: New session status
            
        Returns:
            Updated session or None if not found
        """
        collection = self._get_collection()
        
        result = await collection.find_one_and_update(
            {"session_id": str(session_id)},
            {
                "$set": {
                    "lesson_plan": lesson_plan,
                    "status": status,
                    "updated_at": datetime.utcnow(),
                }
            },
            return_document=True,
        )
        
        if result:
            logger.info(f"Updated lesson plan for session {session_id}")
        
        return result
    
    async def update_progress(
        self,
        session_id: uuid.UUID,
        current_day: Optional[int] = None,
        current_topic_index: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update learning progress.
        
        Args:
            session_id: Session identifier
            current_day: New current day (optional)
            current_topic_index: New topic index (optional)
            
        Returns:
            Updated session or None
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        update_fields = {"updated_at": datetime.utcnow()}
        
        if current_day is not None:
            update_fields["current_day"] = min(current_day, session["total_days"])
        
        if current_topic_index is not None:
            update_fields["current_topic_index"] = current_topic_index
        
        # Check if course is complete
        new_day = update_fields.get("current_day", session["current_day"])
        new_topic_idx = update_fields.get("current_topic_index", session["current_topic_index"])
        
        if new_day >= session["total_days"]:
            lesson_plan = session.get("lesson_plan") or {}
            days = lesson_plan.get("days", [])
            if days:
                last_day = days[-1]
                topics = last_day.get("topics", [])
                if new_topic_idx >= len(topics) - 1:
                    update_fields["status"] = SessionStatus.COMPLETED.value
                    update_fields["completed_at"] = datetime.utcnow()
        
        collection = self._get_collection()
        return await collection.find_one_and_update(
            {"session_id": str(session_id)},
            {"$set": update_fields},
            return_document=True,
        )
    
    async def advance_day(self, session_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Move to the next day.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated session or None
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        if session["current_day"] < session["total_days"]:
            return await self.update_progress(
                session_id,
                current_day=session["current_day"] + 1,
                current_topic_index=0,
            )
        
        return session
    
    async def advance_topic(self, session_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Move to the next topic within the current day.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated session or None
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        return await self.update_progress(
            session_id,
            current_topic_index=session["current_topic_index"] + 1,
        )
    
    async def set_status(
        self,
        session_id: uuid.UUID,
        status: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Update session status.
        
        Args:
            session_id: Session identifier
            status: New status value
            
        Returns:
            Updated session or None
        """
        collection = self._get_collection()
        
        update_fields = {
            "status": status,
            "updated_at": datetime.utcnow(),
        }
        
        if status == SessionStatus.COMPLETED.value:
            update_fields["completed_at"] = datetime.utcnow()
        
        return await collection.find_one_and_update(
            {"session_id": str(session_id)},
            {"$set": update_fields},
            return_document=True,
        )
    
    # =========================================================================
    # DELETE OPERATIONS
    # =========================================================================
    
    async def delete_session(self, session_id: uuid.UUID) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        collection = self._get_collection()
        
        result = await collection.delete_one({"session_id": str(session_id)})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted session {session_id}")
            return True
        
        return False
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def calculate_progress_percentage(self, session: Dict[str, Any]) -> float:
        """
        Calculate completion percentage for a session.
        
        Args:
            session: Session document
            
        Returns:
            Progress percentage (0-100)
        """
        lesson_plan = session.get("lesson_plan")
        if not lesson_plan:
            return 0.0
        
        days = lesson_plan.get("days", [])
        if not days:
            return 0.0
        
        total_topics = sum(len(day.get("topics", [])) for day in days)
        if total_topics == 0:
            return 0.0
        
        # Count completed topics
        completed_topics = 0
        current_day = session.get("current_day", 1)
        current_topic_index = session.get("current_topic_index", 0)
        
        for i, day in enumerate(days):
            day_num = i + 1
            topics_in_day = len(day.get("topics", []))
            
            if day_num < current_day:
                # All topics in previous days are complete
                completed_topics += topics_in_day
            elif day_num == current_day:
                # Current day - count up to current topic
                completed_topics += min(current_topic_index, topics_in_day)
        
        return round((completed_topics / total_topics) * 100, 1)
    
    def session_to_dict(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to API response format."""
        return {
            "session_id": session.get("session_id"),
            "user_id": session.get("user_id"),
            "mode": session.get("mode"),
            "status": session.get("status"),
            "topic": session.get("topic"),
            "total_days": session.get("total_days"),
            "time_per_day": session.get("time_per_day"),
            "lesson_plan": session.get("lesson_plan"),
            "current_day": session.get("current_day"),
            "current_topic_index": session.get("current_topic_index"),
            "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
            "updated_at": session.get("updated_at").isoformat() if session.get("updated_at") else None,
            "completed_at": session.get("completed_at").isoformat() if session.get("completed_at") else None,
        }
