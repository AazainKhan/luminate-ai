"""
Knowledge Graph for COMP 237 Course Concepts

This module provides functions to:
1. Get concept prerequisites
2. Suggest next topics based on mastery
3. Build learning paths
"""

import logging
from typing import List, Optional, Dict
from app.config import settings

logger = logging.getLogger(__name__)


# Hardcoded concept relationships for fast lookup
# Maps concept_id -> list of concepts that build on it
CONCEPT_UNLOCKS = {
    # What you unlock after mastering each concept
    "ml_basics": ["supervised_learning", "unsupervised_learning"],
    "supervised_learning": ["classification", "regression", "model_evaluation"],
    "unsupervised_learning": ["clustering"],
    "classification": ["decision_trees", "knn", "svm", "naive_bayes", "logistic_regression"],
    "regression": ["linear_regression"],
    "linear_regression": ["polynomial_regression", "regularization"],
    "clustering": ["kmeans", "hierarchical", "dbscan"],
    "neural_networks": ["perceptron"],
    "perceptron": ["activation_functions", "backpropagation"],
    "backpropagation": ["deep_learning"],
    "probability": ["bayes_theorem", "conditional_probability", "optimization"],
    "bayes_theorem": ["prior_posterior", "naive_bayes"],
    "optimization": ["gradient_descent", "loss_functions"],
    "gradient_descent": ["learning_rate", "backpropagation"],
    "data_preprocessing": ["normalization", "feature_engineering", "train_test_split"],
}

# Concept display names
CONCEPT_NAMES = {
    "machine_learning": "Machine Learning",
    "neural_networks": "Neural Networks",
    "probability": "Probability & Statistics",
    "optimization": "Optimization",
    "data_preprocessing": "Data Preprocessing",
    "ml_basics": "ML Fundamentals",
    "supervised_learning": "Supervised Learning",
    "unsupervised_learning": "Unsupervised Learning",
    "model_evaluation": "Model Evaluation",
    "classification": "Classification",
    "regression": "Regression",
    "decision_trees": "Decision Trees",
    "knn": "K-Nearest Neighbors",
    "svm": "Support Vector Machines",
    "naive_bayes": "Naive Bayes",
    "logistic_regression": "Logistic Regression",
    "linear_regression": "Linear Regression",
    "polynomial_regression": "Polynomial Regression",
    "regularization": "Regularization",
    "clustering": "Clustering",
    "kmeans": "K-Means Clustering",
    "hierarchical": "Hierarchical Clustering",
    "dbscan": "DBSCAN",
    "perceptron": "Perceptron",
    "backpropagation": "Backpropagation",
    "activation_functions": "Activation Functions",
    "deep_learning": "Deep Learning",
    "bayes_theorem": "Bayes' Theorem",
    "conditional_probability": "Conditional Probability",
    "prior_posterior": "Prior & Posterior",
    "gradient_descent": "Gradient Descent",
    "loss_functions": "Loss Functions",
    "learning_rate": "Learning Rate",
    "normalization": "Normalization",
    "feature_engineering": "Feature Engineering",
    "train_test_split": "Train/Test Split",
}


async def get_student_mastery_all(user_id: str) -> Dict[str, float]:
    """
    Fetch all mastery scores for a student.
    
    Returns:
        Dict mapping concept_tag to mastery_score
    """
    if not user_id:
        return {}
    
    try:
        from supabase import create_client
        
        if not settings.supabase_url or not settings.supabase_service_role_key:
            return {}
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        result = supabase.table("student_mastery").select(
            "concept_tag, mastery_score"
        ).eq("user_id", user_id).execute()
        
        if result.data:
            return {row["concept_tag"]: row["mastery_score"] for row in result.data}
        
        return {}
        
    except Exception as e:
        logger.debug(f"Could not fetch mastery: {e}")
        return {}


async def get_recent_interactions(user_id: str, limit: int = 10) -> List[Dict]:
    """
    Fetch recent interactions for a student to provide context about what they've studied.
    
    Returns:
        List of recent interactions with concept, outcome, timestamp
    """
    if not user_id:
        return []
    
    try:
        from supabase import create_client
        
        if not settings.supabase_url or not settings.supabase_service_role_key:
            return []
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        result = supabase.table("interactions").select(
            "concept_focus, outcome, scaffolding_level, created_at, metadata"
        ).eq("student_id", user_id).order(
            "created_at", desc=True
        ).limit(limit).execute()
        
        if result.data:
            return result.data
        
        return []
        
    except Exception as e:
        logger.debug(f"Could not fetch recent interactions: {e}")
        return []


def format_student_history(
    mastery_scores: Dict[str, float],
    recent_interactions: List[Dict],
    current_concept: Optional[str] = None
) -> str:
    """
    Format student history into a readable context for the tutor.
    
    Args:
        mastery_scores: Dict of concept_tag -> mastery_score
        recent_interactions: List of recent interaction records
        current_concept: The concept being asked about (for highlighting)
        
    Returns:
        Formatted string describing student's learning history
    """
    parts = []
    
    # Part 1: Overall mastery summary
    if mastery_scores:
        strong = [(k, v) for k, v in mastery_scores.items() if v >= 0.6]
        moderate = [(k, v) for k, v in mastery_scores.items() if 0.3 <= v < 0.6]
        weak = [(k, v) for k, v in mastery_scores.items() if v < 0.3]
        
        parts.append("## 📊 Student Learning History")
        parts.append("")
        
        if strong:
            strong_names = [CONCEPT_NAMES.get(c, c.replace("_", " ").title()) for c, _ in strong]
            parts.append(f"✅ **Strong mastery:** {', '.join(strong_names)}")
        
        if moderate:
            moderate_names = [CONCEPT_NAMES.get(c, c.replace("_", " ").title()) for c, _ in moderate]
            parts.append(f"📈 **Building understanding:** {', '.join(moderate_names)}")
        
        if weak:
            weak_names = [CONCEPT_NAMES.get(c, c.replace("_", " ").title()) for c, _ in weak]
            parts.append(f"📝 **Needs reinforcement:** {', '.join(weak_names)}")
        
        # Check if current concept was previously studied
        if current_concept and current_concept in mastery_scores:
            score = mastery_scores[current_concept]
            concept_name = CONCEPT_NAMES.get(current_concept, current_concept.replace("_", " ").title())
            if score >= 0.6:
                parts.append(f"\n💡 **Note:** Student has studied **{concept_name}** before and has strong mastery ({int(score*100)}%).")
                parts.append("   → Consider building on prior knowledge and going deeper.")
            elif score >= 0.3:
                parts.append(f"\n💡 **Note:** Student has some familiarity with **{concept_name}** ({int(score*100)}%).")
                parts.append("   → Ask if they want a refresher: 'We covered this before. Want to review the key points?'")
            else:
                parts.append(f"\n💡 **Note:** Student struggled with **{concept_name}** previously ({int(score*100)}%).")
                parts.append("   → Offer to re-explain: 'I know this was tricky before. Let's try a different approach!'")
        
        parts.append("")
    
    # Part 2: Recent learning sessions
    if recent_interactions:
        from datetime import datetime, timezone
        
        parts.append("## 🕐 Recent Learning Activity")
        parts.append("")
        
        # Group interactions by concept
        concept_sessions = {}
        for interaction in recent_interactions:
            concept = interaction.get("concept_focus")
            if not concept:
                continue
            
            if concept not in concept_sessions:
                concept_sessions[concept] = {
                    "count": 0,
                    "outcomes": [],
                    "last_seen": None,
                    "scaffolding_levels": []
                }
            
            concept_sessions[concept]["count"] += 1
            concept_sessions[concept]["outcomes"].append(interaction.get("outcome", "unknown"))
            
            if interaction.get("scaffolding_level"):
                concept_sessions[concept]["scaffolding_levels"].append(interaction.get("scaffolding_level"))
            
            # Track last seen
            if interaction.get("created_at"):
                try:
                    created_str = interaction["created_at"]
                    # Handle various datetime formats from Supabase
                    if "Z" in created_str:
                        created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    elif "+" in created_str or created_str.endswith("00"):
                        created = datetime.fromisoformat(created_str)
                    else:
                        # No timezone info - assume UTC
                        created = datetime.fromisoformat(created_str).replace(tzinfo=timezone.utc)
                    
                    if not concept_sessions[concept]["last_seen"] or created > concept_sessions[concept]["last_seen"]:
                        concept_sessions[concept]["last_seen"] = created
                except Exception as e:
                    logger.debug(f"Could not parse datetime: {e}")
        
        # Format recent sessions
        now = datetime.now(timezone.utc)
        for concept, data in list(concept_sessions.items())[:5]:  # Top 5 recent concepts
            concept_name = CONCEPT_NAMES.get(concept, concept.replace("_", " ").title())
            
            # Calculate time since last interaction
            time_ago = ""
            if data["last_seen"]:
                try:
                    # Ensure both datetimes are timezone-aware
                    last_seen = data["last_seen"]
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                    
                    delta = now - last_seen
                    if delta.days > 0:
                        time_ago = f" ({delta.days} days ago)"
                    elif delta.seconds > 3600:
                        time_ago = f" ({delta.seconds // 3600} hours ago)"
                    else:
                        time_ago = " (recently)"
                except Exception as e:
                    logger.debug(f"Could not calculate time delta: {e}")
                    time_ago = ""
            
            # Determine outcome summary
            confusion_count = data["outcomes"].count("confusion_detected")
            correct_count = data["outcomes"].count("correct")
            
            outcome_icon = "✅" if confusion_count == 0 else "⚠️" if confusion_count < 2 else "🔄"
            
            parts.append(f"  {outcome_icon} **{concept_name}**{time_ago} - {data['count']} interaction(s)")
            
            if confusion_count > 0:
                parts.append(f"      → Student showed confusion {confusion_count} time(s). Consider offering to review.")
        
        parts.append("")
    
    if not mastery_scores and not recent_interactions:
        return ""
    
    return "\n".join(parts)


def get_next_concepts(
    current_concept: str,
    mastery_scores: Dict[str, float],
    max_suggestions: int = 3
) -> List[Dict]:
    """
    Suggest next concepts to learn based on current concept and mastery.
    
    Args:
        current_concept: The concept the student just learned about
        mastery_scores: Dict of concept_tag -> mastery_score
        max_suggestions: Maximum number of suggestions
        
    Returns:
        List of dicts with concept info: [{id, name, reason, ready}]
    """
    suggestions = []
    
    # Get concepts that this one unlocks
    unlocked = CONCEPT_UNLOCKS.get(current_concept, [])
    
    for concept_id in unlocked:
        # Check if student has high mastery of prerequisites
        current_mastery = mastery_scores.get(current_concept, 0.0)
        concept_mastery = mastery_scores.get(concept_id, 0.0)
        
        # Skip if already mastered
        if concept_mastery > 0.8:
            continue
        
        # Check if ready (current concept mastered enough)
        ready = current_mastery >= 0.5
        
        suggestions.append({
            "id": concept_id,
            "name": CONCEPT_NAMES.get(concept_id, concept_id),
            "reason": f"Builds on {CONCEPT_NAMES.get(current_concept, current_concept)}",
            "ready": ready,
            "current_mastery": concept_mastery
        })
    
    # Sort by readiness and current mastery (prefer concepts student has started)
    suggestions.sort(key=lambda x: (not x["ready"], -x["current_mastery"]))
    
    return suggestions[:max_suggestions]


def get_prerequisite_gaps(
    target_concept: str,
    mastery_scores: Dict[str, float],
    min_mastery: float = 0.5
) -> List[Dict]:
    """
    Find concepts the student needs to master before learning target concept.
    
    Returns:
        List of concepts with low mastery that are prerequisites
    """
    gaps = []
    
    # Find which concepts unlock the target
    for prereq, unlocks in CONCEPT_UNLOCKS.items():
        if target_concept in unlocks:
            mastery = mastery_scores.get(prereq, 0.0)
            if mastery < min_mastery:
                gaps.append({
                    "id": prereq,
                    "name": CONCEPT_NAMES.get(prereq, prereq),
                    "current_mastery": mastery,
                    "needed_mastery": min_mastery,
                    "gap": min_mastery - mastery
                })
    
    # Sort by gap size (largest gaps first)
    gaps.sort(key=lambda x: -x["gap"])
    
    return gaps


def format_next_concepts_message(suggestions: List[Dict]) -> str:
    """
    Format next concept suggestions as a friendly message.
    """
    if not suggestions:
        return ""
    
    lines = ["\n\n📚 **What to learn next:**"]
    
    for i, concept in enumerate(suggestions, 1):
        ready_icon = "✅" if concept["ready"] else "⏳"
        lines.append(f"{ready_icon} **{concept['name']}** - {concept['reason']}")
    
    return "\n".join(lines)


def format_prereq_gaps_message(gaps: List[Dict]) -> str:
    """
    Format prerequisite gaps as a friendly message.
    """
    if not gaps:
        return ""
    
    lines = ["\n\n⚠️ **Before diving deeper, you might want to review:**"]
    
    for gap in gaps[:3]:  # Show top 3 gaps
        progress = int(gap["current_mastery"] * 100)
        lines.append(f"- **{gap['name']}** (current: {progress}%)")
    
    return "\n".join(lines)


# ============================================================================
# STUDENT HISTORY FUNCTIONS
# Fetch and format recent student interactions for context-aware tutoring
# ============================================================================

def get_recent_student_interactions(user_id: str, limit: int = 10) -> List[Dict]:
    """
    Fetch recent student interactions from Supabase.
    Returns a list of recent learning interactions with concept, outcome, and timestamp.
    
    Args:
        user_id: The student's UUID
        limit: Maximum number of interactions to fetch
        
    Returns:
        List of interaction dictionaries with keys:
        - concept_focus: The concept covered
        - outcome: 'correct', 'incorrect', 'confusion_detected', 'passive_read'
        - scaffolding_level: The scaffolding used
        - created_at: Timestamp
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        if not settings.supabase_service_role_key:
            logger.warning("SUPABASE_SERVICE_ROLE_KEY not configured")
            return []
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        # Fetch recent interactions for this student
        response = supabase.table("interactions").select(
            "concept_focus, outcome, scaffolding_level, created_at, type"
        ).eq(
            "student_id", user_id
        ).order(
            "created_at", desc=True
        ).limit(limit).execute()
        
        if response.data:
            logger.info(f"Fetched {len(response.data)} recent interactions for user {user_id[:8]}...")
            return response.data
        
        return []
        
    except Exception as e:
        logger.error(f"Error fetching student interactions: {e}")
        return []


def get_student_mastery_scores(user_id: str) -> Dict[str, float]:
    """
    Fetch all mastery scores for a student.
    
    Args:
        user_id: The student's UUID
        
    Returns:
        Dictionary mapping concept_tag -> mastery_score (0.0 to 1.0)
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        if not settings.supabase_service_role_key:
            logger.warning("SUPABASE_SERVICE_ROLE_KEY not configured")
            return {}
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        response = supabase.table("student_mastery").select(
            "concept_tag, mastery_score, last_assessed_at"
        ).eq(
            "user_id", user_id
        ).execute()
        
        if response.data:
            return {
                row["concept_tag"]: row["mastery_score"] 
                for row in response.data
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Error fetching student mastery: {e}")
        return {}


def format_student_history(interactions: List[Dict], mastery_scores: Optional[Dict[str, float]] = None) -> str:
    """
    Format student interactions into a context string for the tutor.
    
    This provides the tutor with:
    1. What topics the student has covered
    2. When they covered them (relative time)
    3. What outcomes they had (struggles, successes)
    4. Current mastery levels
    
    Args:
        interactions: List of interaction dictionaries from get_recent_student_interactions
        mastery_scores: Optional dict of concept -> mastery score
        
    Returns:
        Formatted string describing student's learning history
    """
    if not interactions:
        return ""
    
    from datetime import datetime, timezone
    
    lines = ["## Recent Learning History"]
    
    # Group by concept
    concept_history: Dict[str, List[Dict]] = {}
    for interaction in interactions:
        concept = interaction.get("concept_focus", "general")
        if concept not in concept_history:
            concept_history[concept] = []
        concept_history[concept].append(interaction)
    
    # Format each concept's history
    for concept, history in concept_history.items():
        if concept == "general" or not concept:
            continue
            
        concept_name = CONCEPT_NAMES.get(concept, concept.replace("_", " ").title())
        
        # Get the most recent interaction
        latest = history[0]
        created_at = latest.get("created_at", "")
        
        # Calculate relative time
        try:
            if created_at:
                # Handle both ISO format with and without timezone
                if isinstance(created_at, str):
                    # Remove microseconds if present for simpler parsing
                    if "." in created_at:
                        created_at = created_at.split(".")[0]
                    if "Z" in created_at:
                        created_at = created_at.replace("Z", "+00:00")
                    if "+" not in created_at and "-" not in created_at[-6:]:
                        created_at += "+00:00"
                    
                    interaction_time = datetime.fromisoformat(created_at)
                else:
                    interaction_time = created_at
                    
                now = datetime.now(timezone.utc)
                if interaction_time.tzinfo is None:
                    interaction_time = interaction_time.replace(tzinfo=timezone.utc)
                    
                delta = now - interaction_time
                
                if delta.days == 0:
                    if delta.seconds < 3600:
                        time_ago = f"{delta.seconds // 60} minutes ago"
                    else:
                        time_ago = f"{delta.seconds // 3600} hours ago"
                elif delta.days == 1:
                    time_ago = "yesterday"
                elif delta.days < 7:
                    time_ago = f"{delta.days} days ago"
                else:
                    time_ago = f"{delta.days // 7} weeks ago"
            else:
                time_ago = "recently"
        except Exception as e:
            logger.warning(f"Error parsing timestamp: {e}")
            time_ago = "recently"
        
        # Determine outcome summary
        outcomes = [h.get("outcome", "") for h in history]
        confusion_count = outcomes.count("confusion_detected")
        incorrect_count = outcomes.count("incorrect")
        correct_count = outcomes.count("correct")
        
        if confusion_count > 0 or incorrect_count > 0:
            outcome_emoji = "⚠️"
            outcome_note = "had some difficulty"
        elif correct_count > 0:
            outcome_emoji = "✅"
            outcome_note = "understood well"
        else:
            outcome_emoji = "📖"
            outcome_note = "reviewed"
        
        # Add mastery if available
        mastery_note = ""
        if mastery_scores and concept in mastery_scores:
            score = mastery_scores[concept]
            if score >= 0.8:
                mastery_note = f" (mastery: {int(score*100)}% 🌟)"
            elif score >= 0.5:
                mastery_note = f" (mastery: {int(score*100)}%)"
            else:
                mastery_note = f" (needs review: {int(score*100)}%)"
        
        lines.append(f"- {outcome_emoji} **{concept_name}**: {outcome_note} ({time_ago}){mastery_note}")
    
    if len(lines) == 1:
        return ""  # Only header, no content
    
    return "\n".join(lines)


def get_student_context_summary(user_id: str) -> Dict:
    """
    Get a complete summary of student's learning context.
    
    Returns a dictionary with:
    - interactions: Raw list of recent interactions
    - mastery_scores: Dict of concept -> score
    - formatted_history: Human-readable history string
    - topics_covered: List of concepts the student has worked on
    - struggling_topics: List of topics with confusion/incorrect outcomes
    - strong_topics: List of topics with high mastery
    """
    interactions = get_recent_student_interactions(user_id, limit=15)
    mastery_scores = get_student_mastery_scores(user_id)
    
    # Identify struggling and strong topics
    struggling = []
    strong = []
    topics_covered = set()
    
    for interaction in interactions:
        concept = interaction.get("concept_focus", "")
        if concept and concept != "general":
            topics_covered.add(concept)
            
            outcome = interaction.get("outcome", "")
            if outcome in ["confusion_detected", "incorrect"]:
                if concept not in struggling:
                    struggling.append(concept)
    
    for concept, score in mastery_scores.items():
        if score >= 0.8:
            strong.append(concept)
    
    return {
        "interactions": interactions,
        "mastery_scores": mastery_scores,
        "formatted_history": format_student_history(interactions, mastery_scores),
        "topics_covered": list(topics_covered),
        "struggling_topics": struggling,
        "strong_topics": strong,
        "has_prior_sessions": len(interactions) > 0
    }
