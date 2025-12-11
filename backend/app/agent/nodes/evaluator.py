"""
Evaluator Node - Response quality evaluation, interaction logging, and mastery updates

This node runs after tutor/math/reject nodes to:
1. Detect concepts from the query
2. Log interactions to Supabase `interactions` table
3. Update student mastery scores
4. Score responses in Langfuse

Based on evaluator logic from backend/app/agents/evaluator.py
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.agent.state import AgentState
from app.config import settings
from app.observability import get_langfuse_client

logger = logging.getLogger(__name__)


# =============================================================================
# COMP 237 Concept Detection Patterns
# =============================================================================

CONCEPT_PATTERNS = {
    "backpropagation": r"\b(backprop\w*|back.?propagat\w*|chain.?rule|error.?propagat\w*)",
    "gradient_descent": r"\b(gradient.?descent|learning.?rate|optimi[sz]\w+|minimize|converge|gradient)",
    "neural_networks": r"\b(neural.?network\w*|perceptron\w*|hidden.?layer\w*|deep.?learn\w*|ann\b|neuron\w*|activation.?function\w*)",
    "classification": r"\b(classif\w+|decision.?tree\w*|knn\b|k-?nearest|svm\b|support.?vector\w*|naive.?bayes|logistic.?regress\w*)",
    "regression": r"\b(regress\w+|linear.?model\w*|polynomial|predict\w*.*(continuous|number|value)|linear.?regress\w*)",
    "clustering": r"\b(cluster\w+|k-?means|hierarchical|unsupervised.?learn\w*|grouping|dbscan)",
    "probability": r"\b(bayes\w*|probabilit\w+|prior|posterior|conditional|likelihood|distribution)",
    "supervised_learning": r"\b(supervis\w+|labeled.?data|training.?label\w*|target.?variable|train.?test)",
    "unsupervised_learning": r"\b(unsupervis\w+|unlabeled|dimensionality.?reduc\w*|pca\b)",
    "model_evaluation": r"\b(accuracy|precision|recall|f1.?score|confusion.?matrix|cross.?validat\w*|overfit\w*|underfit\w*|bias.?variance)",
    "data_preprocessing": r"\b(normali[sz]\w*|feature.?engineer\w*|data.?clean\w*|missing.?value\w*|scaling|encoding|preprocess\w*)",
}

# Scaffolding level to string mapping
SCAFFOLDING_LEVEL_MAP = {
    1: "hint",
    2: "guided", 
    3: "explained",
    4: "demonstrated",
}


def detect_concept_from_query(query: str) -> Optional[str]:
    """
    Detect the AI/ML concept being discussed from the query.
    
    Returns:
        Concept tag string or None
    """
    query_lower = query.lower()
    
    for concept, pattern in CONCEPT_PATTERNS.items():
        if re.search(pattern, query_lower, re.IGNORECASE):
            return concept
    
    # Fallback: check for general course keywords
    if any(kw in query_lower for kw in ["course", "class", "comp 237", "comp237"]):
        return "course_general"
    
    return None


def detect_misconceptions(query: str) -> List[Dict]:
    """
    Detect potential misconceptions in student's query.
    
    Returns list of detected misconceptions with metadata.
    """
    MISCONCEPTION_PATTERNS = {
        "classification_regression_swap": {
            "pattern": r"\b(regression|regress).*(categor|class|discrete)|\b(classif).*(continuous|number|value)\b",
            "description": "Confusing classification (categories) with regression (continuous values)",
            "concept": "classification"
        },
        "overfitting_underfitting_swap": {
            "pattern": r"\b(overfit).*(simple|less\s+data)|\b(underfit).*(complex|more\s+data)\b",
            "description": "Confusing overfitting (too complex) with underfitting (too simple)",
            "concept": "model_evaluation"
        },
        "supervised_unsupervised_swap": {
            "pattern": r"\b(supervised).*(no\s+labels|unlabeled)|\b(unsupervised).*(labeled|target)\b",
            "description": "Confusing supervised (labeled data) with unsupervised (unlabeled)",
            "concept": "supervised_learning"
        },
        "gradient_descent_direction": {
            "pattern": r"\bgradient.*(increase|maximize|ascent)\b(?!.*negative)",
            "description": "Thinking gradient descent goes UP the gradient (it goes DOWN)",
            "concept": "gradient_descent"
        },
    }
    
    query_lower = query.lower()
    detected = []
    
    for name, info in MISCONCEPTION_PATTERNS.items():
        if re.search(info["pattern"], query_lower, re.IGNORECASE):
            detected.append({
                "misconception_id": name,
                "description": info["description"],
                "concept": info["concept"]
            })
            logger.info(f"🔍 Detected misconception: {name}")
    
    return detected


def determine_outcome(state: AgentState) -> str:
    """
    Determine the outcome of the interaction based on state.
    
    Returns one of: 'confusion_detected', 'correct', 'incorrect'
    (These are the allowed values in the interactions table check constraint)
    """
    is_stuck = state.get("is_stuck", False)
    escalation_level = state.get("escalation_level", 1)
    
    if is_stuck:
        return "confusion_detected"
    elif escalation_level >= 3:
        # High scaffolding needed = student was struggling
        return "confusion_detected"
    else:
        # Student got a normal response without heavy scaffolding
        return "correct"


def log_interaction_to_supabase(
    user_id: str,
    interaction_type: str,
    concept_focus: Optional[str],
    outcome: str,
    intent: str,
    scaffolding_level: Optional[str],
    query: str,
    response_preview: str,
    misconceptions: Optional[List[Dict]] = None
) -> bool:
    """
    Log interaction to Supabase `interactions` table for learning analytics.
    
    Returns:
        True if logged successfully
    """
    if not user_id:
        logger.debug("No user_id, skipping interaction logging")
        return False
    
    try:
        from supabase import create_client
        
        if not settings.supabase_url or not settings.supabase_service_role_key:
            logger.warning("Supabase not configured, skipping interaction logging")
            return False
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        # Build metadata with misconceptions
        metadata = {
            "query_preview": query[:200] if query else "",
            "response_preview": response_preview[:200] if response_preview else "",
        }
        
        if misconceptions:
            metadata["misconceptions"] = misconceptions
            logger.info(f"📊 Recording {len(misconceptions)} misconception(s)")
        
        interaction_data = {
            "student_id": user_id,
            "type": interaction_type,
            "concept_focus": concept_focus,
            "outcome": outcome,
            "scaffolding_level": scaffolding_level,
            "metadata": metadata
        }
        
        response = supabase.table("interactions").insert(interaction_data).execute()
        logger.info(f"📊 Logged interaction: {interaction_type} for concept: {concept_focus}")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to log interaction to Supabase: {e}")
        return False


def calculate_mastery_score(
    old_score: float, 
    evaluation_confidence: float, 
    decay_factor: float = 0.95
) -> float:
    """
    Calculate new mastery score using exponential moving average with decay.
    
    Implements forgetting curve - scores decay towards 0.5 over time.
    Good performance increases score, poor performance decreases it.
    
    Formula (clamped to [0.1, 0.95]):
        new = 0.7 * (0.5 + (old_score - 0.5) * decay_factor) + 0.3 * evaluation_confidence
    """
    # Apply decay to old score (moves toward 0.5 neutral)
    decayed_old = 0.5 + (old_score - 0.5) * decay_factor
    
    # Blend with new evaluation (30% weight to new, 70% to decayed old)
    new_score = 0.7 * decayed_old + 0.3 * evaluation_confidence
    
    # Clamp to [0.1, 0.95] to avoid extremes
    return max(0.1, min(0.95, new_score))


def update_student_mastery(
    user_id: str,
    concept_tag: str,
    evaluation_confidence: float,
    decay_factor: float = 0.95
) -> bool:
    """
    Update student mastery score in Supabase `student_mastery` table.
    
    Uses exponential moving average with decay for forgetting curve.
    
    Args:
        user_id: Student's user ID
        concept_tag: The concept being updated
        evaluation_confidence: Quality score from this interaction (0-1)
        decay_factor: Decay factor for forgetting curve
        
    Returns:
        True if updated successfully
    """
    if not user_id or not concept_tag:
        return False
    
    try:
        from supabase import create_client
        
        if not settings.supabase_url or not settings.supabase_service_role_key:
            logger.warning("Supabase not configured, skipping mastery update")
            return False
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        # Get current mastery score
        existing = supabase.table("student_mastery").select("mastery_score").eq(
            "user_id", user_id
        ).eq("concept_tag", concept_tag).execute()
        
        now = datetime.now(timezone.utc).isoformat()
        
        if existing.data and len(existing.data) > 0:
            # Update existing
            old_score = existing.data[0].get("mastery_score", 0.5)
            new_score = calculate_mastery_score(old_score, evaluation_confidence, decay_factor)
            
            supabase.table("student_mastery").update({
                "mastery_score": new_score,
                "decay_factor": decay_factor,
                "last_assessed_at": now
            }).eq("user_id", user_id).eq("concept_tag", concept_tag).execute()
            
            logger.info(f"📈 Updated mastery for {concept_tag}: {old_score:.2f} → {new_score:.2f}")
        else:
            # Insert new
            new_score = 0.5 + (evaluation_confidence - 0.5) * 0.3  # Start near neutral
            
            supabase.table("student_mastery").insert({
                "user_id": user_id,
                "concept_tag": concept_tag,
                "mastery_score": new_score,
                "decay_factor": decay_factor,
                "last_assessed_at": now
            }).execute()
            
            logger.info(f"📈 Created mastery for {concept_tag}: {new_score:.2f}")
        
        return True
        
    except Exception as e:
        logger.warning(f"Failed to update mastery in Supabase: {e}")
        return False


def score_in_langfuse(
    trace_id: str,
    evaluation: Dict[str, Any]
) -> bool:
    """
    Send comprehensive evaluation scores to Langfuse.
    
    Scores sent:
    - scaffolding_level: 1-4 escalation level used
    - concept_coverage: Whether a COMP237 concept was detected
    - misconception_count: Number of misconceptions identified
    - response_quality: Overall quality score based on outcome
    - mastery_impact: Whether mastery was updated (positive/negative)
    """
    try:
        client = get_langfuse_client()
        if not client:
            return False
        
        # 1. Scaffolding level score
        client.create_score(
            trace_id=trace_id,
            name="scaffolding_level",
            value=float(evaluation.get("escalation_level", 1)),
            comment=f"Escalation level used: {evaluation.get('scaffolding_level', 'hint')}"
        )
        
        # 2. Concept coverage score
        if evaluation.get("concept_detected"):
            client.create_score(
                trace_id=trace_id,
                name="concept_coverage",
                value=1.0,
                comment=f"Concept: {evaluation['concept_detected']}"
            )
        else:
            client.create_score(
                trace_id=trace_id,
                name="concept_coverage",
                value=0.0,
                comment="No specific COMP237 concept detected"
            )
        
        # 3. Misconception detection score
        misconception_count = len(evaluation.get("misconceptions", []))
        if misconception_count > 0:
            client.create_score(
                trace_id=trace_id,
                name="misconception_count",
                value=float(misconception_count),
                comment=f"Detected {misconception_count} potential misconception(s)"
            )
        
        # 4. Response quality score based on outcome
        outcome = evaluation.get("outcome", "")
        quality_scores = {
            "correct": 1.0,
            "confusion_detected": 0.3,
            "incorrect": 0.2,
            "rejected": 0.0,
            "integrity_violation": 0.0,
            "off_topic": 0.0,
        }
        quality_score = quality_scores.get(outcome, 0.5)
        client.create_score(
            trace_id=trace_id,
            name="response_quality",
            value=quality_score,
            comment=f"Outcome: {outcome}"
        )
        
        # 5. Mastery impact score (whether this helped learning)
        was_rejected = evaluation.get("was_rejected", False)
        escalation = evaluation.get("escalation_level", 1)
        if not was_rejected:
            # Lower escalation = better (student understood faster)
            mastery_impact = 1.0 - (escalation - 1) * 0.25
            client.create_score(
                trace_id=trace_id,
                name="mastery_impact",
                value=mastery_impact,
                comment=f"Learning efficiency: escalation level {escalation}"
            )
        
        logger.info(f"📊 Sent {5} scores to Langfuse for trace {trace_id[:8]}...")
        return True
    except Exception as e:
        logger.warning(f"Failed to score in Langfuse: {e}")
        return False


def evaluator_node(state: AgentState) -> AgentState:
    """
    Evaluator node - runs after generation to log interactions and update mastery.
    
    This node:
    1. Detects the concept from the query
    2. Detects any misconceptions
    3. Logs the interaction to Supabase
    4. Updates student mastery
    5. Sends scores to Langfuse
    
    Uses Langfuse v3 context managers for proper trace hierarchy.
    """
    logger.info("📊 Running evaluator node")
    
    # Get Langfuse client for tracing
    langfuse = get_langfuse_client()
    
    def _execute_evaluator() -> AgentState:
        """Inner function for evaluator logic."""
        # Get data from state
        query = state.get("query", "")
        response = state.get("response", "")
        user_id = state.get("user_id")
        trace_id = state.get("trace_id")
        escalation_level = state.get("escalation_level", 1)
        is_stuck = state.get("is_stuck", False)
        
        # Get intent from plan (may be None if Governor rejected before Planner)
        plan = state.get("plan") or {}
        subtasks = plan.get("subtasks", [])
        intent = subtasks[0].get("task", "explain") if subtasks else "explain"
        
        # Check if this was a Governor rejection (no plan = rejected early)
        was_rejected = not state.get("approved", True)
        rejection_reason = state.get("rejection_reason")
        
        # For Governor rejections, override intent
        if was_rejected:
            intent = "reject"
        
        # Detect concept
        concept = detect_concept_from_query(query)
        
        # Detect misconceptions
        misconceptions = detect_misconceptions(query)
        
        # Determine outcome
        outcome = determine_outcome(state)
        
        # For Governor rejections, override outcome to track the violation
        if was_rejected:
            if rejection_reason == "integrity":
                outcome = "integrity_violation"
            elif rejection_reason in ["off_topic", "low_relevance", "no_course_content"]:
                outcome = "off_topic"
            else:
                outcome = "rejected"
        
        # Map escalation level to scaffolding string
        scaffolding_str = SCAFFOLDING_LEVEL_MAP.get(escalation_level, "hint")
        
        # Create evaluation result
        evaluation = {
            "concept_detected": concept,
            "misconceptions": misconceptions,
            "outcome": outcome,
            "escalation_level": escalation_level,
            "scaffolding_level": scaffolding_str,
            "was_rejected": was_rejected,
            "rejection_reason": rejection_reason,
        }
        
        # Log interaction to Supabase
        if user_id:
            log_interaction_to_supabase(
                user_id=user_id,
                interaction_type="question_asked" if not was_rejected else "policy_violation",
                concept_focus=concept,
                outcome=outcome,
                intent=intent,
                scaffolding_level=scaffolding_str,
                query=query,
                response_preview=response[:200] if response else "",
                misconceptions=misconceptions if misconceptions else None
            )
            
            # Update mastery if concept detected (not for rejections)
            if concept and concept != "course_general" and not was_rejected:
                # Confidence based on outcome and escalation
                if outcome == "confusion_detected" or is_stuck:
                    confidence = 0.3  # Low confidence, mastery decreases
                elif escalation_level >= 3:
                    confidence = 0.4  # Medium-low, needed heavy scaffolding
                elif escalation_level == 2:
                    confidence = 0.6  # Medium confidence
                else:
                    confidence = 0.7  # Good, answered at level 1
                
                update_student_mastery(
                    user_id=user_id,
                    concept_tag=concept,
                    evaluation_confidence=confidence
                )
        
        # Score in Langfuse (uses trace_id, not spans)
        if trace_id:
            score_in_langfuse(trace_id, evaluation)
        
        # Store evaluation in state
        state["evaluation"] = evaluation
        
        logger.info(f"📊 Evaluation complete: concept={concept}, outcome={outcome}, escalation={escalation_level}")
        
        return state
    
    # Execute with Langfuse tracing
    if langfuse:
        try:
            # CRITICAL: Use parent_span_id for proper nesting, not trace_context
            # trace_context would create a new root span, breaking hierarchy
            parent_span_id = state.get("parent_span_id")
            
            # Start evaluator as child of current context
            with langfuse.start_as_current_observation(
                as_type="evaluator",
                name="evaluator_node",
                input={"query": state.get("query", "")[:100]},
                metadata={"node": "evaluator", "version": "v3"}
            ) as eval_span:
                result_state = _execute_evaluator()
                evaluation = result_state.get("evaluation", {})
                
                # Update span with output
                eval_span.update(
                    output={
                        "concept_detected": evaluation.get("concept_detected"),
                        "outcome": evaluation.get("outcome"),
                        "escalation_level": evaluation.get("escalation_level"),
                        "was_rejected": evaluation.get("was_rejected"),
                    },
                    metadata={"parent_confirmed": parent_span_id is not None}
                )
                
                return result_state
        except Exception as e:
            logger.error(f"[Evaluator] Error with tracing: {e}")
            # Fall through to non-traced execution
    
    # Execute without tracing if Langfuse not available
    result_state = _execute_evaluator()
    return result_state
