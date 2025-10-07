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

# Add parent directories to path for imports
project_root = Path(__file__).parent.parent.parent.parent
backend_dir = project_root / "development" / "backend"
sys.path.insert(0, str(backend_dir))

from setup_chromadb import LuminateChromaDB, CHROMA_DB_PATH

# Import LangGraph navigate workflow
langgraph_dir = backend_dir / "langgraph_workflows"
sys.path.insert(0, str(langgraph_dir))
from navigate_graph import build_navigate_graph
from educate_graph import build_educate_graph

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

# Global LangGraph workflows
navigate_workflow = None
educate_workflow = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI - initialize ChromaDB on startup"""
    global chroma_db, navigate_workflow, educate_workflow
    
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
        
        # Initialize LangGraph Educate workflow
        educate_workflow = build_educate_graph()
        logger.info("✓ LangGraph Educate workflow initialized")
    
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
        "service": "Luminate AI API",
        "version": "2.0.0",
        "course": "COMP237",
        "modes": {
            "navigate": "Find and navigate course content",
            "educate": "Adaptive tutoring and learning support"
        },
        "endpoints": {
            "navigate": "/langgraph/navigate",
            "educate": "/langgraph/educate",
            "health": "/health",
            "stats": "/stats",
            "external_resources": "/external-resources"
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
    """Get ChromaDB collection statistics"""
    if chroma_db is None:
        raise HTTPException(status_code=503, detail="ChromaDB not initialized")
    
    try:
        stats = chroma_db.get_stats()
        return {
            "stats": stats,
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
    Uses ChromaDB for vector similarity search.
    """
    start_time = datetime.now()
    client_ip = req.client.host if req.client else "unknown"
    
    logger.info(f"Navigate query from {client_ip}: '{request.query}' (n={request.n_results})")
    
    if chroma_db is None:
        logger.error("ChromaDB not initialized")
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
            query_text=request.query,
            n_results=request.n_results * 2,  # Fetch extra for filtering
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
                if score > request.min_score and request.min_score > 0:
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
                if len(results) >= request.n_results:
                    break
        
        # Calculate execution time
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(
            f"Navigate query completed: '{request.query}' → "
            f"{len(results)} results in {execution_time_ms:.2f}ms"
        )
        
        # Build response
        response = NavigateResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            execution_time_ms=round(execution_time_ms, 2),
            timestamp=datetime.now().isoformat()
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Navigate query failed: {e}", exc_info=True)
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
async def langgraph_navigate(request: LangGraphNavigateRequest):
    """
    LangGraph Navigate Mode: Multi-agent workflow for course content search
    
    Uses 4 agents:
    1. Query Understanding - Expands and interprets user query
    2. Retrieval - Searches ChromaDB for relevant content
    3. Context - Adds related topics and module context
    4. Formatting - Structures output for Chrome extension
    """
    start_time = datetime.now()
    
    logger.info(f"🤖 LangGraph Navigate query: '{request.query}'")
    
    if navigate_workflow is None:
        logger.error("LangGraph workflow not initialized")
        raise HTTPException(status_code=503, detail="Navigate workflow not available")
    
    try:
        # Run the workflow with ChromaDB instance
        result = navigate_workflow.invoke({
            "query": request.query,
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
        
        return LangGraphNavigateResponse(
            formatted_response=answer,
            top_results=top_results,
            related_topics=related_topics,
            external_resources=external_resources,  # NEW: Include external resources
            next_steps=[next_steps] if next_steps and isinstance(next_steps, str) else next_steps
        )
    
    except Exception as e:
        logger.error(f"LangGraph Navigate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Navigate workflow failed: {str(e)}")


class ExternalResourcesRequest(BaseModel):
    """Request for external resources (lazy loading)"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")


# LangGraph Educate Endpoint
class LangGraphEducateRequest(BaseModel):
    """LangGraph Educate Mode request"""
    query: str = Field(..., min_length=1, max_length=500, description="User question")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Previous conversation for context"
    )


class LangGraphEducateResponse(BaseModel):
    """LangGraph Educate Mode response"""
    response_type: str = Field(..., description="Type: concept, problem, clarification, assessment")
    main_content: str = Field(..., description="Primary response content")
    hints: Optional[Dict[str, Any]] = Field(default=None, description="Scaffolded hints for problems")
    socratic_questions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Guiding questions to help student learn"
    )
    sources: List[Dict[str, Any]] = Field(default=[], description="Course materials referenced")
    related_concepts: List[Dict[str, Any]] = Field(default=[], description="Related topics to explore")
    follow_up_suggestions: List[str] = Field(default=[], description="Suggested follow-up questions")
    misconception_alert: Optional[str] = Field(default=None, description="Detected misconception")
    assessment_questions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Practice questions"
    )
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


@app.post("/langgraph/educate", response_model=LangGraphEducateResponse)
async def langgraph_educate(request: LangGraphEducateRequest):
    """
    LangGraph Educate Mode: Multi-agent workflow for adaptive tutoring
    
    Uses multiple agents based on intent:
    1. Intent Classification - Determines what student needs (concept/problem/clarification/assessment)
    2. Retrieval - Searches ChromaDB for relevant content
    3. Specialized Agents:
       - Concept Explanation - Clear structured explanations
       - Problem Solving - Scaffolded hints (light → medium → full)
       - Clarification - Misconception detection and correction
       - Assessment - Practice question generation
    4. Socratic Agent - Guiding questions for deeper learning
    5. Formatting - Structures output for Chrome extension
    
    Based on educational AI research:
    - VanLehn (2011) - Intelligent Tutoring Systems
    - AutoTutor (Graesser et al., 2004) - Dialogue-based tutoring
    - Wood et al. (1976) - Scaffolding in learning
    """
    start_time = datetime.now()
    
    logger.info(f"🎓 LangGraph Educate query: '{request.query}'")
    
    if educate_workflow is None:
        logger.error("LangGraph Educate workflow not initialized")
        raise HTTPException(status_code=503, detail="Educate workflow not available")
    
    try:
        # Run the educate workflow
        result = educate_workflow.invoke({
            "query": request.query,
            "conversation_history": request.conversation_history or [],
            "chroma_db": chroma_db
        })
        
        # Extract formatted response
        formatted_data = result.get("formatted_response", {})
        
        # Handle case where formatted_response might be a string
        if isinstance(formatted_data, str):
            formatted_data = {
                "response_type": "concept",
                "main_content": formatted_data,
                "sources": [],
                "related_concepts": [],
                "follow_up_suggestions": []
            }
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log success with details
        intent = result.get("intent", "unknown")
        response_type = formatted_data.get("response_type", "unknown")
        has_socratic = len(formatted_data.get("socratic_questions", [])) > 0
        
        logger.info(
            f"✓ LangGraph Educate completed in {execution_time_ms:.2f}ms: "
            f"Intent={intent}, Type={response_type}, Socratic={has_socratic}"
        )
        
        # Build response
        return LangGraphEducateResponse(
            response_type=formatted_data.get("response_type", "concept"),
            main_content=formatted_data.get("main_content", "I'm having trouble generating a response. Please try rephrasing your question."),
            hints=formatted_data.get("hints"),
            socratic_questions=formatted_data.get("socratic_questions"),
            sources=formatted_data.get("sources", []),
            related_concepts=formatted_data.get("related_concepts", []),
            follow_up_suggestions=formatted_data.get("follow_up_suggestions", []),
            misconception_alert=formatted_data.get("misconception_alert"),
            assessment_questions=formatted_data.get("assessment_questions"),
            metadata={
                "intent": intent,
                "complexity_level": result.get("parsed_query", {}).get("complexity_level", "intermediate"),
                "execution_time_ms": round(execution_time_ms, 2),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        logger.error(f"LangGraph Educate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Educate workflow failed: {str(e)}")


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
        
        return ExternalResourcesResponse(
            resources=resources,
            count=len(resources)
        )
    
    except Exception as e:
        logger.error(f"External resources search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"External resources search failed: {str(e)}")


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
