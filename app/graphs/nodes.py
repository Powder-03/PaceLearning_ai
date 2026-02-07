"""
LangGraph Nodes for Generation Mode.

Contains the node functions that perform the actual work:
- plan_generator_node: Creates the curriculum (Gemini 2.5 Pro)
- tutor_node: Handles interactive teaching (Gemini 2.5 Flash)

Streaming Strategy:
- Expected tokens < 100: Burst response
- Expected tokens >= 100: Streaming response
"""
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.graphs.state import GenerationGraphState
from app.core.llm_factory import (
    get_planner_llm, 
    get_tutor_llm,
    should_stream,
    estimate_response_tokens,
    classify_expected_response,
)
from app.core.prompts import (
    PLAN_GENERATION_SYSTEM_PROMPT,
    PLAN_GENERATION_PROMPT,
    QUICK_PLAN_GENERATION_SYSTEM_PROMPT,
    QUICK_PLAN_GENERATION_PROMPT,
    TUTOR_SYSTEM_PROMPT,
    TUTOR_FIRST_MESSAGE_PROMPT,
)

logger = logging.getLogger(__name__)


async def plan_generator_node(state: GenerationGraphState) -> Dict[str, Any]:
    """
    Node that generates the complete lesson plan.
    
    Uses Gemini 2.5 Pro for powerful, structured JSON output.
    This node is only called once per session to create the curriculum.
    Always uses burst mode (non-streaming) since we need complete JSON.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with lesson_plan and initial ai_response
    """
    mode = state.get("mode", "generation")
    target = state.get("target", "General understanding")
    logger.info(f"Generating lesson plan for topic: {state['topic']} (mode={mode})")
    
    # Planning always uses burst mode (need complete JSON)
    llm = get_planner_llm(temperature=0.3, streaming=False)
    
    # Build the planning prompt based on mode
    if mode == "quick":
        system_prompt = QUICK_PLAN_GENERATION_SYSTEM_PROMPT
        prompt = QUICK_PLAN_GENERATION_PROMPT.format(
            topic=state["topic"],
            time_per_day=state["time_per_day"],
            target=target or "General understanding",
        )
    else:
        system_prompt = PLAN_GENERATION_SYSTEM_PROMPT
        prompt = PLAN_GENERATION_PROMPT.format(
            topic=state["topic"],
            total_days=state["total_days"],
            time_per_day=state["time_per_day"],
            goal=target or "Master the topic thoroughly",
        )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = response.content
        
        # Extract JSON from response (handle potential markdown formatting)
        lesson_plan = _parse_json_response(content)
        
        logger.info(f"Successfully generated lesson plan with {len(lesson_plan.get('days', []))} days")
        
        # Create welcome message
        welcome_message = _create_welcome_message(state["topic"], lesson_plan)
        
        return {
            "lesson_plan": lesson_plan,
            "ai_response": welcome_message,
        }
        
    except Exception as e:
        logger.error(f"Failed to generate lesson plan: {str(e)}")
        return {
            "lesson_plan": {"error": str(e)},
            "ai_response": f"I encountered an error while creating your lesson plan. Please try again. Error: {str(e)}",
        }


async def tutor_node(state: GenerationGraphState) -> Dict[str, Any]:
    """
    Node that handles interactive tutoring.
    
    Uses Gemini 2.5 Flash for fast, engaging Socratic-style teaching.
    Automatically determines streaming vs burst based on expected response length.
    
    Streaming Strategy:
    - Short responses (< 100 tokens): Burst mode (immediate full response)
    - Long responses (>= 100 tokens): Streaming mode (token by token)
    
    Args:
        state: Current graph state with lesson_plan and user_message
        
    Returns:
        Updated state with ai_response, updated chat_history, and streaming flag
    """
    logger.info(f"Tutoring session - Day {state['current_day']}, Topic {state['current_topic_index']}")
    
    user_message = state.get("user_message")
    
    # Classify expected response and determine streaming mode
    response_type = classify_expected_response(user_message)
    expected_tokens = estimate_response_tokens(response_type)
    use_streaming = should_stream(expected_tokens)
    
    logger.info(f"Response type: {response_type}, Expected tokens: {expected_tokens}, Streaming: {use_streaming}")
    
    # Get LLM with appropriate streaming setting
    llm = get_tutor_llm(temperature=0.7, streaming=use_streaming)
    
    lesson_plan = state["lesson_plan"]
    current_day = state["current_day"]
    current_topic_index = state["current_topic_index"]
    
    # Get current day's content
    day_content = _get_day_content(lesson_plan, current_day)
    current_topic = _get_current_topic(day_content, current_topic_index)
    
    # Build system prompt with context
    mode = state.get("mode", "generation")
    target = state.get("target", "General understanding")
    
    if mode == "quick":
        from app.core.prompts import QUICK_TUTOR_SYSTEM_PROMPT
        system_prompt = QUICK_TUTOR_SYSTEM_PROMPT.format(
            topic=state["topic"],
            target=target,
            day_title=day_content.get("title", state["topic"]),
            day_objectives=", ".join(day_content.get("objectives", [])),
            current_topic=json.dumps(current_topic, indent=2) if current_topic else "Wrapping up the session",
            memory_summary=state.get("memory_summary") or "This is the start of the conversation.",
        )
    else:
        system_prompt = TUTOR_SYSTEM_PROMPT.format(
            topic=state["topic"],
            current_day=current_day,
            total_days=state["total_days"],
            day_title=day_content.get("title", f"Day {current_day}"),
            day_objectives=", ".join(day_content.get("objectives", [])),
            current_topic=json.dumps(current_topic, indent=2) if current_topic else "Wrapping up the day",
            memory_summary=state.get("memory_summary") or "This is the start of the conversation.",
            goal=target or "Master the topic thoroughly",
        )
    
    # Build messages
    messages = [SystemMessage(content=system_prompt)]
    
    # Add recent chat history (last 10 exchanges for context)
    for msg in state["chat_history"][-20:]:
        messages.append(msg)
    
    # Handle first message of a session vs continuation
    user_message = state.get("user_message")
    if user_message:
        messages.append(HumanMessage(content=user_message))
    else:
        # First message - prompt tutor to introduce the day
        first_topic = _get_current_topic(day_content, 0)
        intro_prompt = TUTOR_FIRST_MESSAGE_PROMPT.format(
            current_day=current_day,
            first_topic=json.dumps(first_topic, indent=2) if first_topic else "the day's content"
        )
        messages.append(HumanMessage(content=intro_prompt))
    
    try:
        # Handle streaming vs burst response
        if use_streaming:
            # Streaming mode - collect chunks
            ai_response = ""
            async for chunk in llm.astream(messages):
                if chunk.content:
                    ai_response += chunk.content
        else:
            # Burst mode - immediate full response
            response = await llm.ainvoke(messages)
            ai_response = response.content
        
        # Update chat history
        new_history = list(state["chat_history"])
        if user_message:
            new_history.append(HumanMessage(content=user_message))
        new_history.append(AIMessage(content=ai_response))
        
        # No automatic advancement - user controls day navigation manually
        
        return {
            "ai_response": ai_response,
            "chat_history": new_history,
            "should_advance_topic": False,
            "is_day_complete": False,
            "is_course_complete": False,
            "used_streaming": use_streaming,
        }
        
    except Exception as e:
        logger.error(f"Tutor error: {str(e)}")
        return {
            "ai_response": f"I'm having a moment of confusion. Could you repeat that? (Error: {str(e)})",
            "chat_history": state["chat_history"],
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _parse_json_response(content: str) -> Dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    # Try direct parse first
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code blocks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    return json.loads(content.strip())


def _create_welcome_message(topic: str, lesson_plan: Dict[str, Any]) -> str:
    """Create a welcome message after plan generation."""
    days = lesson_plan.get("days", [])
    total_days = len(days)
    
    if total_days == 0:
        return f"I've prepared your learning plan for **{topic}**. Ready to begin?"
    
    day1 = days[0]
    day1_title = day1.get("title", "Day 1")
    day1_objectives = day1.get("objectives", [])
    
    message = f"""🎉 **Your personalized learning plan for "{topic}" is ready!**

📚 **Course Overview:**
- **Duration:** {total_days} days
- **Description:** {lesson_plan.get('description', 'A comprehensive learning journey')}

📅 **Day 1: {day1_title}**
"""
    
    if day1_objectives:
        message += "\n**Today's objectives:**\n"
        for obj in day1_objectives[:3]:
            message += f"• {obj}\n"
    
    message += "\n✨ **Ready to start Day 1?** Just say 'Let's begin!' or ask me any questions about the plan."
    
    return message


def _get_day_content(lesson_plan: Dict[str, Any], day: int) -> Dict[str, Any]:
    """Get content for a specific day from the lesson plan."""
    if not lesson_plan:
        return {}
    
    days = lesson_plan.get("days", [])
    if day <= 0 or day > len(days):
        return {}
    
    return days[day - 1]


def _get_current_topic(day_content: Dict[str, Any], topic_index: int) -> Dict[str, Any]:
    """Get the current topic from day content."""
    topics = day_content.get("topics", [])
    if topic_index < 0 or topic_index >= len(topics):
        return {}
    
    return topics[topic_index]


def _should_advance_topic(user_message: str, ai_response: str) -> bool:
    """
    Legacy placeholder - actual LLM-based advancement is done in chat_service.py.
    This function is kept for backwards compatibility but always returns False.
    
    The chat_service.py now uses Gemini 2.5 Flash for intelligent sentiment
    analysis to determine when a student is ready to advance topics.
    """
    return False


def _is_day_complete(day_content: Dict[str, Any], current_topic_index: int, advancing: bool) -> bool:
    """Check if all topics for the day have been covered."""
    topics = day_content.get("topics", [])
    if not topics:
        return True
    
    # If we're advancing and on the last topic
    if advancing and current_topic_index >= len(topics) - 1:
        return True
    
    return False
