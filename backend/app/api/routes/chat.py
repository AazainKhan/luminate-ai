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

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


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
    logger.info(f"Received chat request for user {user_info.get('email')}: '{user_message}'")

    async def generate_stream():
        """
        Async generator that streams responses in AI SDK v5 format.
        Format: data: {"type":"text-delta","textDelta":"chunk"}\n\n
        """
        if not user_message:
            yield f'data: {json.dumps({"type": "finish"})}\n\n'
            return

        try:
            from app.agents.tutor_agent import astream_agent
            
            # Stream events from the agent
            async for event in astream_agent(
                user_message,
                user_info.get("user_id"),
                user_info.get("email"),
                request.session_id
            ):
                yield f'data: {json.dumps(event)}\n\n'

            # Signal completion
            yield f'data: {json.dumps({"type": "finish"})}\n\n'

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

