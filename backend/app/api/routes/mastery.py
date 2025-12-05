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


# ============ Quiz Evaluation ============

class QuizAnswer(BaseModel):
    """Student's answer to a quiz question"""
    concept: str
    question: str
    selected_index: int  # 0-based index of selected answer
    options: List[str]
    correct_index: int


class QuizResult(BaseModel):
    """Result of quiz evaluation"""
    is_correct: bool
    feedback: str
    mastery_delta: float
    new_mastery: Optional[float] = None


@router.post("/quiz/evaluate")
async def evaluate_quiz_answer(
    answer: QuizAnswer,
    user_info: dict = require_student,
):
    """
    Evaluate a student's quiz answer and update mastery.
    
    This endpoint:
    1. Checks if the answer is correct
    2. Provides feedback with explanation
    3. Updates the student's mastery score for the concept
    4. Logs the interaction
    """
    try:
        supabase = get_supabase_client()
        user_id = user_info["user_id"]
        
        # Determine correctness
        is_correct = answer.selected_index == answer.correct_index
        
        # Calculate mastery delta
        mastery_delta = 0.1 if is_correct else -0.05
        
        # Generate feedback
        if is_correct:
            feedback = f"✅ Correct! Great job understanding {answer.concept}."
        else:
            correct_answer = answer.options[answer.correct_index] if 0 <= answer.correct_index < len(answer.options) else "the correct option"
            feedback = f"❌ Not quite. The correct answer was: **{correct_answer}**"
        
        # Get current mastery
        current_mastery = 0.5  # Default starting mastery
        try:
            mastery_response = supabase.table("student_mastery").select("mastery_score").eq(
                "user_id", user_id
            ).eq("concept_tag", answer.concept).execute()
            
            if mastery_response.data and len(mastery_response.data) > 0:
                current_mastery = mastery_response.data[0].get("mastery_score", 0.5)
        except Exception as e:
            logger.debug(f"Could not fetch current mastery: {e}")
        
        # Calculate new mastery (clamped between 0 and 1)
        new_mastery = max(0.0, min(1.0, current_mastery + mastery_delta))
        
        # Update mastery in database
        try:
            supabase.table("student_mastery").upsert({
                "user_id": user_id,
                "concept_tag": answer.concept,
                "mastery_score": new_mastery,
            }).execute()
            logger.info(f"Updated mastery for {answer.concept}: {current_mastery:.2f} → {new_mastery:.2f}")
        except Exception as e:
            logger.warning(f"Could not update mastery: {e}")
        
        # Log the interaction
        try:
            outcome = "correct" if is_correct else "incorrect"
            supabase.table("interactions").insert({
                "student_id": user_id,
                "type": "quiz_attempt",
                "concept_focus": answer.concept,
                "outcome": outcome,
                "metadata": {
                    "question": answer.question,
                    "selected_index": answer.selected_index,
                    "correct_index": answer.correct_index,
                    "mastery_delta": mastery_delta,
                }
            }).execute()
        except Exception as e:
            logger.debug(f"Could not log interaction: {e}")
        
        return QuizResult(
            is_correct=is_correct,
            feedback=feedback,
            mastery_delta=mastery_delta,
            new_mastery=new_mastery,
        )
        
    except Exception as e:
        logger.error(f"Error evaluating quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quiz/history")
async def get_quiz_history(
    concept: Optional[str] = None,
    limit: int = 10,
    user_info: dict = require_student,
):
    """
    Get student's quiz attempt history
    """
    try:
        supabase = get_supabase_client()
        user_id = user_info["user_id"]
        
        query = supabase.table("interactions").select("*").eq(
            "student_id", user_id
        ).eq("type", "quiz_attempt").order("created_at", desc=True).limit(limit)
        
        if concept:
            query = query.eq("concept_focus", concept)
        
        response = query.execute()
        
        return {
            "history": response.data if response.data else [],
            "count": len(response.data) if response.data else 0,
        }
        
    except Exception as e:
        logger.error(f"Error getting quiz history: {e}")
        raise HTTPException(status_code=500, detail=str(e))



