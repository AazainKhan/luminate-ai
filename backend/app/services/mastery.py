"""
Student Mastery Service

Handles querying and updating student mastery scores in Supabase.
Uses exponential decay for forgetting curve simulation.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)

# Concept patterns for detection (same as evaluator)
CONCEPT_PATTERNS = {
    "backpropagation": r"\b(backprop\w*|back.?propagat\w*|chain.?rule)",
    "gradient_descent": r"\b(gradient.?descent|learning.?rate|optimi[sz]\w+)",
    "neural_networks": r"\b(neural.?network\w*|perceptron|hidden.?layer|neuron)",
    "activation_functions": r"\b(activ\w*.?func\w*|relu|sigmoid|tanh|softmax)",
    "loss_functions": r"\b(loss.?func\w*|mse|cross.?entropy|cost.?func\w*)",
    "supervised_learning": r"\b(supervis\w*.?learn\w*|classif\w*|regress\w*|label\w*)",
    "unsupervised_learning": r"\b(unsupervis\w*|cluster\w*|k.?means|pca|dimensionality)",
    "decision_trees": r"\b(decision.?tree\w*|random.?forest\w*|entropy|gini|split)",
    "search_algorithms": r"\b(search.?algo\w*|bfs|dfs|a.?star|heuristic|uninformed|informed)",
    "intelligent_agents": r"\b(intelligen\w*.?agent\w*|agent.?func\w*|percept\w*|actuator)",
    "knowledge_representation": r"\b(knowledge.?rep\w*|ontolog\w*|semantic.?net\w*|frame\w*)",
}


async def get_student_mastery(user_id: str) -> Dict[str, Dict]:
    """
    Get all mastery scores for a student.
    
    Returns:
        Dict mapping concept_tag to {mastery_score, last_assessed_at, decay_factor}
    """
    if not user_id or not settings.supabase_url:
        return {}
    
    try:
        from supabase import create_client
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        response = supabase.table("student_mastery") \
            .select("concept_tag, mastery_score, last_assessed_at, decay_factor") \
            .eq("user_id", user_id) \
            .execute()
        
        mastery = {}
        for row in response.data:
            concept = row["concept_tag"]
            mastery[concept] = {
                "score": row["mastery_score"],
                "last_assessed": row["last_assessed_at"],
                "decay_factor": row["decay_factor"],
            }
        
        logger.info(f"Retrieved mastery for user {user_id}: {len(mastery)} concepts")
        return mastery
        
    except Exception as e:
        logger.warning(f"Failed to get student mastery: {e}")
        return {}


async def get_mastery_context_string(user_id: str, detected_concept: str = None) -> str:
    """
    Get a human-readable mastery context string for prompts.
    
    Returns string like:
    "Neural Networks: Strong (0.8), Backpropagation: Needs work (0.3)"
    """
    if not user_id:
        return "Not logged in - using default scaffolding"
    
    mastery = await get_student_mastery(user_id)
    
    if not mastery:
        return "First session - no prior mastery data. Start with diagnostic questions."
    
    # Format mastery into readable string
    lines = []
    for concept, data in sorted(mastery.items(), key=lambda x: x[1]["score"], reverse=True):
        score = data["score"]
        
        # Apply time-based decay
        last_assessed = data.get("last_assessed")
        if last_assessed:
            try:
                last_dt = datetime.fromisoformat(last_assessed.replace("Z", "+00:00"))
                days_ago = (datetime.now(last_dt.tzinfo) - last_dt).days
                if days_ago > 0:
                    decay = data.get("decay_factor", 0.95) ** days_ago
                    score = 0.5 + (score - 0.5) * decay  # Decay toward 0.5
            except:
                pass
        
        # Convert to human-readable level
        if score >= 0.8:
            level = "Strong"
        elif score >= 0.6:
            level = "Good"
        elif score >= 0.4:
            level = "Developing"
        else:
            level = "Needs work"
        
        # Format concept name
        concept_name = concept.replace("_", " ").title()
        lines.append(f"• {concept_name}: {level} ({score:.2f})")
    
    # Highlight relevant concept if detected
    if detected_concept:
        if detected_concept in mastery:
            current = mastery[detected_concept]["score"]
            hint = "build on existing knowledge" if current >= 0.5 else "needs scaffolding"
            lines.insert(0, f"**Current topic ({detected_concept.replace('_', ' ').title()})**: {hint}")
        else:
            lines.insert(0, f"**Current topic ({detected_concept.replace('_', ' ').title()})**: New concept - start diagnostic")
    
    return "\n".join(lines[:6])  # Limit to 6 most relevant


async def update_student_mastery(
    user_id: str,
    concept_tag: str,
    evaluation_confidence: float,
    outcome: str = "question_asked",
) -> bool:
    """
    Update student mastery score using exponential moving average.
    
    Args:
        user_id: Student UUID
        concept_tag: Concept being assessed
        evaluation_confidence: 0-1 confidence from evaluator
        outcome: 'correct', 'incorrect', 'confusion_detected', 'passive_read'
    
    Returns:
        True if update succeeded
    """
    if not user_id or not settings.supabase_url:
        return False
    
    try:
        from supabase import create_client
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        # Get current mastery
        current = await get_student_mastery(user_id)
        current_score = current.get(concept_tag, {}).get("score", 0.5)
        
        # Calculate new score using EMA
        # Weight recent performance more heavily for confused students
        if outcome == "confusion_detected":
            weight = 0.4  # More weight to recent (poor) performance
            evaluation_confidence = 0.3  # Lower confidence
        elif outcome == "incorrect":
            weight = 0.3
            evaluation_confidence = 0.4
        else:
            weight = 0.2  # Standard learning weight
        
        new_score = (1 - weight) * current_score + weight * evaluation_confidence
        new_score = max(0.1, min(0.95, new_score))  # Clamp to 0.1-0.95
        
        # Upsert to database
        response = supabase.table("student_mastery").upsert({
            "user_id": user_id,
            "concept_tag": concept_tag,
            "mastery_score": new_score,
            "last_assessed_at": datetime.utcnow().isoformat(),
            "decay_factor": 0.95,
        }).execute()
        
        logger.info(f"Updated mastery for {user_id}/{concept_tag}: {current_score:.2f} → {new_score:.2f}")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to update student mastery: {e}")
        return False


def get_mastery_context_sync(user_id: str, detected_concept: str = None) -> str:
    """
    Synchronous wrapper for mastery context (for non-async contexts).
    Falls back to placeholder if async fails.
    """
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In async context, return placeholder (will be properly fetched later)
                logger.debug("Event loop running, using placeholder context")
                return _get_placeholder_context(detected_concept)
        except RuntimeError:
            # No event loop in current thread - create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(get_mastery_context_string(user_id, detected_concept))
            loop.close()
            return result
        return loop.run_until_complete(get_mastery_context_string(user_id, detected_concept))
    except Exception as e:
        logger.debug(f"Sync mastery fetch failed (non-critical): {e}")
        return _get_placeholder_context(detected_concept)


def _get_placeholder_context(detected_concept: str = None) -> str:
    """Return placeholder mastery context"""
    if detected_concept:
        return f"Topic: {detected_concept.replace('_', ' ').title()} - Use scaffolding approach"
    return "No prior mastery data - start with diagnostic questions"
