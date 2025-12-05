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
        # Use effective_query (contextualized) if available, otherwise original query
        query = state.get("effective_query") or state.get("query", "")
        messages = state.get("messages", [])

        
        # Get reasoning output if available
        reasoning_intent = state.get("reasoning_intent")
        reasoning_confidence = state.get("reasoning_confidence", 0.0)
        key_concepts = state.get("key_concepts_detected", [])
        
        # 1. Check Integrity (Academic Honesty) - Critical, always check first
        integrity_check = self._check_integrity(query)
        if not integrity_check["approved"]:
            return {
                "approved": False,
                "reason": integrity_check["reason"],
                "law_violated": "integrity"
            }
            
        # 2. Check Scope (Course Relevance)
        # Use reasoning output to augment vector search
        scope_check = self._check_scope(query, reasoning_intent, reasoning_confidence, key_concepts)
        if not scope_check["approved"]:
            return {
                "approved": False,
                "reason": scope_check["reason"],
                "law_violated": "scope"
            }
            
        # 3. Check Mastery (Pedagogical Appropriateness)
        # Currently a placeholder for future adaptive learning rules
        return {
            "approved": True,
            "reason": "All policies passed",
            "law_violated": None
        }

    def _check_scope(
        self, 
        query: str, 
        reasoning_intent: str = None, 
        reasoning_confidence: float = 0.0,
        key_concepts: List[str] = None
    ) -> Dict[str, any]:
        """
        Check if query is within COMP 237 scope.
        
        Uses a hybrid approach:
        1. Reasoning Node: If high confidence (>0.8) that it's a valid intent, ALLOW.
        2. Vector Search: Fallback to similarity search if reasoning is unsure.
        """
        # SMART BYPASS: Trust the Reasoning Node if it's confident
        # If the reasoning node identified it as a valid educational intent with high confidence,
        # we trust it even if the vector store doesn't have an exact match.
        valid_intents = ["tutor", "math", "coder", "explain"]
        if reasoning_intent in valid_intents and reasoning_confidence >= 0.8:
            logger.info(f"Governor: Reasoning node confident ({reasoning_confidence:.2f}) - bypassing vector check")
            return {
                "approved": True,
                "reason": f"Reasoning node validated {reasoning_intent} intent",
            }

        # If we have key concepts, we can also be more lenient
        if key_concepts and len(key_concepts) > 0:
            # If specific AI concepts were detected, we can relax the threshold
            logger.info(f"Governor: Key concepts detected {key_concepts} - relaxing threshold")
            SCOPE_THRESHOLD = 0.85  # More permissive (higher distance allowed)
        else:
            SCOPE_THRESHOLD = 0.80  # Strict default
            
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=3,
                filter={"course_id": self.course_id}
            )
            
            if not results:
                # If no results found (empty DB?), default to safe mode
                logger.warning("Governor: No documents found in vector store")
                return {
                    "approved": False,
                    "reason": "I cannot verify if this is part of the course content.",
                }
                
            # ChromaDB returns distance (lower is better)
            # 0.0 = exact match, 1.0 = very different
            # We use the minimum distance (closest match)
            min_score = min(score for _, score in results)
            avg_score = sum(score for _, score in results) / len(results)
            
            # Check against threshold
            if min_score > SCOPE_THRESHOLD:
                logger.info(f"❌ Scope check failed (min_score: {min_score:.3f}, avg: {avg_score:.3f}, threshold: {SCOPE_THRESHOLD})")
                return {
                    "approved": False,
                    "reason": "This topic is not clearly covered in COMP 237. Please ask about course content like machine learning, neural networks, or AI concepts from your course materials.",
                }
                
            logger.info(f"✓ Scope check passed (min_score: {min_score:.3f})")
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
    
    # Create guardrail observation as child of root trace (v3 pattern)
    from app.observability.langfuse_client import create_child_span_from_state
    observation = create_child_span_from_state(
        state=state,
        name="policy_enforcement_guardrail",
        input_data={
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

