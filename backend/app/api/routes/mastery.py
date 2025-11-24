"""
Student Mastery Tracking API routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.api.middleware import require_student
from supabase import create_client, Client
from app.config import settings

router = APIRouter(prefix="/api/mastery", tags=["mastery"])
logger = logging.getLogger(__name__)

# Supabase client for mastery tracking
supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get Supabase client for database operations"""
    global supabase_client
    if supabase_client is None:
        if not settings.supabase_service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY not configured")
        supabase_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return supabase_client


class MasteryUpdate(BaseModel):
    concept_tag: str
    mastery_score: float
    interaction_type: str  # "question_asked", "quiz_attempt", "explanation_viewed"


class ConceptMastery(BaseModel):
    concept_tag: str
    mastery_score: float
    last_interaction: Optional[str] = None


@router.get("/")
async def get_mastery(
    user_info: dict = require_student,
):
    """
    Get student mastery scores for all concepts
    """
    try:
        supabase = get_supabase_client()
        
        # Query student_mastery table
        response = supabase.table("student_mastery").select("*").eq(
            "user_id", user_info["user_id"]
        ).execute()
        
        return {
            "mastery": response.data if response.data else [],
        }
    except Exception as e:
        logger.error(f"Error getting mastery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def update_mastery(
    update: MasteryUpdate,
    user_info: dict = require_student,
):
    """
    Update mastery score for a concept
    """
    try:
        supabase = get_supabase_client()
        
        # Upsert mastery record
        response = supabase.table("student_mastery").upsert({
            "user_id": user_info["user_id"],
            "concept_tag": update.concept_tag,
            "mastery_score": update.mastery_score,
            "last_interaction": "now()",
        }).execute()
        
        return {
            "success": True,
            "concept_tag": update.concept_tag,
            "mastery_score": update.mastery_score,
        }
    except Exception as e:
        logger.error(f"Error updating mastery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weak-topics")
async def get_weak_topics(
    threshold: float = 0.5,
    user_info: dict = require_student,
):
    """
    Get concepts where student mastery is below threshold
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("student_mastery").select("*").eq(
            "user_id", user_info["user_id"]
        ).lt("mastery_score", threshold).execute()
        
        return {
            "weak_topics": response.data if response.data else [],
            "threshold": threshold,
        }
    except Exception as e:
        logger.error(f"Error getting weak topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))



