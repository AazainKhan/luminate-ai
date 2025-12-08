"""
API routes for source description generation.

Uses Gemini 2.0 Flash-Lite to generate contextual descriptions for RAG sources.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.redis_client import get_redis_client
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sources", tags=["sources"])


class SourceDescriptionRequest(BaseModel):
    """Request model for generating source description"""
    query: str
    title: str
    content: str
    source_file: Optional[str] = None
    module: Optional[str] = None
    week: Optional[int] = None


class SourceDescriptionResponse(BaseModel):
    """Response model with generated description"""
    description: str


@router.post("/generate-description", response_model=SourceDescriptionResponse)
async def generate_source_description(request: SourceDescriptionRequest):
    """
    Generate a contextual description for a source citation using Gemini 2.0 Flash-Lite.
    
    The description is:
    - Query-aware: Explains relevance to the user's question
    - Concise: 1-2 sentences, no fluff
    - Contextual: Highlights key concepts from the content
    
    Example:
        Query: "What is backpropagation?"
        Content: "...chain rule...gradient descent...neural networks..."
        Description: "Explains how backpropagation uses the chain rule to compute 
                     gradients for updating neural network weights during training."
    """
    try:
        # Generate cache key based on query + title + content hash
        cache_input = f"{request.query}:{request.title}:{request.content[:500]}"
        cache_key = f"source_desc:{hashlib.md5(cache_input.encode()).hexdigest()}"
        
        # Try to get from Redis cache first
        redis_client = get_redis_client()
        cached_description = redis_client.get(cache_key)
        
        if cached_description:
            logger.info(f"Cache hit for source description: {request.title[:50]}...")
            return SourceDescriptionResponse(description=cached_description)
        
        logger.info(f"Cache miss, generating description for: {request.title[:50]}...")
        
        # Initialize Gemini 2.0 Flash-Lite (cost-efficient, low latency model)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",  # Optimized for cost efficiency and low latency
            temperature=0.3,  # Low temperature for consistent, factual descriptions
            google_api_key=settings.google_api_key,
        )
        
        # Build context-aware prompt
        context_parts = []
        if request.module:
            context_parts.append(f"Module: {request.module}")
        if request.week:
            context_parts.append(f"Week: {request.week}")
        if request.source_file:
            context_parts.append(f"Source: {request.source_file}")
        
        context_str = " | ".join(context_parts) if context_parts else "Course Material"
        
        prompt = f"""Generate a concise, query-relevant description (1-2 sentences) for this source citation.

User's Question: "{request.query}"

Source Title: {request.title}
Context: {context_str}

Source Content (excerpt):
{request.content[:800]}

Requirements:
- Explain how this content is relevant to the user's question
- Highlight key concepts or information from the excerpt
- Be specific and informative, not generic
- Keep it to 1-2 sentences (max 150 characters)
- Write in present tense, direct and clear
- Start directly with the key concept or explanation
- NEVER use phrases like:
  ❌ "This source discusses..."
  ❌ "This resource explains..."
  ❌ "For this topic..."
  ❌ "The source covers..."
  ✅ Instead, start with: "Explains...", "Covers...", "Demonstrates...", "Introduces..."

Examples of GOOD descriptions:
- "Explains how backpropagation uses the chain rule to compute gradients for updating neural network weights."
- "Demonstrates the difference between BFS and DFS with step-by-step examples."
- "Introduces the concept of activation functions and their role in non-linear transformations."

Description:"""
        
        # Generate description
        response = llm.invoke(prompt)
        description = response.content.strip()
        
        # Ensure it's not too long
        if len(description) > 200:
            description = description[:197] + "..."
        
        # Cache the description for 7 days (604800 seconds)
        redis_client.set(cache_key, description, ex=604800)
        
        logger.info(f"Generated and cached description for source: {request.title[:50]}...")
        
        return SourceDescriptionResponse(description=description)
        
    except Exception as e:
        logger.error(f"Error generating source description: {e}")
        # Fallback to truncated content if generation fails
        fallback = request.content[:150].strip()
        if len(request.content) > 150:
            fallback += "..."
        return SourceDescriptionResponse(description=fallback)
