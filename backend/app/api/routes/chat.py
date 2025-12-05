"""
Chat API routes for streaming responses
"""
import logging
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio

from app.api.middleware import require_student
from app.agents.tutor_agent import run_agent
from app.observability import get_langfuse_client
from app.config import settings
from app.api.routes.history import (
    get_conversation_history,
    save_message_to_history,
    get_or_create_chat,
    update_chat_title_from_query
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def save_message(chat_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
    """Save message to database (wrapper for history service)"""
    await save_message_to_history(chat_id, role, content, metadata)

class ScoreRequest(BaseModel):
    trace_id: str = Field(..., description="Trace ID to attach score to")
    name: str = Field(..., description="Name of the score (e.g., 'user_feedback')")
    value: float = Field(..., description="Numeric value of the score")
    comment: Optional[str] = Field(None, description="Optional comment")
    observation_id: Optional[str] = Field(None, description="Optional observation ID")


@router.post("/feedback")
async def submit_feedback(
    request: ScoreRequest,
    user_info: dict = Depends(require_student),
):
    """
    Submit user feedback (score) for a chat response.
    """
    client = get_langfuse_client()
    if not client:
        logger.warning("Langfuse client not available, skipping feedback")
        return {"status": "skipped", "reason": "observability_disabled"}
        
    try:
        client.create_score(
            trace_id=request.trace_id,
            name=request.name,
            value=request.value,
            comment=request.comment,
            observation_id=request.observation_id
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")



class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    parts: Optional[List[Dict[str, Any]]] = Field(default=None, description="Message parts for structured content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, description="List of chat messages")
    stream: bool = Field(default=True, description="Whether to stream the response")
    session_id: Optional[str] = Field(default=None, description="Session ID for observability")
    chat_id: Optional[str] = Field(default=None, description="Chat ID for persistence")
    model: Optional[str] = Field(default=None, description="Model to use (e.g., 'gemini-2.0-flash', 'gpt-4.1-mini')")


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    user_info: dict = Depends(require_student),
):
    """
    Stream chat responses from the LangGraph agent using Vercel AI SDK format.
    Returns Server-Sent Events (SSE) compatible with AI SDK v5.
    """
    user_message = request.messages[-1].content if request.messages else ""
    user_id = user_info.get("user_id")
    user_email = user_info.get("email")
    logger.info(f"Received chat request for user {user_email}: '{user_message}'")

    # Get or create chat for persistence
    chat_id = request.chat_id
    if not chat_id:
        chat_id = await get_or_create_chat(user_id)
    
    # Load conversation history for agent context
    conversation_history = await get_conversation_history(chat_id, limit=10)
    
    # Save user message
    await save_message(chat_id, "user", user_message)
    
    # Auto-title chat from first query
    await update_chat_title_from_query(chat_id, user_message)

    async def generate_stream():
        """
        Async generator that streams responses in AI SDK v5 format.
        Format: data: {"type":"text-delta","textDelta":"chunk"}\n\n
        """
        if not user_message:
            yield f'data: {json.dumps({"type": "finish"})}\n\n'
            return

        full_response = ""
        trace_id = None
        queue_steps = []  # Collect queue steps for persistence
        sources = []  # Collect sources for persistence
        evaluation = None  # Collect evaluation for persistence

        try:
            from app.agents.tutor_agent import astream_agent
            
            # Use chat_id as session_id for Langfuse grouping if not provided
            effective_session_id = request.session_id or chat_id
            
            # Handle "auto" model selection by treating it as None (no override)
            model_to_use = request.model
            if model_to_use == "auto":
                model_to_use = None
            
            # Stream events from the agent with conversation history
            async for event in astream_agent(
                user_message,
                user_id,
                user_email,
                effective_session_id,
                chat_id=chat_id,
                conversation_history=conversation_history,
                model=model_to_use
            ):
                if event.get("type") == "text-delta":
                    full_response += event.get("textDelta", "")
                if event.get("type") == "trace-id":
                    trace_id = event.get("traceId")
                # Collect queue events for persistence in message metadata
                if event.get("type") == "queue-init":
                    queue_steps = event.get("queue", [])
                # Collect sources for persistence
                if event.get("type") == "sources":
                    sources = event.get("sources", [])
                # Collect evaluation for persistence
                if event.get("type") == "evaluation":
                    evaluation = event.get("evaluation")
                if event.get("type") == "queue-update":
                    # Update the status of the matching queue step
                    # Backend sends queueItemId, match it with step id
                    step_id = event.get("queueItemId") or event.get("stepId")
                    status = event.get("status")
                    for step in queue_steps:
                        if step.get("id") == step_id:
                            step["status"] = status
                            break
                yield f'data: {json.dumps(event)}\n\n'

            # Save assistant message with metadata including queue steps, sources, and evaluation
            metadata = {
                "trace_id": trace_id,
                "queue_steps": queue_steps,  # Persist chain of thought steps
                "sources": sources,  # Persist sources
                "evaluation": evaluation  # Persist evaluation scores
            }
            await save_message(chat_id, "assistant", full_response, metadata)

            # Signal completion with chat_id and trace_id for client reference
            yield f'data: {json.dumps({"type": "finish", "chatId": chat_id, "traceId": trace_id})}\n\n'

        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            error_msg = "An unexpected error occurred while processing your request."
            yield f'data: {json.dumps({"type": "error", "error": error_msg})}\n\n'

    # Return StreamingResponse with proper SSE headers
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/")
async def chat(
    request: ChatRequest,
    user_info: dict = Depends(require_student),
):
    """
    Non-streaming chat endpoint (for fallback)
    """
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Use /api/chat/stream for streaming responses",
        )
    
    user_message = request.messages[-1].content if request.messages else ""
    logger.info(f"Received non-streaming chat request: '{user_message}'")
    
    # This is a placeholder and should ideally also call the agent
    result = run_agent(user_message, user_info.get("user_id"), user_info.get("email"))
    
    return {
        "role": "assistant",
        "content": result.get("response", "This is a placeholder response."),
    }

