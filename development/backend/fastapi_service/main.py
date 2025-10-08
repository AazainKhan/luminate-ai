"""
FastAPI Navigate Endpoint for Luminate AI
Purpose: Provide semantic search API for COMP237 course content

Features:
- POST /query/navigate - Semantic search with ChromaDB
- GET /health - Health check endpoint
- CORS enabled for Chrome extension
- Request/response logging
- Configurable filters and thresholds
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path
import logging
from contextlib import asynccontextmanager
import time

# Import enhanced middleware
from middleware import cache, rate_limiter, metrics, validator

# Add parent directories to path for imports
project_root = Path(__file__).parent.parent.parent.parent
backend_dir = project_root / "development" / "backend"
sys.path.insert(0, str(backend_dir))

from setup_chromadb import LuminateChromaDB, CHROMA_DB_PATH

# Import LangGraph navigate workflow
langgraph_dir = backend_dir / "langgraph"
sys.path.insert(0, str(langgraph_dir))
from navigate_graph import build_navigate_graph

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "fastapi_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global ChromaDB instance
chroma_db = None

# Global LangGraph workflow
navigate_workflow = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI - initialize ChromaDB on startup"""
    global chroma_db, navigate_workflow
    
    logger.info("🚀 Starting Luminate AI FastAPI service...")
    
    try:
        # Initialize ChromaDB
        chroma_db = LuminateChromaDB(persist_directory=CHROMA_DB_PATH)
        doc_count = chroma_db.collection.count()
        logger.info(f"✓ ChromaDB loaded with {doc_count} documents")
        
        if doc_count == 0:
            logger.warning("⚠️  ChromaDB collection is empty! Run setup_chromadb.py first.")
        
        # Initialize LangGraph Navigate workflow
        navigate_workflow = build_navigate_graph()
        logger.info("✓ LangGraph Navigate workflow initialized")
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise
    
    yield
    
    # Cleanup (if needed)
    logger.info("🛑 Shutting down Luminate AI FastAPI service...")


# Initialize FastAPI app
app = FastAPI(
    title="Luminate AI Navigate API",
    description="Semantic search API for COMP237 course content",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",
        "http://localhost:*",
        "http://127.0.0.1:*",
        "https://luminate.centennialcollege.ca"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class NavigateRequest(BaseModel):
    """Navigate mode search request"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    n_results: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score (0-1)")
    module_filter: Optional[str] = Field(default=None, description="Filter by module name")
    content_type_filter: Optional[str] = Field(default=None, description="Filter by content type")
    include_no_url: bool = Field(default=False, description="Include results without BB URLs")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning algorithms",
                "n_results": 10,
                "min_score": 0.5,
                "module_filter": "Root",
                "content_type_filter": None,
                "include_no_url": False
            }
        }


class SearchResult(BaseModel):
    """Single search result"""
    title: str
    excerpt: str = Field(..., description="Text snippet (150 chars)")
    score: float = Field(..., description="Similarity score (lower is better)")
    live_url: Optional[str] = Field(default=None, description="Blackboard URL")
    module: str
    bb_doc_id: Optional[str] = None
    content_type: str
    chunk_index: int
    total_chunks: int
    tags: List[str] = []


class NavigateResponse(BaseModel):
    """Navigate mode search response"""
    query: str
    results: List[SearchResult]
    total_results: int
    execution_time_ms: float
    timestamp: str


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "Luminate AI Navigate API",
        "version": "1.0.0",
        "course": "COMP237",
        "endpoints": {
            "navigate": "/query/navigate",
            "health": "/health",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if chroma_db is None:
        raise HTTPException(status_code=503, detail="ChromaDB not initialized")
    
    try:
        doc_count = chroma_db.collection.count()
        return {
            "status": "healthy",
            "chromadb_documents": doc_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get ChromaDB collection and API performance statistics"""
    if chroma_db is None:
        raise HTTPException(status_code=503, detail="ChromaDB not initialized")
    
    try:
        db_stats = chroma_db.get_stats()
        api_metrics = metrics.get_stats()
        
        return {
            "database": db_stats,
            "api_metrics": api_metrics,
            "cache_size": cache.size(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/query/navigate", response_model=NavigateResponse)
async def navigate_query(request: NavigateRequest, req: Request):
    """
    Navigate mode: Semantic search for course content
    
    Returns relevant course materials with Blackboard URLs for navigation.
    Uses ChromaDB for vector similarity search with caching and rate limiting.
    """
    start_time = datetime.now()
    client_ip = req.client.host if req.client else "unknown"
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        metrics.record_error("rate_limit_exceeded")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before making more requests."
        )
    
    # Validate and sanitize input
    sanitized_query = validator.sanitize_query(request.query)
    validated_n_results = validator.validate_n_results(request.n_results)
    validated_min_score = validator.validate_score(request.min_score)
    
    logger.info(f"Navigate query from {client_ip}: '{sanitized_query}' (n={validated_n_results})")
    
    # Check cache
    cache_key = {
        "query": sanitized_query,
        "n_results": validated_n_results,
        "min_score": validated_min_score,
        "module_filter": request.module_filter,
        "content_type_filter": request.content_type_filter,
        "include_no_url": request.include_no_url
    }
    
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info(f"Returning cached response for: '{sanitized_query}'")
        metrics.record_request("/query/navigate", 0, success=True)
        return NavigateResponse(**cached_response)
    
    if chroma_db is None:
        logger.error("ChromaDB not initialized")
        metrics.record_error("chromadb_unavailable")
        raise HTTPException(status_code=503, detail="Search service not available")
    
    try:
        # Build metadata filter
        where_filter = {}
        if request.module_filter:
            where_filter["module"] = request.module_filter
        if request.content_type_filter:
            where_filter["content_type"] = request.content_type_filter
        
        # Query ChromaDB
        chroma_results = chroma_db.query(
            query_text=sanitized_query,
            n_results=validated_n_results * 2,  # Fetch extra for filtering
            filter_metadata=where_filter if where_filter else None
        )
        
        # Process results
        results = []
        if chroma_results["documents"] and chroma_results["documents"][0]:
            for doc, meta, dist in zip(
                chroma_results["documents"][0],
                chroma_results["metadatas"][0],
                chroma_results["distances"][0]
            ):
                # Convert distance to score (lower distance = better match)
                # ChromaDB uses L2 distance; normalize for display
                score = dist
                
                # Apply score threshold
                if score > validated_min_score and validated_min_score > 0:
                    continue
                
                # Filter out results without URLs (unless explicitly allowed)
                live_url = meta.get("live_lms_url")
                if not request.include_no_url and not live_url:
                    continue
                
                # Extract tags
                tags_str = meta.get("tags", "")
                tags = tags_str.split(",") if tags_str else []
                
                # Create search result
                result = SearchResult(
                    title=meta.get("title", "Untitled"),
                    excerpt=doc[:150] + "..." if len(doc) > 150 else doc,
                    score=round(score, 4),
                    live_url=live_url,
                    module=meta.get("module", "Unknown"),
                    bb_doc_id=meta.get("bb_doc_id"),
                    content_type=meta.get("content_type", "unknown"),
                    chunk_index=meta.get("chunk_index", 0),
                    total_chunks=meta.get("total_chunks", 1),
                    tags=tags
                )
                results.append(result)
                
                # Stop if we have enough results
                if len(results) >= validated_n_results:
                    break
        
        # Calculate execution time
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(
            f"Navigate query completed: '{sanitized_query}' → "
            f"{len(results)} results in {execution_time_ms:.2f}ms"
        )
        
        # Build response
        response = NavigateResponse(
            query=sanitized_query,
            results=results,
            total_results=len(results),
            execution_time_ms=round(execution_time_ms, 2),
            timestamp=datetime.now().isoformat()
        )
        
        # Cache the response
        cache.set(cache_key, response.model_dump())
        
        # Record metrics
        metrics.record_request("/query/navigate", execution_time_ms, success=True)
        
        return response
    
    except Exception as e:
        logger.error(f"Navigate query failed: {e}", exc_info=True)
        metrics.record_request("/query/navigate", 0, success=False)
        metrics.record_error(type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# LangGraph Navigate Endpoint
class LangGraphNavigateRequest(BaseModel):
    """LangGraph Navigate Mode request"""
    query: str = Field(..., min_length=1, max_length=500, description="User question")


class LangGraphNavigateResponse(BaseModel):
    """LangGraph Navigate Mode response"""
    formatted_response: str
    top_results: List[Dict[str, Any]]
    related_topics: List[Dict[str, Any]]  # Changed from List[str] to List[Dict]
    external_resources: Optional[List[Dict[str, Any]]] = None  # NEW: External learning resources
    next_steps: Optional[List[str]] = None


@app.post("/langgraph/navigate", response_model=LangGraphNavigateResponse)
async def langgraph_navigate(request: LangGraphNavigateRequest, req: Request):
    """
    LangGraph Navigate Mode: Multi-agent workflow for course content search
    
    Uses 4 agents:
    1. Query Understanding - Expands and interprets user query
    2. Retrieval - Searches ChromaDB for relevant content
    3. Context - Adds related topics and module context
    4. Formatting - Structures output for Chrome extension
    """
    start_time = datetime.now()
    client_ip = req.client.host if req.client else "unknown"
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        metrics.record_error("rate_limit_exceeded")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before making more requests."
        )
    
    # Validate and sanitize input
    sanitized_query = validator.sanitize_query(request.query)
    
    logger.info(f"🤖 LangGraph Navigate query from {client_ip}: '{sanitized_query}'")
    
    # Check cache
    cache_key = {"query": sanitized_query, "endpoint": "langgraph"}
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info(f"Returning cached LangGraph response for: '{sanitized_query}'")
        metrics.record_request("/langgraph/navigate", 0, success=True)
        return LangGraphNavigateResponse(**cached_response)
    
    if navigate_workflow is None:
        logger.error("LangGraph workflow not initialized")
        metrics.record_error("langgraph_unavailable")
        raise HTTPException(status_code=503, detail="Navigate workflow not available")
    
    try:
        # Run the workflow with ChromaDB instance
        result = navigate_workflow.invoke({
            "query": sanitized_query,
            "chroma_db": chroma_db
        })
        
        # Extract formatted response (it's a dict from the formatting agent)
        formatted_data = result.get("formatted_response", {})
        
        # Handle case where formatted_response might be a string (shouldn't happen but defensive)
        if isinstance(formatted_data, str):
            formatted_data = {"message": formatted_data, "top_results": [], "related_topics": []}
        
        # Extract fields from formatted_data
        top_results = formatted_data.get("top_results", [])
        related_topics = formatted_data.get("related_topics", [])
        external_resources = formatted_data.get("external_resources", [])  # NEW: Extract external resources
        next_steps = formatted_data.get("suggested_next_step")
        
        # Get the answer (new field) or fallback to encouragement/message
        answer = formatted_data.get("answer", formatted_data.get("encouragement", "Here are the most relevant course materials for your query."))
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(
            f"✓ LangGraph Navigate completed in {execution_time_ms:.2f}ms: "
            f"{len(top_results)} results, {len(related_topics)} related topics"
        )
        
        response = LangGraphNavigateResponse(
            formatted_response=answer,
            top_results=top_results,
            related_topics=related_topics,
            external_resources=external_resources,  # NEW: Include external resources
            next_steps=[next_steps] if next_steps and isinstance(next_steps, str) else next_steps
        )
        
        # Cache the response
        cache.set(cache_key, response.model_dump())
        
        # Record metrics
        metrics.record_request("/langgraph/navigate", execution_time_ms, success=True)
        
        return response
    
    except Exception as e:
        logger.error(f"LangGraph Navigate failed: {e}", exc_info=True)
        metrics.record_request("/langgraph/navigate", 0, success=False)
        metrics.record_error(type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Navigate workflow failed: {str(e)}")


class ExternalResourcesRequest(BaseModel):
    """Request for external resources (lazy loading)"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")


class ExternalResourcesResponse(BaseModel):
    """Response with external learning resources"""
    resources: List[Dict[str, Any]]
    count: int


@app.post("/external-resources", response_model=ExternalResourcesResponse)
async def get_external_resources(request: ExternalResourcesRequest):
    """
    Lazy load external resources when user clicks "Load Additional Resources"
    
    Searches:
    - YouTube videos (3 direct links via API)
    - Wikipedia (1 direct article via API)
    - Khan Academy (1-2 curated direct content links)
    - MIT OCW (1 curated direct course link)
    - OER Commons (1 curated direct resource link)
    """
    start_time = datetime.now()
    
    logger.info(f"🔍 External resources request: '{request.query}'")
    
    try:
        # Import external resources functions
        from langgraph.agents.external_resources import (
            search_youtube,
            search_oer_commons,
            search_educational_resources,
            _enhance_query_for_ai_context
        )
        
        # Enhance query with AI/ML context for better matching
        enhanced_query = _enhance_query_for_ai_context(request.query)
        logger.info(f"  Enhanced query: '{enhanced_query}'")
        
        resources = []
        
        # Search YouTube (3 videos) - using enhanced query
        youtube_results = search_youtube(request.query, max_results=3)
        resources.extend(youtube_results)
        
        # Search educational resources (Wikipedia, Khan Academy, MIT OCW) - using enhanced query
        edu_results = search_educational_resources(request.query, max_results=10)
        resources.extend(edu_results)
        
        # Search OER Commons (1 resource) - search page
        oer_results = search_oer_commons(request.query, max_results=1)
        resources.extend(oer_results)
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(
            f"✓ External resources found in {execution_time_ms:.2f}ms: "
            f"{len(resources)} total resources "
            f"(YouTube: {len(youtube_results)}, Educational: {len(edu_results)}, OER: {len(oer_results)})"
        )
        
        metrics.record_request("/external-resources", execution_time_ms, success=True)
        
        return ExternalResourcesResponse(
            resources=resources,
            count=len(resources)
        )
    
    except Exception as e:
        logger.error(f"External resources search failed: {e}", exc_info=True)
        metrics.record_request("/external-resources", 0, success=False)
        metrics.record_error(type(e).__name__)
        raise HTTPException(status_code=500, detail=f"External resources search failed: {str(e)}")


# Conversation History Models
class ConversationMessage(BaseModel):
    """Single conversation message"""
    role: str = Field(..., description="user or assistant")
    content: str
    timestamp: str
    results: Optional[List[Dict[str, Any]]] = None
    related_topics: Optional[List[Dict[str, Any]]] = None


class SaveConversationRequest(BaseModel):
    """Request to save conversation history"""
    session_id: str = Field(..., description="Unique session identifier")
    messages: List[ConversationMessage]


class LoadConversationResponse(BaseModel):
    """Response with conversation history"""
    session_id: str
    messages: List[ConversationMessage]
    last_updated: str


# Simple in-memory conversation storage (could be Redis/DB in production)
conversation_store: Dict[str, Dict] = {}


@app.post("/conversation/save")
async def save_conversation(request: SaveConversationRequest):
    """
    Save conversation history for a session
    
    In production, this would be stored in Redis or a database.
    Currently using in-memory storage for simplicity.
    """
    try:
        conversation_store[request.session_id] = {
            "messages": [msg.model_dump() for msg in request.messages],
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"Saved conversation for session: {request.session_id} ({len(request.messages)} messages)")
        
        return {
            "success": True,
            "session_id": request.session_id,
            "message_count": len(request.messages),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save conversation: {str(e)}")


@app.get("/conversation/load/{session_id}", response_model=LoadConversationResponse)
async def load_conversation(session_id: str):
    """
    Load conversation history for a session
    
    Returns empty list if session not found.
    """
    try:
        if session_id not in conversation_store:
            logger.info(f"No conversation found for session: {session_id}")
            return LoadConversationResponse(
                session_id=session_id,
                messages=[],
                last_updated=datetime.now().isoformat()
            )
        
        data = conversation_store[session_id]
        messages = [ConversationMessage(**msg) for msg in data["messages"]]
        
        logger.info(f"Loaded conversation for session: {session_id} ({len(messages)} messages)")
        
        return LoadConversationResponse(
            session_id=session_id,
            messages=messages,
            last_updated=data["last_updated"]
        )
    
    except Exception as e:
        logger.error(f"Failed to load conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load conversation: {str(e)}")


@app.delete("/conversation/{session_id}")
async def delete_conversation(session_id: str):
    """Delete conversation history for a session"""
    try:
        if session_id in conversation_store:
            del conversation_store[session_id]
            logger.info(f"Deleted conversation for session: {session_id}")
            return {"success": True, "message": "Conversation deleted"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
