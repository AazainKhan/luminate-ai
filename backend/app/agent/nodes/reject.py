"""
Reject Node - Handles off-topic and policy-violating queries

Handles rejections from both:
1. Governor (policy enforcement pre-check)
2. Planner (classification as off-topic)

Politely declines while staying helpful.
"""

import logging
from typing import Dict, Any

from app.agent.state import AgentState

logger = logging.getLogger(__name__)


REJECT_RESPONSES = {
    "off_topic": """I appreciate your question! However, this seems to be outside the scope of COMP237: Introduction to AI.

I'm designed to help you with AI and machine learning concepts covered in your course, like:
- Search algorithms (A*, BFS, DFS)
- Machine learning fundamentals
- Neural networks and deep learning
- Natural Language Processing
- Computer Vision basics

Is there something from these topics I can help you with instead?""",

    "integrity": """I understand you might be feeling stuck, but I can't provide complete solutions to assignments, labs, quizzes, or exams. That would undermine your learning and violate academic integrity.

Instead, I'm here to help you actually understand the material:
- **Explain concepts** you're struggling with
- **Walk through similar examples** step-by-step
- **Give hints** to guide your thinking
- **Debug your approach** without giving the answer

What specific concept or part would you like help understanding? I promise that working through it yourself will make you much better prepared for exams! 🎓""",

    "low_relevance": """I'm not finding strong connections between your question and COMP237 course materials.

Could you rephrase your question to be more specific about:
- The AI/ML concept you're asking about
- Which week or topic from the course this relates to
- What you've already tried or understand

This will help me give you a more relevant answer!""",

    "no_course_content": """I couldn't find related course materials for your question.

I'm optimized to help with COMP237: Introduction to AI topics like:
- Supervised & unsupervised learning
- Neural networks and backpropagation
- Search algorithms and heuristics
- NLP and text processing
- Evaluation metrics (accuracy, precision, recall)

Could you clarify which of these topics relates to your question?""",

    "general": """I'm Course Marshal, your AI tutor for COMP237: Introduction to AI.

I can help you with:
- Understanding AI/ML concepts from your course
- Working through practice problems step-by-step
- Explaining algorithms and their implementations
- Clarifying lecture material

What would you like to learn about today?""",
}


def reject_node(state: AgentState) -> Dict[str, Any]:
    """
    Reject node: handles off-topic or policy-violating queries
    
    Handles rejections from:
    1. Governor (approved=False, rejection_reason set)
    2. Planner (task=reject in plan)
    
    Returns helpful redirection response.
    """
    # Check if this is a Governor rejection (approved=False)
    if not state.get("approved", True):
        reason = state.get("rejection_reason", "off_topic")
        logger.info(f"[Reject] Governor rejection: {reason}")
    else:
        # This is a Planner rejection
        plan = state.get("plan", {})
        subtasks = plan.get("subtasks", [])
        current_subtask = subtasks[0] if subtasks else {}
        
        payload = current_subtask.get("payload", {})
        reason = payload.get("reason", "off_topic")
        logger.info(f"[Reject] Planner rejection: {reason}")
    
    # Select appropriate response based on reason
    if reason == "integrity":
        response = REJECT_RESPONSES["integrity"]
    elif reason == "low_relevance":
        response = REJECT_RESPONSES["low_relevance"]
    elif reason == "no_course_content":
        response = REJECT_RESPONSES["no_course_content"]
    elif reason in ["off_topic", "off-topic"]:
        response = REJECT_RESPONSES["off_topic"]
    else:
        response = REJECT_RESPONSES["general"]
    
    return {
        **state,
        "response": response,
        "sources": [],
        "rag_metadata": {"docs_retrieved": 0, "retrieval_success": False, "has_comp237": False},
    }
