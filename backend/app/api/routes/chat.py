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
from supabase import create_client, Client

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Supabase client
supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get Supabase client for database operations"""
    global supabase_client
    if supabase_client is None:
        if not settings.supabase_service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY not configured")
        supabase_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return supabase_client

async def save_message(chat_id: str, role: str, content: str):
    """Save message to database"""
    if not chat_id: return
    try:
        supabase = get_supabase_client()
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        logger.error(f"Error saving message: {e}")

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

    # Save user message if chat_id is present
    if request.chat_id:
        await save_message(request.chat_id, "user", user_message)

    async def generate_stream():
        """
        Async generator that streams responses in AI SDK v5 format.
        Format: data: {"type":"text-delta","textDelta":"chunk"}\n\n
        """
        if not user_message:
            yield f'data: {json.dumps({"type": "finish"})}\n\n'
            return

        full_response = ""

        try:
            from app.agents.tutor_agent import astream_agent
            
            # Stream events from the agent
            async for event in astream_agent(
                user_message,
                user_info.get("user_id"),
                user_info.get("email"),
                request.session_id
            ):
                if event.get("type") == "text-delta":
                    full_response += event.get("textDelta", "")
                yield f'data: {json.dumps(event)}\n\n'

            # Save assistant message if chat_id is present
            if request.chat_id:
                await save_message(request.chat_id, "assistant", full_response)

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

