"""
Router for fetching external learning resources.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

from ..main import logger

router = APIRouter()

class ExternalResourcesRequest(BaseModel):
    """Request for external resources (lazy loading)"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")

class ExternalResourcesResponse(BaseModel):
    """Response with external learning resources"""
    resources: List[Dict[str, Any]]
    count: int

@router.post("/external-resources", response_model=ExternalResourcesResponse, tags=["External"], summary="Get External Resources")
async def get_external_resources(request: ExternalResourcesRequest):
    """
    Lazy loads external resources from various educational platforms.

    Searches:
    - YouTube videos
    - Wikipedia articles
    - Khan Academy, MIT OCW, and OER Commons
    """
    start_time = datetime.now()
    logger.info(f"🔍 External resources request: '{request.query}'")
    
    try:
        # These imports are now local to the endpoint to avoid circular dependencies
        # during the refactoring. They can be moved to the top level later.
        from langgraph.agents.external_resources import (
            search_youtube,
            search_oer_commons,
            search_educational_resources,
            _enhance_query_for_ai_context
        )
        
        enhanced_query = _enhance_query_for_ai_context(request.query)
        logger.info(f"  Enhanced query: '{enhanced_query}'")
        
        resources = []
        
        youtube_results = search_youtube(request.query, max_results=3)
        resources.extend(youtube_results)
        
        edu_results = search_educational_resources(request.query, max_results=10)
        resources.extend(edu_results)
        
        oer_results = search_oer_commons(request.query, max_results=1)
        resources.extend(oer_results)
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(
            f"✓ External resources found in {execution_time_ms:.2f}ms: "
            f"{len(resources)} total resources"
        )
        
        return ExternalResourcesResponse(
            resources=resources,
            count=len(resources)
        )
    
    except Exception as e:
        logger.error(f"External resources search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"External resources search failed: {str(e)}")
