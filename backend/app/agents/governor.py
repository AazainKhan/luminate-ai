"""
Governor (Policy Engine) for Course Marshal
Enforces course policies and constraints
"""

from typing import Dict, List
import logging
from app.agents.state import AgentState
from app.rag.langchain_chroma import get_langchain_chroma_client

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
            
            # If all results are very distant, might be out of scope
            if min_score > 1.5:  # Threshold for relevance
                return {
                    "approved": False,
                    "reason": "This topic is not clearly covered in COMP 237. Please rephrase or ask about specific course content.",
                }
            
            logger.info(f"✅ Scope check passed (min_score: {min_score:.3f})")
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
    Governor node for LangGraph
    Checks policies before allowing query to proceed
    """
    governor = Governor()
    policy_check = governor.check_policies(state)
    
    state["governor_approved"] = policy_check["approved"]
    state["governor_reason"] = policy_check["reason"]
    
    if not policy_check["approved"]:
        # Set error response
        state["error"] = policy_check["reason"]
        state["response"] = policy_check["reason"]
    
    return state

