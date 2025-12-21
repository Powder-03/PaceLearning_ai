"""
MongoDB service for chat storage and memory management.
Handles connection, chat operations, and buffer-based storage.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBService:
    """MongoDB client wrapper with connection management."""
    
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls) -> None:
        """Initialize MongoDB connection with timeout."""
        if cls._client is None:
            cls._client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
            )
            cls._db = cls._client[settings.MONGODB_DB_NAME]
            
            # Test connection with ping
            await cls._client.admin.command('ping')
            
            # Create indexes for optimal query performance
            await cls._create_indexes()
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    
    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls) -> None:
        """Create necessary indexes for performance."""
        if cls._db is not None:
            # Index for fast session lookups
            await cls._db.chat_history.create_index("session_id", unique=True)
            await cls._db.chat_history.create_index("updated_at")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls._db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls._db


class ChatStorageService:
    """
    Service for storing and retrieving chat messages with buffer management.
    
    Chat Document Schema:
    {
        "session_id": str,
        "messages": [
            {"role": "user", "content": str, "timestamp": datetime},
            {"role": "assistant", "content": str, "timestamp": datetime}
        ],
        "buffer_count": int,  # Current count of messages in buffer
        "summaries": [str],  # List of summarized conversation chunks
        "created_at": datetime,
        "updated_at": datetime
    }
    """
    
    def __init__(self):
        self.collection_name = "chat_history"
    
    @property
    def collection(self):
        """Get the chat history collection."""
        return MongoDBService.get_db()[self.collection_name]
    
    async def get_or_create_chat(self, session_id: str) -> Dict[str, Any]:
        """Get existing chat document or create a new one."""
        doc = await self.collection.find_one({"session_id": session_id})
        
        if doc is None:
            doc = {
                "session_id": session_id,
                "messages": [],
                "buffer_count": 0,
                "summaries": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await self.collection.insert_one(doc)
            logger.info(f"Created new chat document for session: {session_id}")
        
        return doc
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str
    ) -> Dict[str, Any]:
        """
        Add a message to the chat buffer.
        
        Args:
            session_id: The session identifier
            role: 'user' or 'assistant'
            content: The message content
            
        Returns:
            Updated chat document
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        
        result = await self.collection.find_one_and_update(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$inc": {"buffer_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True,
            return_document=True
        )
        
        # If document didn't exist, initialize it properly
        if result is None or "created_at" not in result:
            await self.collection.update_one(
                {"session_id": session_id},
                {
                    "$setOnInsert": {
                        "created_at": datetime.utcnow(),
                        "summaries": []
                    }
                }
            )
            result = await self.collection.find_one({"session_id": session_id})
        
        logger.debug(f"Added message to session {session_id}, buffer count: {result.get('buffer_count', 0)}")
        return result
    
    async def get_buffer_count(self, session_id: str) -> int:
        """Get the current buffer count for a session."""
        doc = await self.collection.find_one(
            {"session_id": session_id},
            {"buffer_count": 1}
        )
        return doc.get("buffer_count", 0) if doc else 0
    
    async def get_buffer_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages currently in the buffer."""
        doc = await self.collection.find_one(
            {"session_id": session_id},
            {"messages": 1}
        )
        return doc.get("messages", []) if doc else []
    
    async def get_summaries(self, session_id: str) -> List[str]:
        """Get all conversation summaries for a session."""
        doc = await self.collection.find_one(
            {"session_id": session_id},
            {"summaries": 1}
        )
        return doc.get("summaries", []) if doc else []
    
    async def clear_buffer_and_add_summary(
        self, 
        session_id: str, 
        summary: str
    ) -> Dict[str, Any]:
        """
        Clear the message buffer and add a summary.
        Called after summarization when buffer reaches threshold.
        
        Args:
            session_id: The session identifier
            summary: The summarized content of the buffer messages
            
        Returns:
            Updated chat document
        """
        result = await self.collection.find_one_and_update(
            {"session_id": session_id},
            {
                "$set": {
                    "messages": [],
                    "buffer_count": 0,
                    "updated_at": datetime.utcnow()
                },
                "$push": {"summaries": summary}
            },
            return_document=True
        )
        
        logger.info(f"Cleared buffer and added summary for session: {session_id}")
        return result
    
    async def get_full_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get the full conversation context including summaries and buffer.
        
        Returns:
            Dict with 'summaries' (list of str) and 'recent_messages' (list of messages)
        """
        doc = await self.collection.find_one(
            {"session_id": session_id},
            {"summaries": 1, "messages": 1}
        )
        
        if doc is None:
            return {"summaries": [], "recent_messages": []}
        
        return {
            "summaries": doc.get("summaries", []),
            "recent_messages": doc.get("messages", [])
        }
    
    async def format_context_for_llm(self, session_id: str) -> str:
        """
        Format the conversation context for LLM consumption.
        Combines summaries and recent messages into a coherent context string.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Formatted context string for the LLM
        """
        context = await self.get_full_context(session_id)
        
        parts = []
        
        # Add summaries first (older context)
        if context["summaries"]:
            parts.append("=== Previous Conversation Summary ===")
            for i, summary in enumerate(context["summaries"], 1):
                parts.append(f"[Part {i}]: {summary}")
            parts.append("")
        
        # Add recent messages (buffer)
        if context["recent_messages"]:
            parts.append("=== Recent Conversation ===")
            for msg in context["recent_messages"]:
                role = "Student" if msg["role"] == "user" else "Tutor"
                parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(parts) if parts else ""
    
    async def delete_chat(self, session_id: str) -> bool:
        """Delete all chat data for a session."""
        result = await self.collection.delete_one({"session_id": session_id})
        return result.deleted_count > 0


# Singleton instance
chat_storage = ChatStorageService()
