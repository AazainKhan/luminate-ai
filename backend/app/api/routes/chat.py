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

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    parts: Optional[List[Dict[str, Any]]] = Field(default=None, description="Message parts for structured content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, description="List of chat messages")
    stream: bool = Field(default=True, description="Whether to stream the response")


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

        loop = asyncio.get_event_loop()
        try:
            # Run the blocking agent call in a thread pool
            result = await loop.run_in_executor(
                None,
                run_agent,
                user_message,
                user_info.get("user_id"),
                user_info.get("email")
            )

            # Extract response components
            response_text = result.get("response", "")
            reasoning = result.get("reasoning", [])
            sources = result.get("sources", [])
            
            # Stream reasoning if available
            if reasoning:
                reasoning_text = "\n".join([f"{step.get('step', '')}: {step.get('details', '')}" for step in reasoning])
                yield f'data: {json.dumps({"type": "reasoning-delta", "reasoningDelta": reasoning_text})}\n\n'
            
            # Stream main response text in chunks
            if response_text:
                logger.info(f"Agent generated response: '{response_text[:100]}...'")
                # Simulate streaming by chunking the response
                chunk_size = 10  # words per chunk
                words = response_text.split()
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i + chunk_size])
                    if i + chunk_size < len(words):
                        chunk += " "
                    yield f'data: {json.dumps({"type": "text-delta", "textDelta": chunk})}\n\n'
                    await asyncio.sleep(0.05)  # Small delay for smooth streaming
                
                # Stream sources if available
                if sources:
                    yield f'data: {json.dumps({"type": "sources", "sources": sources})}\n\n'
            else:
                error_msg = result.get("error", "I apologize, but I couldn't generate a response.")
                logger.error(f"Agent returned an error or no response: {error_msg}")
                yield f'data: {json.dumps({"type": "text-delta", "textDelta": error_msg})}\n\n'

            # Signal completion
            yield f'data: {json.dumps({"type": "finish"})}\n\n'

        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            error_message = "An unexpected error occurred while processing your request."
            yield f'data: {json.dumps({"type": "text-delta", "textDelta": error_message})}\n\n'
            yield f'data: {json.dumps({"type": "finish"})}\n\n'

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

