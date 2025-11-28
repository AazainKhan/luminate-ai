"""
Governor (Policy Engine) for Course Marshal
Enforces course policies and constraints
"""

from typing import Dict, List
import logging
import time
from app.agents.state import AgentState
from app.rag.langchain_chroma import get_langchain_chroma_client
from app.observability.langfuse_client import (
    create_observation, 
    update_observation_with_usage
)

logger = logging.getLogger(__name__)


class Governor:
    """
    Policy Engine that enforces course rules:
    - Law 1: Scope enforcement (only COMP 237 topics)
    - Law 2: Integrity enforcement (no full solutions for graded components)
    - Law 3: Mastery enforcement (requires verification)
    """

    def __init__(self):
        self.vectorstore = get_langchain_chroma_client()
        self.course_id = "COMP237"

    def check_policies(self, state: AgentState) -> Dict[str, any]:
        """
        Check all policies and return approval status
        
        Args:
            state: Current agent state
            
        Returns:
            Dictionary with approval status and reason
        """
        query = state.get("query", "")
        
        # Law 1: Scope Check
        scope_check = self._check_scope(query)
        if not scope_check["approved"]:
            return {
                "approved": False,
                "reason": scope_check["reason"],
                "law_violated": "scope",
            }
        
        # Law 2: Integrity Check (check if query asks for full solution)
        integrity_check = self._check_integrity(query)
        if not integrity_check["approved"]:
            return {
                "approved": False,
                "reason": integrity_check["reason"],
                "law_violated": "integrity",
            }
        
        # Law 3: Mastery Check (will be enforced by Evaluator Node in Feature 11)
        # For now, always approve
        
        return {
            "approved": True,
            "reason": "All policies satisfied",
            "law_violated": None,
        }

    def _check_scope(self, query: str) -> Dict[str, any]:
        """
        Law 1: Check if query is within COMP 237 scope
        Uses ChromaDB distance scores to determine relevance.
        
        Note on scoring: ChromaDB returns L2 distance by default.
        Lower scores = more relevant (closer vectors).
        - In-scope queries typically score 0.3-0.7
        - Out-of-scope queries typically score 0.8+
        
        Returns:
            Dictionary with approval status
        """
        # Query vector store to see if relevant content exists
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=3,
                filter={"course_id": self.course_id}
            )
            
            # If no relevant results, might be out of scope
            if not results:
                return {
                    "approved": False,
                    "reason": "This topic is not covered in COMP 237. Please ask about course content.",
                }
            
            # Check if results are relevant (lower score = more relevant)
            min_score = min(score for _, score in results)
            avg_score = sum(score for _, score in results) / len(results)
            
            # Threshold tuned based on empirical testing:
            # - In-scope queries (e.g., "What is backpropagation?"): ~0.60
            # - Edge case AI queries (e.g., "softmax function"): ~0.77
            # - Out-of-scope queries (e.g., "What is the capital of France?"): ~0.90
            # Using 0.80 as threshold to include edge-case AI topics
            SCOPE_THRESHOLD = 0.80
            
            if min_score > SCOPE_THRESHOLD:
                logger.info(f"❌ Scope check failed (min_score: {min_score:.3f}, avg: {avg_score:.3f}, threshold: {SCOPE_THRESHOLD})")
                return {
                    "approved": False,
                    "reason": "This topic is not clearly covered in COMP 237. Please ask about course content like machine learning, neural networks, or AI concepts from your course materials.",
                }
            
            logger.info(f"✅ Scope check passed (min_score: {min_score:.3f}, avg: {avg_score:.3f}, threshold: {SCOPE_THRESHOLD})")
            return {
                "approved": True,
                "reason": "Topic is within course scope",
            }
        except Exception as e:
            logger.error(f"❌ Error checking scope: {e}")
            # On error, allow but log
            return {
                "approved": True,
                "reason": "Scope check error, allowing query",
            }

    def _check_integrity(self, query: str) -> Dict[str, any]:
        """
        Law 2: Check if query requests full solution for graded work
        
        Returns:
            Dictionary with approval status
        """
        query_lower = query.lower()
        
        # Keywords that suggest asking for full solution
        integrity_keywords = [
            "give me the code",
            "write the full",
            "complete solution",
            "do my assignment",
            "solve this for me",
            "just give me the answer",
            "full script",
            "complete code",
        ]
        
        # Check for integrity violations
        for keyword in integrity_keywords:
            if keyword in query_lower:
                return {
                    "approved": False,
                    "reason": "I cannot provide complete solutions for graded assignments. I can help you understand concepts and provide guidance instead.",
                }
        
        return {
            "approved": True,
            "reason": "Query does not violate academic integrity",
        }


def governor_node(state: AgentState) -> AgentState:
    """
    Governor node for LangGraph with comprehensive observability
    Checks policies before allowing query to proceed
    """
    logger.info("Governor: Enforcing course policies")
    start_time = time.time()
    
    # Create guardrail observation if we have a trace context
    observation = None
    trace_id = state.get("trace_id")
    if trace_id:
        from app.observability.langfuse_client import get_langfuse_client
        client = get_langfuse_client()
        if client:
            try:
                # Create guardrail observation for policy enforcement linked to the trace
                observation = client.start_span(
                    trace_context={"trace_id": trace_id},
                    name="policy_enforcement_guardrail",
                    input={
                        "query": state.get("query"),
                        "user_context": {
                            "user_id": state.get("user_id"),
                            "user_role": state.get("user_role")
                        }
                    },
                    metadata={
                        "component": "governor",
                        "policy_framework": "three_laws_compliance"
                    }
                )
            except Exception as e:
                logger.warning(f"Could not create governor observation: {e}")
    
    governor = Governor()
    policy_check = governor.check_policies(state)
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000  # milliseconds
    
    # Store policy decision history
    policy_decisions = state.get("policy_decisions", [])
    policy_decisions.append({
        "timestamp": time.time(),
        "decision": policy_check,
        "processing_time_ms": processing_time,
        "laws_evaluated": ["scope", "integrity", "mastery"]
    })
    
    # Update processing times tracking
    processing_times = state.get("processing_times", {})
    processing_times["governor"] = processing_time
    
    # Update state
    state["governor_approved"] = policy_check["approved"]
    state["governor_reason"] = policy_check["reason"]
    state["policy_decisions"] = policy_decisions
    state["processing_times"] = processing_times
    
    if not policy_check["approved"]:
        # Set error response for policy violation
        state["error"] = policy_check["reason"]
        state["response"] = f"Policy Violation: {policy_check['reason']}"
    
    # Update observation with comprehensive results
    if observation:
        update_observation_with_usage(
            observation,
            output_data={
                "policy_decision": policy_check,
                "compliance_status": "approved" if policy_check["approved"] else "violated",
                "processing_metrics": {
                    "duration_ms": processing_time,
                    "laws_checked": 3,
                    "violation_category": policy_check.get("law_violated")
                }
            },
            level="WARNING" if not policy_check["approved"] else "DEFAULT",
            latency_seconds=processing_time / 1000.0
        )
        observation.end()
    
    logger.info(f"Governor: {'✓ Approved' if policy_check['approved'] else '✗ Blocked'} - {policy_check.get('reason', '')} ({processing_time:.1f}ms)")
    
    return state

