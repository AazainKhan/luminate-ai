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
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, AsyncGenerator
from datetime import datetime
import sys
from pathlib import Path
import logging
from contextlib import asynccontextmanager
import json
import asyncio
import uuid
from nanoid import generate as nanoid

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

# Try to import enhanced middleware (if available from aazain branch)
try:
    from middleware import cache, rate_limiter, metrics, validator
    MIDDLEWARE_AVAILABLE = True
    logger.info("✓ Enhanced middleware loaded")
except ImportError:
    MIDDLEWARE_AVAILABLE = False
    logger.info("ℹ️ Enhanced middleware not available (optional)")

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
        
        # Store in app state for dependency injection
        app.state.chroma_db = chroma_db
        app.state.navigate_workflow = navigate_workflow
    
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

# Include routers (import after app is created)
try:
    # Add routers directory to path for proper import resolution
    routers_dir = Path(__file__).parent / "routers"
    if routers_dir.exists():
        sys.path.insert(0, str(routers_dir.parent))
        from fastapi_service.routers import auto
        app.include_router(auto.router, tags=["Auto Mode"])
        logger.info("✓ Auto mode router loaded")
    else:
        logger.warning(f"Routers directory not found at: {routers_dir}")
except ImportError as e:
    logger.warning(f"Could not import auto router: {e}")


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
            n_results=request.n_results * 3,  # Fetch extra for filtering (increased to account for csfiles exclusion)
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
                # Skip csfiles and other system/navigation files
                module = meta.get("module", "")
                if module.lower() in ["csfiles", "system", "navigation", "__internals"]:
                    logger.debug(f"Skipping system module: {module}")
                    continue
                
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


# ============================================================================
# UNIFIED QUERY ENDPOINT (Dual-Mode with Orchestrator)
# ============================================================================

class UnifiedQueryRequest(BaseModel):
    """Unified query request for both Navigate and Educate modes"""
    query: str = Field(..., min_length=1, max_length=500, description="User query")
    student_id: Optional[str] = Field(default=None, description="Student fingerprint ID")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "explain gradient descent",
                "student_id": "fingerprint-12345",
                "session_id": "session-abc-123"
            }
        }


class UnifiedQueryResponse(BaseModel):
    """
    Unified response from orchestrator.
    
    Frontend UI Components Map:
    - mode: Shows mode indicator badge
    - confidence: Used for confidence percentage display
    - reasoning: Displayed in ReasoningTrigger/ReasoningContent
    - response.formatted_response: Main content in Response component
    - response.top_results: Displayed in Sources component (Navigate)
    - response.related_topics: Displayed as clickable Suggestions
    - response.external_resources: Displayed in ExternalResources component
    - response.quiz_suggestion: Triggers QuizDialog
    - response.math_translation: 4-level explanation (Educate)
    - response.next_steps: Action suggestions
    """
    mode: Literal["navigate", "educate"]
    confidence: float = Field(..., description="Confidence in mode selection (0-1)")
    reasoning: str = Field(..., description="Why this mode was selected")
    response: Dict[str, Any] = Field(..., description="Mode-specific response data")
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "educate",
                "confidence": 0.95,
                "reasoning": "Query contains 'explain' and references COMP-237 core topic 'gradient descent'",
                "response": {
                    "formatted_response": "## Gradient Descent Explained\n\n...",
                    "math_translation": {
                        "level_1_intuition": "...",
                        "level_2_mathematical": "...",
                        "level_3_code": "...",
                        "level_4_misconceptions": "..."
                    },
                    "quiz_suggestion": {
                        "topic": "Gradient Descent",
                        "difficulty": "medium",
                        "question_count": 5
                    },
                    "next_steps": ["Practice with code", "Try variations"]
                },
                "timestamp": "2025-10-07T12:34:56Z"
            }
        }


@app.post("/api/query", response_model=UnifiedQueryResponse)
async def unified_query(request: UnifiedQueryRequest):
    """
    Unified query endpoint that routes to Navigate or Educate mode using orchestrator.
    
    **Workflow:**
    1. Orchestrator analyzes query intent
    2. Routes to Navigate (Gemini 2.0 Flash) or Educate (Gemini 2.5 Flash)
    3. Returns mode-specific response
    
    **Navigate Mode:** Fast retrieval, external resources, quick answers
    **Educate Mode:** Deep explanations, math translation, scaffolded learning
    """
    start_time = datetime.now()
    logger.info(f"📨 Unified query request: '{request.query[:50]}...'")
    
    try:
        # Import orchestrator
        import sys
        from pathlib import Path
        langgraph_path = Path(__file__).parent.parent / "langgraph"
        if str(langgraph_path) not in sys.path:
            sys.path.insert(0, str(langgraph_path))
        
        from orchestrator import classify_mode, OrchestratorState
        
        # Step 1: Orchestrator classification
        orchestrator_state = OrchestratorState(
            query=request.query,
            student_id=request.student_id or "anonymous",
            session_id=request.session_id or f"session-{int(datetime.now().timestamp())}",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={}
        )
        
        result_state = classify_mode(orchestrator_state)
        mode = result_state['mode']
        confidence = result_state['confidence']
        reasoning = result_state['reasoning']
        
        logger.info(f"🎯 Orchestrator: {mode} ({confidence:.2f}) - {reasoning}")
        
        # Step 2: Route to appropriate pipeline
        if mode == "navigate":
            # NAVIGATE MODE: Full workflow with ChromaDB + External Resources
            logger.info("🧭 Using Navigate mode workflow")
            
            # Use the proven /langgraph/navigate endpoint logic
            if navigate_workflow is None:
                logger.error("Navigate workflow not initialized")
                # Fallback to direct ChromaDB
                raise Exception("Navigate workflow not available")
            
            # Execute full workflow
            workflow_result = navigate_workflow.invoke({
                "query": request.query,
                "chroma_db": chroma_db
            })
            
            # Extract formatted response
            formatted_data = workflow_result.get("formatted_response", {})
            if isinstance(formatted_data, str):
                formatted_data = {"answer": formatted_data, "top_results": [], "related_topics": []}
            
            # Format top_results for Sources UI component (expects: title, excerpt, live_url, module, relevance_explanation)
            top_results = formatted_data.get("top_results", [])
            formatted_results = []
            for result in top_results:
                formatted_results.append({
                    'title': result.get('title', 'Untitled'),
                    'excerpt': result.get('excerpt', result.get('content', ''))[:200],  # Limit to 200 chars for UI
                    'live_url': result.get('url') or result.get('live_url') or result.get('bb_url'),
                    'module': result.get('module', result.get('module_name', 'Unknown Module')),
                    'relevance_explanation': result.get('relevance_explanation', 'Relevant course material'),
                    'content_type': result.get('content_type', 'document')
                })
            
            # Format related_topics for Suggestion UI component (expects: title, why_explore)
            related_topics = formatted_data.get("related_topics", [])
            formatted_topics = []
            for topic in related_topics:
                if isinstance(topic, str):
                    formatted_topics.append({
                        'title': topic,
                        'why_explore': f'Learn more about {topic}'
                    })
                else:
                    formatted_topics.append({
                        'title': topic.get('title', 'Unknown Topic'),
                        'why_explore': topic.get('why_explore', 'Related concept worth exploring')
                    })
            
            # Format external resources if present
            external_resources = formatted_data.get("external_resources", [])
            
            # Detect if quiz suggestion is appropriate
            quiz_keywords = ['test', 'quiz', 'practice', 'assess', 'check understanding', 'evaluate']
            should_suggest_quiz = any(keyword in request.query.lower() for keyword in quiz_keywords)
            
            # Extract main topic for quiz
            main_topic = None
            if formatted_results:
                main_topic = formatted_results[0]['title']
            elif formatted_topics:
                main_topic = formatted_topics[0]['title']
            
            response_data = {
                "formatted_response": formatted_data.get("answer", formatted_data.get("encouragement", "Here are relevant materials.")),
                "top_results": formatted_results,
                "related_topics": formatted_topics,
                "external_resources": external_resources,
                "total_results": len(formatted_results),
            }
            
            # Add quiz suggestion if appropriate
            if (should_suggest_quiz or len(formatted_results) >= 3) and main_topic:
                response_data['quiz_suggestion'] = {
                    'topic': main_topic,
                    'difficulty': 'medium',
                    'question_count': 5,
                    'prompt': f'💡 Test your knowledge of {main_topic}'
                }
            
            logger.info(f"✓ Navigate: {len(response_data['top_results'])} results, {len(response_data['related_topics'])} topics")
            
        else:  # educate mode
            # EDUCATE MODE: Use the Educate StateGraph (math translation first, then RAG)
            logger.info("🎓 Using Educate mode (LangGraph)")
            try:
                from langgraph.educate_graph import query_educate_mode

                workflow_result = query_educate_mode(request.query, chroma_db=chroma_db)
                formatted = workflow_result.get('formatted_response', {})

                # If math translation produced answer_markdown, return that directly
                if isinstance(formatted, dict) and formatted.get('answer_markdown'):
                    # 4-level translation response
                    response_data = {
                        'formatted_response': formatted['answer_markdown'],
                        'level': '4-level-translation',
                        'math_translation': {
                            'available': True,
                            'levels': ['intuition', 'mathematical', 'code', 'misconceptions']
                        },
                        'misconceptions_detected': [],
                        'next_steps': [
                            '💻 Try implementing the code',
                            '🔄 Practice with variations',
                            '📊 Compare different approaches'
                        ]
                    }
                    
                    # Extract topic for quiz suggestion
                    topic_match = request.query.lower()
                    main_keywords = [w for w in topic_match.split() if len(w) > 4]
                    if main_keywords:
                        main_topic = ' '.join(main_keywords[:3]).title()
                        response_data['quiz_suggestion'] = {
                            'topic': main_topic,
                            'difficulty': 'medium',
                            'question_count': 5,
                            'prompt': f'🎯 Ready to test your understanding of {main_topic}?'
                        }
                        
                else:
                    # Fallback to the existing RAG-conceptual path if graph returned conceptual formatted_response
                    if isinstance(formatted, str):
                        response_data = {
                            'formatted_response': formatted,
                            'level': 'conceptual',
                            'misconceptions_detected': [],
                            'next_steps': [
                                '📚 Review the course materials',
                                '🧮 Practice related problems',
                                '💬 Ask follow-up questions'
                            ]
                        }
                    else:
                        # If formatting agent returned a dict
                        response_data = {
                            'formatted_response': formatted.get('answer', ''),
                            'top_results': formatted.get('top_results', []),
                            'related_topics': formatted.get('related_topics', []),
                            'level': 'conceptual',
                            'misconceptions_detected': [],
                            'next_steps': [
                                '📚 Review the course materials',
                                '🧮 Practice related problems',
                                '💬 Ask follow-up questions'
                            ]
                        }
                    
                    # Add quiz suggestion for conceptual responses too
                    topic_words = request.query.split()[:5]
                    main_topic = ' '.join([w for w in topic_words if len(w) > 3]).title()
                    if main_topic:
                        response_data['quiz_suggestion'] = {
                            'topic': main_topic,
                            'difficulty': 'easy',
                            'question_count': 3,
                            'prompt': f'📝 Test your understanding of {main_topic}'
                        }

            except Exception as e:
                logger.exception(f"Educate workflow error: {e}")
                # Graceful fallback to simple RAG
                rag_raw_results = chroma_db.query(
                    query_text=request.query,
                    n_results=10,
                    filter_metadata=None
                )

                rag_results = []
                if rag_raw_results and 'documents' in rag_raw_results and len(rag_raw_results['documents'][0]) > 0:
                    for i, doc in enumerate(rag_raw_results['documents'][0]):
                        metadata = rag_raw_results['metadatas'][0][i] if 'metadatas' in rag_raw_results else {}
                        rag_results.append({
                            'content': doc,
                            'title': metadata.get('title', f'Document {i+1}'),
                            'module_name': metadata.get('module', 'Unknown'),
                            'chunk_index': metadata.get('chunk_index', 999),
                            'bb_url': metadata.get('bb_url', ''),
                            'score': 1.0 - rag_raw_results['distances'][0][i] if 'distances' in rag_raw_results else 0.0
                        })

                if rag_results:
                    explanation = _build_conceptual_explanation(request.query, rag_results)
                    response_data = {
                        'formatted_response': explanation,
                        'level': 'conceptual',
                        'context_sources': [r.get('title', 'Unknown') for r in rag_results[:3]],
                        'misconceptions_detected': [],
                        'next_steps': ['Review materials', 'Practice problems', 'Ask follow-ups']
                    }
                else:
                    response_data = {
                        "formatted_response": _mock_educate_response(request.query),
                        "level": "adaptive",
                        "misconceptions_detected": [],
                        "next_steps": ["Practice", "Code implementation"]
                    }
        
        return UnifiedQueryResponse(
            mode=mode,
            confidence=confidence,
            reasoning=reasoning,
            response=response_data,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"❌ Unified query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _mock_educate_response(query: str) -> str:
    """Mock educate mode response (will be replaced with real pipeline)"""
    query_lower = query.lower()
    
    if "gradient descent" in query_lower:
        return """## 📉 Gradient Descent Explained

### 🎯 Level 1: Intuition (5-year-old)
Imagine you're blindfolded on a hill and want to reach the bottom. You can't see, so you:
1. Feel the ground around you
2. Find which direction slopes down the most
3. Take a step in that direction
4. Repeat until you can't go any lower!

That's gradient descent - finding the lowest point by always stepping downhill.

### 📐 Level 2: Math Translation

**Formula:**

$$\\theta_{new} = \\theta_{old} - \\alpha \\nabla J(\\theta)$$

**What Each Symbol Means:**

- **θ (theta)**: Your current position on the hill (model parameters)
- **α (alpha)**: How big each step is (learning rate, usually 0.001-0.1)
- **∇J(θ)**: Which direction is downhill (slope of loss function)

### 💻 Level 3: Code Example
```python
# Starting position
theta = 5.0

# Learning rate
alpha = 0.01

# Repeat 1000 times
for i in range(1000):
    # Calculate which way is downhill
    gradient = compute_gradient(theta)
    
    # Take a step downhill
    theta = theta - alpha * gradient
    
    print(f"Step {i}: theta = {theta:.4f}")
```

### 🔍 Level 4: Common Misconception
❌ **WRONG:** "Bigger learning rate (α) = faster learning = better!"

✅ **CORRECT:** Too big → you overshoot and bounce around!
✅ **CORRECT:** Too small → takes forever to reach the bottom!

Think of α like step size when walking downhill:
- Giant leaps (α=1.0) → you jump past the valley!
- Tiny steps (α=0.0001) → takes 1000 years to get down!
- Goldilocks zone (α=0.01) → just right! ⭐
"""
    
    elif "backprop" in query_lower or "backpropagation" in query_lower:
        return r"""## 🔄 Backpropagation Explained

### Chain Rule in Action
Backpropagation uses the **chain rule** to calculate how much each weight contributed to the error.

**Formula:**

$$\frac{\partial L}{\partial w} = \frac{\partial L}{\partial a} \cdot \frac{\partial a}{\partial z} \cdot \frac{\partial z}{\partial w}$$

### PyTorch Example
```python
import torch

# Forward pass (automatic tracking)
x = torch.tensor([1.0, 2.0], requires_grad=True)
y = (x ** 2).sum()

# Backward pass (automatic!)
y.backward()

print(x.grad)  # [2.0, 4.0] - derivatives!
```
"""
    
    else:
        return f"""## 🎓 About "{query}"

**I'm currently in mock mode.** When the full Educate Mode pipeline is ready, I'll provide:

✅ 4-level explanations (Intuition → Math → Code → Misconceptions)
✅ Adaptive scaffolding based on your mastery level
✅ Interactive quizzes and practice problems
✅ Visual algorithm animations

**For now, try asking about:**
- **Gradient Descent** - Full 4-level explanation ready!
- **Backpropagation** - Chain rule breakdown with code!
"""


def _clean_content(text: str) -> str:
    """Remove XML artifacts and image placeholders while preserving markdown structure"""
    import re
    
    # Remove XML declarations and tags
    text = re.sub(r'<\?xml[^>]*\?>', '', text)
    text = re.sub(r'<lom[^>]*>.*?</lom>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove image placeholders
    text = re.sub(r'\b[A-Z0-9]+_[a-zA-Z0-9_]+\.(png|jpg|jpeg|gif|PNG|JPG|JPEG|GIF)\b', '', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove TOC-style header chains (e.g., "### Header1 ### Header2 ### Header3")
    # Match any line with 3+ consecutive headers
    text = re.sub(r'###[^#\n]+(?:###[^#\n]+){2,}', '', text)
    
    # Convert remaining headers to consistent level (### for h3)
    text = re.sub(r'#{4,6}\s+', '### ', text)
    
    # Split into lines and clean
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        cleaned_line = ' '.join(line.strip().split())
        
        if not cleaned_line:
            continue
        
        cleaned_lines.append(cleaned_line)
    
    # Join with paragraph breaks
    result = '\n\n'.join(cleaned_lines)
    
    # Clean up excess whitespace
    result = re.sub(r' +', ' ', result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()

def _build_conceptual_explanation(query: str, rag_results: List[Dict]) -> str:
    """Build clean, ChatGPT-style conceptual explanation from RAG results
    
    Strategy: Find chunk_index 0 from the most relevant document title,
    as it typically contains the complete structured content.
    """
    if not rag_results:
        return f"## {query.title()}\n\n*I don't have detailed information on this topic in the course materials.*\n\n"
    
    # Get top 10 chunks to have better chance of finding chunk 0
    top_chunks = rag_results[:10]
    
    # Find the most relevant document title (from first result)
    primary_title = rag_results[0].get("title", "Unknown")
    
    # Look for chunk_index 0 from the primary document
    chunk_zero = None
    for result in top_chunks:
        if result.get("title") == primary_title and result.get("chunk_index") == 0:
            chunk_zero = result
            break
    
    # If we found chunk 0, use it as primary
    if chunk_zero:
        content = _clean_content(chunk_zero.get("content", ""))
        if content and len(content) > 100:
            primary = content[:2000] if len(content) > 2000 else content
            explanation = f"## {query.title()}\n\n{primary}\n\n"
            
            # Add context from other relevant chunks
            for result in rag_results[:5]:
                if result.get("title") != primary_title:
                    context = _clean_content(result.get("content", ""))
                    if context and len(context) > 100:
                        context_snippet = context[:600]
                        if context_snippet[:80] not in primary:
                            explanation += f"### Related Concepts\n\n{context_snippet}\n\n"
                        break
            
            # Add sources
            explanation += "### Sources\n\n"
            sources_seen = set()
            for i, result in enumerate(rag_results[:3], 1):
                title = result.get("title", "Unknown")
                module = result.get("module_name", "Unknown")
                if title not in sources_seen and title != "Untitled":
                    sources_seen.add(title)
                    explanation += f"{i}. **{title}** ({module})\n"
            
            return explanation
    
    # Fallback: use regular ranking if chunk 0 not found
    fallback_content = []
    for result in rag_results[:5]:
        content = _clean_content(result.get("content", ""))
        if content and len(content) > 100:
            fallback_content.append({
                "text": content,
                "starts_properly": content[0].isupper(),
                "title": result.get("title", "Unknown")
            })
    
    if not fallback_content:
        return f"## {query.title()}\n\n*I don't have detailed information on this topic in the course materials.*\n\n"
    
    # Use the first properly-starting chunk
    fallback_content.sort(key=lambda x: not x["starts_properly"])
    primary = fallback_content[0]["text"][:2000]
    
    explanation = f"## {query.title()}\n\n{primary}\n\n"
    
    # Add sources
    explanation += "### Sources\n\n"
    for i, result in enumerate(rag_results[:2], 1):
        title = result.get("title", "Unknown")
        module = result.get("module_name", "Unknown")
        if title != "Untitled":
            explanation += f"{i}. **{title}** ({module})\n"
    
    return explanation


# ============================================================================
# STREAMING CHAT ENDPOINTS (AI SDK Compatible)
# ============================================================================

class StreamChatMessage(BaseModel):
    """Message in chat stream"""
    role: Literal["user", "assistant", "system"]
    content: str
    id: Optional[str] = None

class StreamChatRequest(BaseModel):
    """Streaming chat request"""
    messages: List[StreamChatMessage]
    mode: Literal["navigate", "educate"] = "navigate"
    student_id: Optional[str] = None
    session_id: Optional[str] = None

async def stream_navigate_response(query: str, student_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Stream Navigate mode response with real-time agent traces.
    
    Stream event types:
    - message_start: Begin response
    - agent_trace: Show agent execution step (in_progress/completed)
    - text_delta: Incremental text content
    - metadata: Sources, topics, resources
    - message_done: Complete response
    - error: Error occurred
    """
    message_id = nanoid()
    trace_queue = []
    
    try:
        # Send initial message start
        yield f"data: {json.dumps({'type': 'message_start', 'id': message_id})}\n\n"
        
        # Trace callback to collect agent execution
        def trace_callback(trace_data: dict):
            trace_queue.append(trace_data)
        
        # Execute navigate workflow with trace callback
        result = navigate_workflow.invoke({
            "query": query,
            "chroma_db": chroma_db,
            "trace_callback": trace_callback
        })
        
        # Send all collected traces
        for trace_data in trace_queue:
            yield f"data: {json.dumps({'type': 'agent_trace', 'data': trace_data})}\n\n"
            await asyncio.sleep(0.1)
        
        # Get formatted response
        formatted_response = result.get("formatted_response", {})
        response_text = formatted_response.get("formatted_response", "") if isinstance(formatted_response, dict) else str(formatted_response)
        
        # Extract top_results and external_resources from the result
        top_results = formatted_response.get("top_results", []) if isinstance(formatted_response, dict) else []
        external_resources = result.get("external_resources", [])
        
        # Stream text in chunks
        chunk_size = 50
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i+chunk_size]
            yield f"data: {json.dumps({'type': 'text_delta', 'delta': chunk})}\n\n"
            await asyncio.sleep(0.05)
        
        # Send metadata (sources, related topics) - formatted for UI components
        metadata = {
            "top_results": top_results,
            "related_topics": formatted_response.get("related_topics", []) if isinstance(formatted_response, dict) else [],
            "external_resources": external_resources
        }
        yield f"data: {json.dumps({'type': 'metadata', 'data': metadata})}\n\n"
        
        # Send completion
        yield f"data: {json.dumps({'type': 'message_done', 'id': message_id})}\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

async def stream_educate_response(query: str, student_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Stream Educate mode response with agent traces.
    
    Shows educational workflow steps:
    - Math translation attempt
    - Context retrieval
    - Scaffolding analysis
    - Response formatting
    """
    message_id = nanoid()
    
    try:
        # Send initial message start
        yield f"data: {json.dumps({'type': 'message_start', 'id': message_id})}\n\n"
        
        # Send math translation check trace
        query_lower = query.lower()
        math_keywords = ['explain', 'formula', 'equation', 'algorithm', 'how does']
        is_math_query = any(keyword in query_lower for keyword in math_keywords)
        
        if is_math_query:
            yield f"data: {json.dumps({'type': 'agent_trace', 'data': {{'agent': 'math_translation', 'action': 'Checking for math concepts', 'timestamp': datetime.now().isoformat()}}})}\n\n"
            await asyncio.sleep(0.1)
        
        # Send retrieval trace
        yield f"data: {json.dumps({'type': 'agent_trace', 'data': {{'agent': 'retrieval', 'action': 'Gathering context from course materials', 'timestamp': datetime.now().isoformat()}}})}\n\n"
        await asyncio.sleep(0.1)
        
        # Get RAG results from ChromaDB
        rag_results = chroma_db.query(query, n_results=5)
        
        # Convert ChromaDB results
        results_list = []
        if rag_results and rag_results.get("ids"):
            for idx in range(len(rag_results["ids"][0])):
                results_list.append({
                    "document": rag_results["documents"][0][idx],
                    "metadata": rag_results["metadatas"][0][idx],
                    "score": 1.0 - (rag_results["distances"][0][idx] if "distances" in rag_results else 0.5)
                })
        
        # Send context analysis trace
        yield f"data: {json.dumps({'type': 'agent_trace', 'data': {{'agent': 'context', 'action': 'Analyzing relevant content', 'count': len(results_list), 'timestamp': datetime.now().isoformat()}}})}\n\n"
        await asyncio.sleep(0.1)
        
        # Send scaffolding trace (adaptive learning level)
        yield f"data: {json.dumps({'type': 'agent_trace', 'data': {{'agent': 'scaffolding', 'action': 'Adapting explanation level', 'timestamp': datetime.now().isoformat()}}})}\n\n"
        await asyncio.sleep(0.1)
        
        # Send formatting trace
        yield f"data: {json.dumps({'type': 'agent_trace', 'data': {{'agent': 'formatting', 'action': 'Building conceptual explanation', 'timestamp': datetime.now().isoformat()}}})}\n\n"
        await asyncio.sleep(0.1)
        
        # Build response (use the proper _build_conceptual_explanation with RAG results)
        response_text = _build_conceptual_explanation(query, results_list)
        
        # Stream text in chunks
        chunk_size = 50
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i+chunk_size]
            yield f"data: {json.dumps({'type': 'text_delta', 'delta': chunk})}\n\n"
            await asyncio.sleep(0.05)
        
        # Send metadata with quiz suggestion
        main_topic = query.split()[:3]
        main_topic = ' '.join([w for w in main_topic if len(w) > 3]).title()
        
        metadata = {
            "quiz_suggestion": {
                "topic": main_topic if main_topic else query[:30],
                "difficulty": "easy",
                "question_count": 3,
                "prompt": f"📝 Test your understanding of {main_topic}"
            } if main_topic else None,
            "next_steps": [
                "📚 Review the course materials",
                "🧮 Practice related problems",
                "💬 Ask follow-up questions"
            ]
        }
        yield f"data: {json.dumps({'type': 'metadata', 'data': metadata})}\n\n"
        
        # Send completion
        yield f"data: {json.dumps({'type': 'message_done', 'id': message_id})}\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

@app.post("/api/chat/navigate")
async def stream_navigate_chat(request: StreamChatRequest):
    """Stream Navigate mode chat responses (AI SDK compatible)"""
    try:
        # Get the last user message
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        query = user_messages[-1].content
        
        return StreamingResponse(
            stream_navigate_response(query, request.student_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Stream navigate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/educate")
async def stream_educate_chat(request: StreamChatRequest):
    """Stream Educate mode chat responses (AI SDK compatible)"""
    try:
        # Get the last user message
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        query = user_messages[-1].content
        
        return StreamingResponse(
            stream_educate_response(query, request.student_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Stream educate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUIZ GENERATION & SUBMISSION ENDPOINTS
# ============================================================================

class QuizGenerateRequest(BaseModel):
    """Quiz generation request"""
    topic: str = Field(..., min_length=1, max_length=200)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    count: int = Field(default=5, ge=1, le=10)

class QuizOption(BaseModel):
    """Quiz option"""
    id: str
    text: str

class QuizQuestion(BaseModel):
    """Quiz question"""
    id: str
    prompt: str
    options: List[QuizOption]
    correct_answer: str
    explanation: str

class QuizGenerateResponse(BaseModel):
    """Quiz generation response"""
    quiz_id: str
    questions: List[QuizQuestion]
    topic: str
    difficulty: str

@app.post("/api/quiz/generate", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest):
    """Generate MCQ quiz based on topic"""
    try:
        # Get context from ChromaDB
        rag_results = chroma_db.query(request.topic, n_results=3)
        
        context = ""
        if rag_results and rag_results.get("documents"):
            context = "\n".join(rag_results["documents"][0][:3])
        
        # Use LLM to generate quiz
        from langgraph.llm_config import get_llm
        llm = get_llm(temperature=0.7, mode="educate")
        
        prompt = f"""Generate {request.count} multiple choice questions about: {request.topic}

Difficulty: {request.difficulty}

Context from course materials:
{context[:1000]}

Generate questions as JSON array with this exact structure:
[
  {{
    "prompt": "Question text here?",
    "options": [
      {{"id": "a", "text": "Option A"}},
      {{"id": "b", "text": "Option B"}},
      {{"id": "c", "text": "Option C"}},
      {{"id": "d", "text": "Option D"}}
    ],
    "correct_answer": "a",
    "explanation": "Explanation of why this is correct"
  }}
]

Requirements:
- {request.difficulty} difficulty level
- 4 options per question
- Clear explanations
- Based on COMP-237 content"""

        response = llm.invoke(prompt)
        
        # Parse LLM response
        import re
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            questions_data = json.loads(json_match.group())
        else:
            # Fallback: generate basic questions
            questions_data = [
                {
                    "prompt": f"Question about {request.topic}?",
                    "options": [
                        {"id": "a", "text": "Option A"},
                        {"id": "b", "text": "Option B"},
                        {"id": "c", "text": "Option C"},
                        {"id": "d", "text": "Option D"}
                    ],
                    "correct_answer": "a",
                    "explanation": "This is the correct answer."
                }
            ]
        
        # Create quiz questions with IDs
        questions = []
        for q_data in questions_data[:request.count]:
            questions.append(QuizQuestion(
                id=nanoid(),
                prompt=q_data["prompt"],
                options=[QuizOption(**opt) for opt in q_data["options"]],
                correct_answer=q_data["correct_answer"],
                explanation=q_data["explanation"]
            ))
        
        quiz_id = str(uuid.uuid4())
        
        return QuizGenerateResponse(
            quiz_id=quiz_id,
            questions=questions,
            topic=request.topic,
            difficulty=request.difficulty
        )
        
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


class QuizSubmitRequest(BaseModel):
    """Quiz submission request"""
    quiz_id: str
    student_id: str
    answers: Dict[str, str]  # question_id -> selected_option_id
    time_taken_seconds: Optional[int] = None

class QuizResult(BaseModel):
    """Single question result"""
    question_id: str
    selected: str
    correct: str
    is_correct: bool
    explanation: str

class QuizSubmitResponse(BaseModel):
    """Quiz submission response"""
    score: float
    total_questions: int
    correct_count: int
    results: List[QuizResult]

@app.post("/api/quiz/submit", response_model=QuizSubmitResponse)
async def submit_quiz(request: QuizSubmitRequest):
    """Submit quiz answers and get results"""
    try:
        # Note: In production, retrieve original quiz from database
        # For now, we'll need to validate against stored quiz data
        # This is a simplified version
        
        # TODO: Integrate with Supabase to store quiz responses
        # For now, return mock results
        
        results = []
        correct_count = 0
        
        for question_id, selected_answer in request.answers.items():
            # In production, look up correct answer from stored quiz
            # For now, we'll mark as correct if it's "a" (placeholder)
            is_correct = selected_answer == "a"  # Placeholder
            if is_correct:
                correct_count += 1
            
            results.append(QuizResult(
                question_id=question_id,
                selected=selected_answer,
                correct="a",  # Placeholder
                is_correct=is_correct,
                explanation="This is a placeholder explanation."
            ))
        
        total = len(request.answers)
        score = (correct_count / total * 100) if total > 0 else 0
        
        return QuizSubmitResponse(
            score=score,
            total_questions=total,
            correct_count=correct_count,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Quiz submission error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")


# ============================================================================
# NOTES CRUD ENDPOINTS
# ============================================================================

class Note(BaseModel):
    """Note model"""
    id: Optional[str] = None
    student_id: str
    topic: Optional[str] = None
    content: str
    context: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CreateNoteRequest(BaseModel):
    """Create note request"""
    student_id: str
    topic: Optional[str] = None
    content: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None

class UpdateNoteRequest(BaseModel):
    """Update note request"""
    content: Optional[str] = None
    topic: Optional[str] = None

@app.post("/api/notes")
async def create_note(request: CreateNoteRequest):
    """Create a new note"""
    try:
        # TODO: Integrate with Supabase
        # For now, return mock success
        note_id = str(uuid.uuid4())
        
        return {
            "id": note_id,
            "student_id": request.student_id,
            "topic": request.topic,
            "content": request.content,
            "context": request.context,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Create note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notes/{student_id}")
async def get_notes(student_id: str):
    """Get all notes for a student"""
    try:
        # TODO: Integrate with Supabase
        # For now, return empty list
        return {"notes": []}
    except Exception as e:
        logger.error(f"Get notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/notes/{note_id}")
async def update_note(note_id: str, request: UpdateNoteRequest):
    """Update a note"""
    try:
        # TODO: Integrate with Supabase
        return {
            "id": note_id,
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Update note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete a note"""
    try:
        # TODO: Integrate with Supabase
        return {"success": True, "id": note_id}
    except Exception as e:
        logger.error(f"Delete note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DASHBOARD ENDPOINT
# ============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    topics_mastered: int
    current_streak: int
    total_quizzes: int
    average_score: float
    weak_topics: List[str]
    recommended_topics: List[str]
    recent_activity: List[Dict[str, Any]]

@app.get("/api/dashboard/{student_id}", response_model=DashboardStats)
async def get_dashboard(student_id: str):
    """Get dashboard statistics for a student"""
    try:
        # TODO: Integrate with Supabase to fetch real data
        # For now, return mock data
        return DashboardStats(
            topics_mastered=5,
            current_streak=3,
            total_quizzes=12,
            average_score=78.5,
            weak_topics=["Backpropagation", "K-means Clustering"],
            recommended_topics=["Neural Networks", "Gradient Descent"],
            recent_activity=[
                {
                    "type": "quiz",
                    "topic": "Machine Learning",
                    "score": 85,
                    "timestamp": datetime.now().isoformat()
                }
            ]
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONCEPT GRAPH ENDPOINT
# ============================================================================

class ConceptNode(BaseModel):
    """Concept graph node"""
    id: str
    label: str
    mastery: float  # 0-1
    module: Optional[str] = None

class ConceptEdge(BaseModel):
    """Concept graph edge"""
    source: str
    target: str
    type: Literal["prerequisite", "related", "next_step"]
    strength: float = 1.0

class ConceptGraphResponse(BaseModel):
    """Concept graph response"""
    nodes: List[ConceptNode]
    edges: List[ConceptEdge]

@app.get("/api/concept-graph", response_model=ConceptGraphResponse)
async def get_concept_graph(student_id: Optional[str] = None):
    """Get concept relationship graph"""
    try:
        # TODO: Build from ChromaDB metadata and Supabase relationships
        # For now, return mock graph
        return ConceptGraphResponse(
            nodes=[
                ConceptNode(id="ml", label="Machine Learning", mastery=0.8, module="Module 1"),
                ConceptNode(id="nn", label="Neural Networks", mastery=0.6, module="Module 2"),
                ConceptNode(id="backprop", label="Backpropagation", mastery=0.4, module="Module 3"),
                ConceptNode(id="kmeans", label="K-means", mastery=0.7, module="Module 5")
            ],
            edges=[
                ConceptEdge(source="ml", target="nn", type="prerequisite", strength=0.9),
                ConceptEdge(source="nn", target="backprop", type="next_step", strength=0.8),
                ConceptEdge(source="ml", target="kmeans", type="related", strength=0.6)
            ]
        )
    except Exception as e:
        logger.error(f"Concept graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "development.backend.fastapi_service.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
