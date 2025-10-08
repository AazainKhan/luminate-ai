"""
Centralized Pydantic models for the FastAPI application.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

# Models for /legacy/navigate
class NavigateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    n_results: int = Field(10, ge=1, le=50)
    min_score: float = Field(0.0, ge=0.0, le=1.0)
    module_filter: Optional[str] = None
    content_type_filter: Optional[str] = None
    include_no_url: bool = False

class SearchResult(BaseModel):
    title: str
    excerpt: str
    score: float
    live_url: Optional[str] = None
    module: str
    bb_doc_id: Optional[str] = None
    content_type: str
    chunk_index: int
    total_chunks: int
    tags: List[str] = []

class NavigateResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    execution_time_ms: float
    timestamp: str

# Models for /legacy/langgraph/navigate
class LangGraphNavigateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

class LangGraphNavigateResponse(BaseModel):
    formatted_response: str
    top_results: List[Dict[str, Any]]
    related_topics: List[Dict[str, Any]]
    external_resources: Optional[List[Dict[str, Any]]] = None
    next_steps: Optional[List[str]] = None

# Models for /api/query (Unified Endpoint)
class UnifiedQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    student_id: Optional[str] = None
    session_id: Optional[str] = None

class UnifiedQueryResponse(BaseModel):
    mode: Literal["navigate", "educate"]
    confidence: float
    reasoning: str
    response: Dict[str, Any]
    timestamp: str
