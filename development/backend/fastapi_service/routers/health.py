"""
Router for health check and status endpoints.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

# The main application will inject these dependencies
from ..main import chroma_db, logger

router = APIRouter()

@router.get("/", tags=["Health"], summary="API Root")
async def root():
    """Root endpoint providing basic API information."""
    return {
        "service": "Luminate AI API",
        "version": "1.0.0",
        "course": "COMP-237",
        "documentation": "/docs"
    }

@router.get("/health", tags=["Health"], summary="Health Check")
async def health_check():
    """Checks the operational status of the service and its dependencies (ChromaDB)."""
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

@router.get("/stats", tags=["Health"], summary="Get Collection Statistics")
async def get_stats():
    """Retrieves statistics and configuration for the ChromaDB collection."""
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
