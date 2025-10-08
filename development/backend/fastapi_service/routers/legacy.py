"""
Router for legacy search endpoints. These are kept for testing and backward compatibility.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..main import chroma_db, navigate_workflow, logger
from ..models import NavigateRequest, NavigateResponse, SearchResult, LangGraphNavigateRequest, LangGraphNavigateResponse

router = APIRouter()

@router.post("/query/navigate", response_model=NavigateResponse, tags=["Legacy"], summary="Legacy Navigate Search")
async def navigate_query(request: NavigateRequest, req: Request):
    """
    Original Navigate mode: Direct semantic search for course content using ChromaDB.
    """
    start_time = datetime.now()
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"Legacy Navigate from {client_ip}: '{request.query}' (n={request.n_results})")

    if chroma_db is None:
        raise HTTPException(status_code=503, detail="Search service not available")

    try:
        where_filter = {}
        if request.module_filter:
            where_filter["module"] = request.module_filter
        if request.content_type_filter:
            where_filter["content_type"] = request.content_type_filter

        chroma_results = chroma_db.query(
            query_text=request.query,
            n_results=request.n_results * 2,
            filter_metadata=where_filter if where_filter else None
        )

        results = []
        if chroma_results["documents"] and chroma_results["documents"][0]:
            for doc, meta, dist in zip(
                chroma_results["documents"][0],
                chroma_results["metadatas"][0],
                chroma_results["distances"][0]
            ):
                if not request.include_no_url and not meta.get("live_lms_url"):
                    continue

                result = SearchResult(
                    title=meta.get("title", "Untitled"),
                    excerpt=doc[:150] + "...",
                    score=round(dist, 4),
                    live_url=meta.get("live_lms_url"),
                    module=meta.get("module", "Unknown"),
                    bb_doc_id=meta.get("bb_doc_id"),
                    content_type=meta.get("content_type", "unknown"),
                    chunk_index=meta.get("chunk_index", 0),
                    total_chunks=meta.get("total_chunks", 1),
                    tags=meta.get("tags", "").split(",") if meta.get("tags") else []
                )
                results.append(result)
                if len(results) >= request.n_results:
                    break

        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return NavigateResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            execution_time_ms=round(execution_time_ms, 2),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Legacy Navigate query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/langgraph/navigate", response_model=LangGraphNavigateResponse, tags=["Legacy"], summary="Legacy LangGraph Navigate")
async def langgraph_navigate(request: LangGraphNavigateRequest):
    """
    Original LangGraph Navigate Mode: Multi-agent workflow for course content search.
    """
    start_time = datetime.now()
    logger.info(f"🤖 Legacy LangGraph Navigate query: '{request.query}'")

    if navigate_workflow is None:
        raise HTTPException(status_code=503, detail="Navigate workflow not available")

    try:
        result = navigate_workflow.invoke({
            "query": request.query,
            "chroma_db": chroma_db
        })
        
        formatted_data = result.get("formatted_response", {})
        if isinstance(formatted_data, str):
            formatted_data = {"message": formatted_data, "top_results": [], "related_topics": []}

        answer = formatted_data.get("answer", formatted_data.get("encouragement", "Here are relevant materials."))
        
        return LangGraphNavigateResponse(
            formatted_response=answer,
            top_results=formatted_data.get("top_results", []),
            related_topics=formatted_data.get("related_topics", []),
            external_resources=formatted_data.get("external_resources", []),
            next_steps=formatted_data.get("suggested_next_step")
        )
    except Exception as e:
        logger.error(f"Legacy LangGraph Navigate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Navigate workflow failed: {str(e)}")
