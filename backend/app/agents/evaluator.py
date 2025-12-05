"""
Evaluator Node for Response Quality & Mastery Tracking
Implements:
1. Response quality scoring (pedagogical quality, scaffolding appropriateness)
2. Supabase interactions logging (for learning analytics)
3. Student mastery updates (for personalized scaffolding)
4. Langfuse scoring (for observability)

Integrates with Langfuse for scoring and analytics
"""

from typing import Dict, Optional, List
import logging
import time
import re
from app.agents.state import AgentState, ScaffoldingLevel, BloomLevel
from app.observability.langfuse_client import (
    create_observation,
    update_observation_with_usage,
    get_langfuse_client,
    create_child_span_from_state
)
from app.config import settings

logger = logging.getLogger(__name__)


# COMP 237 concept hierarchy for mastery tracking
COMP237_CONCEPTS = {
    "machine_learning": ["ml_basics", "supervised_learning", "unsupervised_learning", "model_evaluation"],
    "neural_networks": ["perceptron", "backpropagation", "activation_functions", "deep_learning"],
    "classification": ["decision_trees", "knn", "svm", "naive_bayes", "logistic_regression"],
    "regression": ["linear_regression", "polynomial_regression", "regularization"],
    "clustering": ["kmeans", "hierarchical", "dbscan"],
    "probability": ["bayes_theorem", "conditional_probability", "prior_posterior"],
    "optimization": ["gradient_descent", "loss_functions", "learning_rate"],
    "data_preprocessing": ["normalization", "feature_engineering", "train_test_split"],
}

# Concept detection patterns for automatic tagging
# Patterns should be flexible to match various phrasings
# Note: Using word-start \b but allowing word to continue (no trailing \b for prefixes)
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

# Common misconception patterns in AI/ML
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
    "learning_rate_inverse": {
        "pattern": r"\b(high|large)\s+learning.*(slow|precise)|\b(low|small)\s+learning.*(fast|quick)\b",
        "description": "Inverting learning rate effects (high=fast/unstable, low=slow/stable)",
        "concept": "gradient_descent"
    },
}

# Map intent values to user-friendly display names for UI
AGENT_DISPLAY_NAMES = {
    "tutor": "Concept Tutor",
    "math": "Math Solver",
    "coder": "Code Assistant",
    "syllabus_query": "Course Info",
    "fast": "Quick Answer",
    "explain": "Explainer",  # Explanatory responses
    "default": "AI Tutor",  # Fallback for unknown intents
}


def detect_misconceptions(query: str) -> List[Dict]:
    """
    Detect potential misconceptions in student's query
    
    Returns list of detected misconceptions with metadata
    """
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


class ResponseQualityEvaluator:
    """
    Evaluates the TUTOR'S response quality (not student's answer)
    
    This evaluator checks:
    1. Response structure (has activation, exploration, guidance, challenge sections)
    2. Scaffolding appropriateness for the detected confusion level
    3. Citation of sources
    4. Pedagogical quality (questions asked, progressive disclosure)
    """

    def __init__(self, quality_threshold: float = 0.6):
        """
        Initialize evaluator
        
        Args:
            quality_threshold: Minimum quality score to consider response good (0-1)
        """
        self.quality_threshold = quality_threshold

    def evaluate_response_quality(
        self,
        response: str,
        scaffolding_level: Optional[ScaffoldingLevel],
        confusion_detected: bool,
        retrieved_context: List[dict]
    ) -> Dict[str, any]:
        """
        Evaluate tutor response quality
        
        Args:
            response: Tutor's response text
            scaffolding_level: The scaffolding level used
            confusion_detected: Whether student confusion was detected
            retrieved_context: RAG context that was retrieved
            
        Returns:
            Dictionary with evaluation results
        """
        if not response or len(response.strip()) < 20:
            return {
                "confidence": 0.2,
                "passed": False,
                "feedback": "Response too brief",
                "level": "insufficient",
                "quality_breakdown": {}
            }
        
        response_lower = response.lower()
        quality_breakdown = {}
        
        # Check 1: Response structure (does it follow the pedagogical format?)
        has_thinking = "<thinking>" in response_lower or "**thinking**" in response_lower
        has_activation = any(kw in response_lower for kw in ["activation", "prior knowledge", "what do you already know"])
        has_exploration = any(kw in response_lower for kw in ["exploration", "what do you think", "how would you"])
        has_guidance = any(kw in response_lower for kw in ["guidance", "hint", "consider", "try"])
        has_challenge = any(kw in response_lower for kw in ["challenge", "test your", "try applying"])
        
        structure_score = sum([has_thinking, has_activation, has_exploration, has_guidance, has_challenge]) / 5
        quality_breakdown["structure"] = structure_score
        
        # Check 2: Socratic questioning (good responses ask questions)
        question_count = response.count("?")
        question_score = min(1.0, question_count / 3)  # Expect ~3 questions
        quality_breakdown["socratic_questions"] = question_score
        
        # Check 3: Source citation (if RAG context was available)
        has_citations = any(kw in response_lower for kw in ["from:", "[from", "source:", "according to"])
        citation_expected = len(retrieved_context) > 0
        citation_score = 1.0 if has_citations or not citation_expected else 0.3
        quality_breakdown["citations"] = citation_score
        
        # Check 4: Scaffolding appropriateness
        # Higher scaffolding for high confusion = good
        # Low scaffolding for low confusion = good
        scaffolding_appropriateness = 0.7  # Default
        if scaffolding_level:
            level_weight = {"hint": 0.25, "guided": 0.5, "explained": 0.75, "demonstrated": 1.0}
            scaffolding_weight = level_weight.get(scaffolding_level, 0.5)
            
            if confusion_detected and scaffolding_weight >= 0.5:
                scaffolding_appropriateness = 1.0
            elif not confusion_detected and scaffolding_weight <= 0.5:
                scaffolding_appropriateness = 1.0
            else:
                scaffolding_appropriateness = 0.6
        
        quality_breakdown["scaffolding_fit"] = scaffolding_appropriateness
        
        # Check 5: Response length (too short or too long is bad)
        response_length = len(response)
        if response_length < 200:
            length_score = 0.4
        elif response_length < 500:
            length_score = 0.7
        elif response_length < 2000:
            length_score = 1.0
        else:
            length_score = 0.8  # Slightly penalize very long responses
        quality_breakdown["length"] = length_score
        
        # Weighted average
        weights = {"structure": 0.3, "socratic_questions": 0.2, "citations": 0.15, 
                   "scaffolding_fit": 0.2, "length": 0.15}
        
        confidence = sum(quality_breakdown[k] * weights[k] for k in weights)
        passed = confidence >= self.quality_threshold
        
        return {
            "confidence": round(confidence, 3),
            "passed": passed,
            "feedback": "Good pedagogical response" if passed else "Response could be more structured",
            "level": "good" if confidence > 0.7 else "adequate" if confidence > 0.5 else "needs_improvement",
            "quality_breakdown": quality_breakdown
        }


def detect_concept_from_query(query: str) -> Optional[str]:
    """
    Detect the AI/ML concept being discussed from the query
    
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


def log_interaction_to_supabase_sync(
    user_id: str,
    interaction_type: str,
    concept_focus: Optional[str],
    outcome: str,
    intent: str,
    agent_used: str,
    scaffolding_level: Optional[str],
    query: str,
    response_preview: str,
    misconceptions: Optional[List[Dict]] = None
) -> bool:
    """
    Log interaction to Supabase `interactions` table for learning analytics (SYNCHRONOUS VERSION)
    
    Args:
        user_id: Student's user ID
        interaction_type: Type of interaction (question_asked, quiz_attempt, etc.)
        concept_focus: Detected concept tag
        outcome: Outcome (confusion_detected, correct, answered, etc.)
        intent: Routing intent
        agent_used: Which agent handled it
        scaffolding_level: Scaffolding level used
        query: Student's query
        response_preview: First 200 chars of response
        misconceptions: List of detected misconceptions
        
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
            "intent": intent,
            "agent_used": agent_used,
            "scaffolding_level": scaffolding_level,
            "metadata": metadata
        }
        
        response = supabase.table("interactions").insert(interaction_data).execute()
        logger.info(f"📊 Logged interaction: {interaction_type} for concept: {concept_focus}")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to log interaction to Supabase: {e}")
        return False


async def log_interaction_to_supabase(
    user_id: str,
    interaction_type: str,
    concept_focus: Optional[str],
    outcome: str,
    intent: str,
    agent_used: str,
    scaffolding_level: Optional[str],
    query: str,
    response_preview: str,
    misconceptions: Optional[List[Dict]] = None
) -> bool:
    """
    Log interaction to Supabase `interactions` table for learning analytics
    
    Args:
        user_id: Student's user ID
        interaction_type: Type of interaction (question_asked, quiz_attempt, etc.)
        concept_focus: Detected concept tag
        outcome: Outcome (confusion_detected, correct, answered, etc.)
        intent: Routing intent
        agent_used: Which agent handled it
        scaffolding_level: Scaffolding level used
        query: Student's query
        response_preview: First 200 chars of response
        misconceptions: List of detected misconceptions
        
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
            "intent": intent,
            "agent_used": agent_used,
            "scaffolding_level": scaffolding_level,
            "metadata": metadata
        }
        
        response = supabase.table("interactions").insert(interaction_data).execute()
        logger.info(f"📊 Logged interaction: {interaction_type} for concept: {concept_focus}")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to log interaction to Supabase: {e}")
        return False


def update_student_mastery_sync(
    user_id: str,
    concept_tag: str,
    evaluation_confidence: float,
    decay_factor: float = 0.95
) -> bool:
    """
    Update student mastery score in Supabase `student_mastery` table (SYNCHRONOUS VERSION)
    
    Uses exponential moving average with decay for forgetting curve
    
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
        
        new_score = 0.5
        if existing.data and len(existing.data) > 0:
            # Update with decay
            old_score = existing.data[0].get("mastery_score", 0.5)
            new_score = calculate_mastery_score(old_score, evaluation_confidence, decay_factor)
            
            from datetime import datetime, timezone
            supabase.table("student_mastery").update({
                "mastery_score": new_score,
                "decay_factor": decay_factor,
                "last_assessed_at": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", user_id).eq("concept_tag", concept_tag).execute()
        else:
            # Insert new mastery record
            new_score = evaluation_confidence * 0.5  # Start lower for first interaction
            supabase.table("student_mastery").insert({
                "user_id": user_id,
                "concept_tag": concept_tag,
                "mastery_score": new_score,
                "decay_factor": decay_factor,
            }).execute()
        
        logger.info(f"📈 Updated mastery: {concept_tag} = {new_score:.2f} for user {user_id[:8]}...")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to update mastery in Supabase: {e}")
        return False


async def update_student_mastery(
    user_id: str,
    concept_tag: str,
    evaluation_confidence: float,
    decay_factor: float = 0.95
) -> bool:
    """Async wrapper - kept for API compatibility"""
    return update_student_mastery_sync(user_id, concept_tag, evaluation_confidence, decay_factor)


def create_langfuse_scores(trace_id: str, state: AgentState, evaluation: Dict) -> None:
    """
    Create Langfuse scores for the interaction.
    
    Scores created:
    - pedagogical_quality: How well the response teaches (0-1)
    - policy_compliance: Whether governor approved (boolean as 0/1)
    - response_confidence: Evaluator confidence score (0-1)
    - scaffolding_level: Level of scaffolding used (categorical)
    
    Args:
        trace_id: Langfuse trace ID
        state: Agent state with evaluation data
        evaluation: Evaluation results dict
    """
    if not trace_id:
        return
    
    client = get_langfuse_client()
    if not client:
        return
    
    try:
        # Score 1: Pedagogical Quality (numeric 0-1)
        # Based on scaffolding level, intent, and response structure
        pedagogical_score = calculate_pedagogical_score(state, evaluation)
        client.create_score(
            trace_id=trace_id,
            name="pedagogical_quality",
            value=pedagogical_score,
            comment=f"Agent: {state.get('intent')}, Scaffolding: {state.get('scaffolding_level')}"
        )
        logger.debug(f"Langfuse score: pedagogical_quality = {pedagogical_score}")
        
        # Score 2: Policy Compliance (boolean as 0/1)
        governor_approved = state.get("governor_approved", False)
        client.create_score(
            trace_id=trace_id,
            name="policy_compliance",
            value=1.0 if governor_approved else 0.0,
            comment=state.get("governor_reason") if not governor_approved else "Approved"
        )
        logger.debug(f"Langfuse score: policy_compliance = {1 if governor_approved else 0}")
        
        # Score 3: Response Confidence (numeric 0-1)
        confidence = evaluation.get("confidence", 0.5)
        client.create_score(
            trace_id=trace_id,
            name="response_confidence",
            value=confidence,
            comment=evaluation.get("feedback", "")
        )
        logger.debug(f"Langfuse score: response_confidence = {confidence}")
        
        # Score 4: Scaffolding Level (categorical as string in comment)
        # FIX: Map to correct levels from pedagogical_tutor.py
        scaffolding_level = state.get("scaffolding_level") or "none"
        scaffolding_numeric = {
            "none": 0.0,
            "hint": 0.25,       # Was "minimal"
            "guided": 0.5,
            "explained": 0.75,  # Was "structured" 
            "demonstrated": 1.0 # Was "comprehensive"
        }.get(scaffolding_level, 0.5)
        client.create_score(
            trace_id=trace_id,
            name="scaffolding_level",
            value=scaffolding_numeric,
            comment=f"Level: {scaffolding_level}"
        )
        logger.debug(f"Langfuse score: scaffolding_level = {scaffolding_level}")
        
        # Score 5: Intent Classification (for routing analytics)
        intent = state.get("intent", "fast")
        intent_scores = {"tutor": 1.0, "math": 0.75, "coder": 0.5, "syllabus_query": 0.25, "fast": 0.0}
        client.create_score(
            trace_id=trace_id,
            name="intent_complexity",
            value=intent_scores.get(intent, 0.5),
            comment=f"Intent: {intent}"
        )
        
        # Score 6: Concept detected (NEW - for mastery analytics)
        detected_concept = evaluation.get("detected_concept")
        if detected_concept:
            client.create_score(
                trace_id=trace_id,
                name="concept_coverage",
                value=1.0,
                comment=f"Concept: {detected_concept}"
            )
        
    except Exception as e:
        logger.warning(f"Error creating Langfuse scores: {e}")


def calculate_pedagogical_score(state: AgentState, evaluation: Dict) -> float:
    """
    Calculate pedagogical quality score based on multiple factors.
    
    Factors:
    - Intent routing (tutor > math > coder > fast)
    - Scaffolding level used
    - Response structure (sources, explanations)
    - Evaluation confidence
    
    Returns:
        Score between 0 and 1
    """
    score = 0.5  # Base score
    
    # Intent-based scoring (more pedagogical intents score higher)
    intent = state.get("intent", "fast")
    intent_boost = {
        "tutor": 0.2,    # Socratic method
        "math": 0.15,    # Step-by-step reasoning
        "coder": 0.1,    # Code explanation
        "syllabus_query": 0.05,
        "fast": 0.0
    }
    score += intent_boost.get(intent, 0.0)
    
    # Scaffolding level bonus - FIX: Use correct level names
    scaffolding = state.get("scaffolding_level")
    if scaffolding:
        scaffolding_boost = {
            "hint": 0.05,        # Was "minimal"
            "guided": 0.1,
            "explained": 0.15,   # Was "structured"
            "demonstrated": 0.2  # Was "comprehensive"
        }
        score += scaffolding_boost.get(scaffolding, 0.0)
    
    # Source citation bonus
    sources = state.get("response_sources", [])
    if sources:
        score += min(0.1, len(sources) * 0.02)  # Max 0.1 for 5+ sources
    
    # Evaluation quality breakdown contribution
    quality_breakdown = evaluation.get("quality_breakdown", {})
    if quality_breakdown:
        # Add weighted contribution from quality breakdown
        structure = quality_breakdown.get("structure", 0)
        questions = quality_breakdown.get("socratic_questions", 0)
        score += (structure * 0.05) + (questions * 0.05)
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, score))


def evaluator_node(state: AgentState) -> AgentState:
    """
    Evaluator node for LangGraph with observability and mastery tracking
    
    Responsibilities:
    1. Evaluate tutor response quality (not student answers)
    2. Detect concept from query for mastery tracking
    3. Log interaction to Supabase `interactions` table
    4. Update student mastery in Supabase `student_mastery` table
    5. Create Langfuse scores for analytics dashboard
    
    Performance optimization:
    - For fast/syllabus_query intents, perform lightweight evaluation only
    - Full evaluation with repair suggestions only for tutor/explain intents
    """
    logger.info("📊 Evaluator: Analyzing response quality and updating mastery")
    start_time = time.time()
    
    trace_id = state.get("trace_id")
    user_id = state.get("user_id")
    query = state.get("query", "")
    response = state.get("response", "")
    # Ensure intent is always set - prefer reasoning_intent if intent is not set
    intent = state.get("intent") or state.get("reasoning_intent") or "fast"
    scaffolding_level = state.get("scaffolding_level")
    
    # Performance: Lightweight evaluation for simple queries
    is_lightweight = intent in ["fast", "syllabus_query"]
    
    logger.debug(f"📊 Evaluator state: intent={intent}, reasoning_intent={state.get('reasoning_intent')}, response_len={len(response) if response else 0}, lightweight={is_lightweight}")
    confusion_detected = state.get("student_confusion_detected", False)
    retrieved_context = state.get("retrieved_context", [])
    
    # Create observation span as a child of the root trace (v3 pattern)
    # Uses parent_span.start_span() for proper nesting instead of trace_context
    observation = create_child_span_from_state(
        state=state,
        name="mastery_verification_evaluator",
        input_data={
            "query": query,
            "response_preview": response[:100] + "..." if response else "",
            "user_context": state.get("user_role")
        },
        metadata={
            "component": "evaluator",
            "evaluation_framework": "pedagogical_quality"
        }
    )

    # Step 1: Detect concept from query for mastery tracking
    detected_concept = detect_concept_from_query(query)
    
    # Step 2: Detect misconceptions in student query
    # Skip heavy analysis for lightweight mode
    if is_lightweight:
        detected_misconceptions = []  # Skip misconception detection for fast queries
    else:
        detected_misconceptions = detect_misconceptions(query)
    
    # Step 3: Evaluate TUTOR response quality (not student answer)
    evaluator = ResponseQualityEvaluator()
    
    if is_lightweight:
        # Lightweight evaluation: just basic checks
        evaluation = {
            "passed": len(response) > 50,
            "confidence": 0.7 if len(response) > 100 else 0.5,
            "quality_breakdown": {"structure": 0.7, "relevance": 0.7},
            "feedback": "Quick response mode",
            "pedagogical_quality": 0.6,
            "is_lightweight": True
        }
        logger.debug("📊 Evaluator: Using lightweight evaluation for fast intent")
    else:
        evaluation = evaluator.evaluate_response_quality(
            response=response,
            scaffolding_level=scaffolding_level,
            confusion_detected=confusion_detected,
            retrieved_context=retrieved_context
        )
    
    # Add agent metadata to evaluation with friendly display name
    evaluation["agent_used"] = AGENT_DISPLAY_NAMES.get(intent, intent.replace("_", " ").title())
    evaluation["scaffolding_level"] = scaffolding_level
    evaluation["detected_concept"] = detected_concept
    evaluation["misconceptions"] = detected_misconceptions
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000
    
    # Step 4: Log interaction to Supabase (synchronous for reliability)
    # Instrumented with Langfuse span for observability
    interaction_span = create_child_span_from_state(
        state=state,
        name="log_interaction_supabase",
        input_data={"user_id": user_id[:8] if user_id else None, "concept": detected_concept},
        metadata={"span_type": "TOOL"}
    )
    try:
        # Determine outcome based on confusion and response quality
        # Valid outcomes: 'correct', 'incorrect', 'confusion_detected', 'passive_read'
        if confusion_detected:
            outcome = "confusion_detected"
        else:
            outcome = "correct" if evaluation["passed"] else "incorrect"
        
        # Map scaffolding level to DB-compatible values
        # DB allows: 'hint', 'example', 'guided', 'explain', 'explained', 'demonstrated', 'activation', 'socratic', 'verification', NULL
        scaffolding_map = {
            "hint": "hint",
            "guided": "guided",
            "explained": "explained",
            "demonstrated": "demonstrated",
            "activation": "activation",
            "socratic": "socratic",
        }
        db_scaffolding = scaffolding_map.get(scaffolding_level) if scaffolding_level else None
        
        # Use synchronous logging for reliability
        log_result = log_interaction_to_supabase_sync(
            user_id=user_id,
            interaction_type="question_asked",
            concept_focus=detected_concept,
            outcome=outcome,
            intent=intent,
            agent_used=intent,
            scaffolding_level=db_scaffolding,
            query=query,
            response_preview=response[:200] if response else "",
            misconceptions=detected_misconceptions
        )
        if log_result:
            logger.info(f"✅ Interaction logged successfully for user {user_id[:8] if user_id else 'none'}...")
            if interaction_span:
                interaction_span.update(output={"logged": True, "outcome": outcome}, level="DEFAULT")
        else:
            logger.debug("Interaction not logged (no user_id or Supabase not configured)")
            if interaction_span:
                interaction_span.update(output={"logged": False, "reason": "no user_id or Supabase not configured"}, level="DEFAULT")
    except Exception as e:
        logger.warning(f"Could not log interaction: {e}")
        if interaction_span:
            interaction_span.update(output={"error": str(e)}, level="ERROR")
    finally:
        if interaction_span:
            interaction_span.end()
    
    # Step 5: Update student mastery if concept detected
    # Instrumented with Langfuse span for observability
    if detected_concept and user_id:
        mastery_span = create_child_span_from_state(
            state=state,
            name="update_mastery",
            input_data={
                "user_id": user_id[:8] if user_id else None,
                "concept": detected_concept,
                "confidence": evaluation.get("confidence", 0.5)
            },
            metadata={"span_type": "TOOL"}
        )
        try:
            mastery_result = update_student_mastery_sync(
                user_id=user_id,
                concept_tag=detected_concept,
                evaluation_confidence=evaluation.get("confidence", 0.5)
            )
            if mastery_result:
                logger.info(f"✅ Mastery updated for concept: {detected_concept}")
                if mastery_span:
                    mastery_span.update(
                        output={"updated": True, "concept": detected_concept},
                        level="DEFAULT"
                    )
        except Exception as e:
            logger.warning(f"Could not update mastery: {e}")
            if mastery_span:
                mastery_span.update(output={"error": str(e)}, level="ERROR")
        finally:
            if mastery_span:
                mastery_span.end()
    
    # Update processing times
    processing_times = state.get("processing_times", {})
    processing_times["evaluator"] = processing_time
    state["processing_times"] = processing_times
    
    # Store evaluation in state
    state["evaluation"] = evaluation
    
    # Step 5: Create Langfuse scores for analytics dashboard
    create_langfuse_scores(trace_id, state, evaluation)
    
    # Update observation
    if observation:
        update_observation_with_usage(
            observation,
            output_data={
                "evaluation_result": evaluation,
                "agent_used": intent,
                "scaffolding_level": scaffolding_level,
                "detected_concept": detected_concept,
                "processing_metrics": {
                    "duration_ms": processing_time,
                    "quality_score": evaluation.get("confidence", 0)
                },
                "scores_created": [
                    "pedagogical_quality",
                    "policy_compliance", 
                    "response_confidence",
                    "scaffolding_level",
                    "intent_complexity",
                    "concept_coverage"
                ],
                "mastery_updated": detected_concept is not None and user_id is not None
            },
            level="DEFAULT" if evaluation["passed"] else "WARNING",
            latency_seconds=processing_time / 1000.0
        )
        observation.end()
    
    logger.info(f"📊 Evaluator: {'✓ Good' if evaluation['passed'] else '⚠ Needs work'} "
                f"(quality={evaluation['confidence']:.2f}, concept={detected_concept or 'none'}) "
                f"({processing_time:.1f}ms)")
    
    return state


def calculate_mastery_score(
    previous_score: float,
    evaluation_confidence: float,
    decay_factor: float = 0.95
) -> float:
    """
    Calculate updated mastery score
    
    Args:
        previous_score: Previous mastery score (0-1)
        evaluation_confidence: Confidence from evaluation (0-1)
        decay_factor: Decay factor for forgetting curve
        
    Returns:
        Updated mastery score (0-1)
    """
    # Weighted average with decay
    # New interactions have more weight
    new_score = (previous_score * decay_factor + evaluation_confidence * (1 - decay_factor))
    
    # Ensure score stays in [0, 1]
    return max(0.0, min(1.0, new_score))

