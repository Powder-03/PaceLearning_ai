"""
Chat Service.

Business logic for handling chat interactions with the AI tutor.
Orchestrates the LangGraph execution and state management.

Supports both burst and streaming response modes:
- Burst: Complete response returned at once (< 100 expected tokens)
- Streaming: Token-by-token delivery (>= 100 expected tokens)

Uses MongoDB for all storage:
- Sessions stored in MongoDB
- Chat messages stored in buffer with summarization
"""
import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator, Tuple
from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.session_service import SessionService, SessionStatus
from app.services.memory import memory_service, MemoryService
from app.graphs import invoke_generation_graph, create_initial_state
from app.core.llm_factory import get_tutor_llm
from app.core.prompts import TUTOR_SYSTEM_PROMPT, TUTOR_FIRST_MESSAGE_PROMPT

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service class for handling chat interactions.
    
    Manages the conversation flow between users and the AI tutor,
    including graph invocation and state persistence.
    
    Uses MongoDB for chat storage with buffer-based summarization.
    """
    
    def __init__(
        self, 
        session_service: SessionService,
        memory: MemoryService = memory_service,
    ):
        """
        Initialize the chat service.
        
        Args:
            session_service: SessionService instance for data access
            memory: MemoryService for chat storage and summarization
        """
        self.session_service = session_service
        self.memory = memory
    
    async def send_message(
        self,
        session_id: UUID,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send a message to the AI tutor and get a response.
        
        Args:
            session_id: Session identifier
            message: User's message
            
        Returns:
            Dictionary containing:
                - response: AI's response
                - current_day: Current day number
                - current_topic_index: Current topic index
                - is_day_complete: Whether day is complete
                - is_course_complete: Whether course is complete
                
        Raises:
            ValueError: If session not found or not ready
        """
        # Get session (async)
        session = await self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session["status"] not in [SessionStatus.READY.value, SessionStatus.IN_PROGRESS.value]:
            raise ValueError(f"Session is not ready for chat. Status: {session['status']}")
        
        # Update status to in progress if needed
        if session["status"] == SessionStatus.READY.value:
            await self.session_service.set_status(session_id, SessionStatus.IN_PROGRESS.value)
        
        # Get lesson plan info for topic advancement analysis
        lesson_plan = session.get("lesson_plan") or {}
        days = lesson_plan.get("days", [])
        current_day = session["current_day"]
        current_topic_index = session["current_topic_index"]
        day_content = days[current_day - 1] if current_day <= len(days) else {}
        topics = day_content.get("topics", [])
        current_topic = topics[current_topic_index] if current_topic_index < len(topics) else {}
        
        # Build graph state from session (now includes MongoDB chat history)
        state = await self._build_state_from_session(session, message)
        
        # Invoke the graph
        result = await invoke_generation_graph(state)
        
        # Store messages in MongoDB (handles buffer + summarization)
        ai_response = result.get("ai_response", "")
        if ai_response:
            await self.memory.add_user_message(str(session_id), message)
            await self.memory.add_assistant_message(str(session_id), ai_response)
        
        # Use LLM-based sentiment analysis to determine topic advancement
        should_advance = await self._should_advance_topic(message, ai_response, current_topic)
        
        new_topic_index = current_topic_index
        is_day_complete = False
        
        if should_advance:
            if current_topic_index < len(topics) - 1:
                new_topic_index = current_topic_index + 1
                await self.session_service.advance_topic(session_id)
                logger.info(f"Advanced to topic {new_topic_index} in day {current_day}")
            else:
                is_day_complete = True
                logger.info(f"Day {current_day} completed")
        
        is_course_complete = is_day_complete and current_day >= session["total_days"]
        
        return {
            "response": ai_response,
            "current_day": current_day,
            "current_topic_index": new_topic_index,
            "is_day_complete": is_day_complete,
            "is_course_complete": is_course_complete,
        }
    
    async def start_lesson(
        self,
        session_id: UUID,
        day: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Start or resume a lesson for a specific day.
        
        Args:
            session_id: Session identifier
            day: Day number to start (optional, defaults to current day)
            
        Returns:
            Dictionary with lesson info and welcome message
            
        Raises:
            ValueError: If session not found or invalid day
        """
        session = await self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session["status"] == SessionStatus.PLANNING.value:
            raise ValueError("Lesson plan is still being generated")
        
        # Set day if specified
        if day is not None:
            if day < 1 or day > session["total_days"]:
                raise ValueError(f"Day must be between 1 and {session['total_days']}")
            await self.session_service.update_progress(session_id, current_day=day, current_topic_index=0)
            session = await self.session_service.get_session(session_id)
        
        # Get day content
        lesson_plan = session.get("lesson_plan") or {}
        days = lesson_plan.get("days", [])
        
        if session["current_day"] <= len(days):
            day_content = days[session["current_day"] - 1]
        else:
            day_content = {}
        
        # Build state and invoke graph for welcome message
        state = await self._build_state_from_session(session, user_message=None)
        result = await invoke_generation_graph(state)
        
        # Store the welcome message in MongoDB
        if result.get("ai_response"):
            await self.memory.add_user_message(str(session_id), "[Started lesson]")
            await self.memory.add_assistant_message(str(session_id), result["ai_response"])
        
        return {
            "current_day": session["current_day"],
            "day_title": day_content.get("title", f"Day {session['current_day']}"),
            "objectives": day_content.get("objectives", []),
            "welcome_message": result.get("ai_response", ""),
        }
    
    async def get_chat_history(
        self,
        session_id: UUID,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get chat history for a session from MongoDB.
        
        Args:
            session_id: Session identifier
            limit: Maximum recent messages to return
            
        Returns:
            Dictionary with summaries and recent messages
            
        Raises:
            ValueError: If session not found
        """
        session = await self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        context = await self.memory.storage.get_full_context(str(session_id))
        
        return {
            "summaries": context["summaries"],
            "recent_messages": context["recent_messages"][-limit:],
            "total_summaries": len(context["summaries"]),
        }
    
    async def send_message_streaming(
        self,
        session_id: UUID,
        message: str,
    ) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """
        Send a message and stream the response token by token.
        
        This method yields tokens as they're generated, allowing for
        real-time streaming to the client via SSE.
        
        Args:
            session_id: Session identifier
            message: User's message
            
        Yields:
            Tuple of (token, metadata) where:
                - token: The text chunk (empty string for final yield)
                - metadata: Dict with session state (only on final yield)
                
        Raises:
            ValueError: If session not found or not ready
        """
        # Get session (async)
        session = await self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session["status"] not in [SessionStatus.READY.value, SessionStatus.IN_PROGRESS.value]:
            raise ValueError(f"Session is not ready for chat. Status: {session['status']}")
        
        # Update status to in progress if needed
        if session["status"] == SessionStatus.READY.value:
            await self.session_service.set_status(session_id, SessionStatus.IN_PROGRESS.value)
        
        # Build context for streaming
        lesson_plan = session.get("lesson_plan") or {}
        current_day = session["current_day"]
        current_topic_index = session["current_topic_index"]
        
        # Get current day's content
        days = lesson_plan.get("days", [])
        day_content = days[current_day - 1] if current_day <= len(days) else {}
        topics = day_content.get("topics", [])
        current_topic = topics[current_topic_index] if current_topic_index < len(topics) else {}
        
        # Get memory context from MongoDB
        memory_context = await self.memory.get_context_for_graph(str(session_id))
        
        # Build system prompt with MongoDB memory
        system_prompt = TUTOR_SYSTEM_PROMPT.format(
            topic=session["topic"],
            current_day=current_day,
            total_days=session["total_days"],
            day_title=day_content.get("title", f"Day {current_day}"),
            day_objectives=", ".join(day_content.get("objectives", [])),
            current_topic=json.dumps(current_topic, indent=2) if current_topic else "Wrapping up the day",
            memory_summary=memory_context.get("memory_summary") or "This is the start of the conversation.",
        )
        
        # Build messages
        messages = [SystemMessage(content=system_prompt)]
        
        # Add recent chat history from MongoDB buffer
        chat_history = self._convert_history_to_messages(memory_context.get("chat_history", []))
        messages.extend(chat_history[-20:])
        
        # Add current user message
        messages.append(HumanMessage(content=message))
        
        # Get streaming LLM
        llm = get_tutor_llm(temperature=0.7, streaming=True)
        
        # Collect full response while streaming
        full_response = ""
        
        try:
            async for chunk in llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    yield (chunk.content, {})
            
            # Store messages in MongoDB (handles buffer + summarization)
            await self.memory.add_user_message(str(session_id), message)
            await self.memory.add_assistant_message(str(session_id), full_response)
            
            # Use LLM-based sentiment analysis to determine topic advancement
            should_advance = await self._should_advance_topic(message, full_response, current_topic)
            
            new_topic_index = current_topic_index
            is_day_complete = False
            
            if should_advance:
                # Advance to next topic
                if current_topic_index < len(topics) - 1:
                    new_topic_index = current_topic_index + 1
                    await self.session_service.advance_topic(session_id)
                    logger.info(f"Advanced to topic {new_topic_index} in day {current_day}")
                else:
                    # All topics in day complete
                    is_day_complete = True
                    logger.info(f"Day {current_day} completed")
            
            is_course_complete = is_day_complete and current_day >= session["total_days"]
            
            # Yield final metadata
            yield ("", {
                "current_day": current_day,
                "current_topic_index": new_topic_index,
                "is_day_complete": is_day_complete,
                "is_course_complete": is_course_complete,
                "topic_advanced": should_advance,
            })
            
        except Exception as e:
            logger.exception(f"Streaming error: {str(e)}")
            raise
    
    async def _should_advance_topic(self, user_message: str, ai_response: str, current_topic: Dict[str, Any]) -> bool:
        """
        Use Gemini 2.5 Flash to analyze if user has understood the topic and is ready to advance.
        
        Performs sentiment analysis on the conversation to determine:
        1. Has the user demonstrated understanding of the current topic?
        2. Is the user explicitly asking to move forward?
        3. Has the AI completed explaining the topic?
        
        Returns True only if the LLM determines the user is ready.
        """
        if not user_message:
            return False
        
        topic_title = current_topic.get("title", "current topic") if current_topic else "current topic"
        
        # Use Gemini 2.5 Flash for sentiment analysis
        llm = get_tutor_llm(temperature=0.1, streaming=False)
        
        analysis_prompt = f"""Analyze this conversation exchange and determine if the student should advance to the next topic.

CURRENT TOPIC: {topic_title}

STUDENT'S MESSAGE: "{user_message}"

TUTOR'S RESPONSE: "{ai_response[:500]}..."

Evaluate:
1. Is the student EXPLICITLY requesting to move to the next topic? (e.g., "next topic", "move on", "what's next")
2. Has the student demonstrated clear understanding through their response?
3. Is this just a simple acknowledgment (like "okay", "yes", "got it") without deeper engagement?

IMPORTANT RULES:
- Simple acknowledgments like "okay", "yes", "got it", "thanks" should return NO
- Questions about the current topic should return NO (student wants to learn more)
- Only return YES if the student explicitly asks to move forward OR shows mastery AND requests progression

Respond with ONLY one word: YES or NO"""

        try:
            messages = [
                SystemMessage(content="You are an educational assessment assistant. Analyze student readiness precisely."),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = await llm.ainvoke(messages)
            result = response.content.strip().upper()
            
            should_advance = result == "YES"
            logger.info(f"LLM topic advancement analysis: {result} (advance={should_advance})")
            
            return should_advance
            
        except Exception as e:
            logger.error(f"Error in LLM topic advancement analysis: {e}")
            # Fallback: only advance on very explicit requests
            explicit_phrases = ["next topic", "move on", "next lesson", "what's next"]
            return any(phrase in user_message.lower() for phrase in explicit_phrases)
    
    async def _build_state_from_session(
        self,
        session: Dict[str, Any],
        user_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build graph state from a session document.
        
        Fetches chat history from MongoDB.
        
        Args:
            session: Session document from MongoDB
            user_message: Current user message (optional)
            
        Returns:
            Graph state dictionary
        """
        # Get memory context from MongoDB
        memory_context = await self.memory.get_context_for_graph(session["session_id"])
        
        # Convert stored chat history to LangChain messages
        chat_history = self._convert_history_to_messages(memory_context.get("chat_history", []))
        
        return create_initial_state(
            session_id=session["session_id"],
            user_id=session["user_id"],
            topic=session["topic"],
            total_days=session["total_days"],
            time_per_day=session["time_per_day"],
            lesson_plan=session.get("lesson_plan"),
            current_day=session["current_day"],
            current_topic_index=session["current_topic_index"],
            chat_history=chat_history,
            memory_summary=memory_context.get("memory_summary"),
        ) | {"user_message": user_message}
    
    def _convert_history_to_messages(
        self,
        history: List[Dict[str, Any]],
    ) -> List:
        """
        Convert stored chat history to LangChain message objects.
        
        Args:
            history: List of message dictionaries
            
        Returns:
            List of LangChain message objects
        """
        messages = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role in ["human", "user"]:
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        
        return messages
    
    async def clear_chat_history(self, session_id: UUID) -> bool:
        """
        Clear all chat history for a session from MongoDB.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        return await self.memory.clear_session_memory(str(session_id))
    
    async def force_summarize(self, session_id: UUID) -> Optional[str]:
        """
        Force summarization of current buffer regardless of count.
        Useful for session end or explicit user request.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Generated summary or None if no messages
        """
        return await self.memory.force_summarize(str(session_id))
