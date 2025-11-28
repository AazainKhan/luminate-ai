"""
Evaluator Node for Student Mastery Verification
Implements 3-step verification loop (Passive Validation, Active Validation, Outcome Alignment)
"""

from typing import Dict, Optional, List
import logging
import time
from app.agents.state import AgentState
from app.observability.langfuse_client import (
    create_observation,
    update_observation_with_usage
)

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Evaluates student responses to determine mastery
    Uses proof-of-work protocol based on Bloom's Taxonomy levels
    """

    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize evaluator
        
        Args:
            confidence_threshold: Minimum confidence score to mark as mastered (0-1)
        """
        self.confidence_threshold = confidence_threshold

    def evaluate_response(
        self,
        user_response: str,
        expected_concept: str,
        question_type: str = "recall"
    ) -> Dict[str, any]:
        """
        Evaluate student response
        
        Args:
            user_response: Student's response text
            expected_concept: Concept being tested
            question_type: Type of question (recall, application, evaluation)
            
        Returns:
            Dictionary with evaluation results
        """
        # This is a simplified evaluator
        # In production, this would use an LLM to evaluate the response
        
        # For now, basic keyword matching and length check
        response_lower = user_response.lower()
        
        # Check if response is substantial (not just "yes" or "no")
        if len(user_response.strip()) < 10:
            return {
                "confidence": 0.2,
                "passed": False,
                "feedback": "Your response is too brief. Please provide more detail.",
                "level": "insufficient",
            }
        
        # Check for common correct indicators
        correct_indicators = ["correct", "right", "yes", "true", "understand"]
        incorrect_indicators = ["wrong", "incorrect", "no", "false", "don't know"]
        
        has_correct = any(indicator in response_lower for indicator in correct_indicators)
        has_incorrect = any(indicator in response_lower for indicator in incorrect_indicators)
        
        # Simple heuristic: longer responses with correct indicators score higher
        if has_correct and not has_incorrect:
            confidence = min(0.9, 0.5 + (len(user_response) / 100))
        elif has_incorrect:
            confidence = 0.3
        else:
            confidence = 0.5  # Neutral
        
        passed = confidence >= self.confidence_threshold
        
        return {
            "confidence": confidence,
            "passed": passed,
            "feedback": "Good response!" if passed else "Please try to explain more clearly.",
            "level": "mastered" if passed else "developing",
        }

    def evaluate_code(
        self,
        code: str,
        test_cases: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        Evaluate code submission
        
        Args:
            code: Student's code
            test_cases: Optional test cases to run
            
        Returns:
            Dictionary with evaluation results
        """
        # Basic code evaluation
        # In production, would run test cases
        
        if not code or len(code.strip()) < 10:
            return {
                "confidence": 0.2,
                "passed": False,
                "feedback": "Code submission is too short.",
            }
        
        # Check for basic Python syntax indicators
        has_function = "def " in code or "function" in code.lower()
        has_logic = any(keyword in code for keyword in ["if", "for", "while", "return"])
        
        confidence = 0.5
        if has_function:
            confidence += 0.2
        if has_logic:
            confidence += 0.2
        
        confidence = min(0.9, confidence)
        passed = confidence >= self.confidence_threshold
        
        return {
            "confidence": confidence,
            "passed": passed,
            "feedback": "Code looks good!" if passed else "Try adding more functionality.",
        }


def evaluator_node(state: AgentState) -> AgentState:
    """
    Evaluator node for LangGraph with observability
    Evaluates student responses and updates mastery scores
    """
    logger.info("Evaluator: Verifying mastery and quality")
    start_time = time.time()
    
    # Create observation
    observation = None
    trace_id = state.get("trace_id")
    if trace_id:
        from app.observability.langfuse_client import get_langfuse_client
        client = get_langfuse_client()
        if client:
            try:
                observation = client.start_span(
                    trace_context={"trace_id": trace_id},
                    name="mastery_verification_evaluator",
                    input={
                        "query": state.get("query"),
                        "response_preview": state.get("response", "")[:100] + "...",
                        "user_context": state.get("user_role")
                    },
                    metadata={
                        "component": "evaluator",
                        "evaluation_framework": "pedagogical_quality"
                    }
                )
            except Exception as e:
                logger.warning(f"Could not create evaluator observation: {e}")

    evaluator = Evaluator()
    
    # This would be called after student interaction
    # For now, it's a placeholder that will be integrated with Feature 11
    
    # Extract concept from query or context
    query = state.get("query", "")
    intent = state.get("intent", "fast")  # Track which agent was used
    scaffolding_level = state.get("scaffolding_level", None)  # Track scaffolding
    
    # In production, would extract concept tags from query
    
    # Evaluate (placeholder - would use actual student response)
    evaluation = evaluator.evaluate_response(
        user_response=state.get("response", ""),  # Use actual response from state
        expected_concept="",
        question_type="recall"
    )
    
    # Add agent metadata to evaluation
    evaluation["agent_used"] = intent
    evaluation["scaffolding_level"] = scaffolding_level
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000
    
    # Update processing times
    processing_times = state.get("processing_times", {})
    processing_times["evaluator"] = processing_time
    state["processing_times"] = processing_times
    
    # Store evaluation in state
    state["evaluation"] = evaluation
    
    # Update observation
    if observation:
        update_observation_with_usage(
            observation,
            output_data={
                "evaluation_result": evaluation,
                "agent_used": intent,
                "scaffolding_level": scaffolding_level,
                "processing_metrics": {
                    "duration_ms": processing_time,
                    "quality_score": evaluation.get("confidence", 0)
                }
            },
            level="DEFAULT" if evaluation["passed"] else "WARNING",
            latency_seconds=processing_time / 1000.0
        )
        observation.end()
    
    logger.info(f"Evaluator: {'✓ Passed' if evaluation['passed'] else '⚠ Flagged'} ({processing_time:.1f}ms)")
    
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

