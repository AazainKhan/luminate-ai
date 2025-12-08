"""
Agent State Definition - Simplified state for LangGraph

This is a dramatically simplified state compared to the old 60+ field version.
Only includes fields that are actually used in the agent pipeline.
"""

from typing import TypedDict, List, Optional, Literal, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


# Scaffolding levels based on Adarsh's escalation model
# Level 1: Hints/questions only
# Level 2: Directed hints with analogies  
# Level 3: Concrete examples
# Level 4: Full direct explanation
EscalationLevel = Literal[1, 2, 3, 4]


class AgentState(TypedDict):
    """
    Simplified state schema for the tutor agent
    
    Pipeline: Planner → Router → [Tutor|Math|Reject] → Evaluator → End
    """
    
    # ========== Input ==========
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    
    # ========== User Context ==========
    user_id: Optional[str]
    user_email: Optional[str]
    conversation_history: Optional[List[dict]]  # [{role, content, timestamp}]
    
    # ========== Routing (from Planner) ==========
    plan: Optional[dict]              # PlannerPlan as dict
    current_subtask: Optional[dict]   # Current subtask being processed
    routing_info: Optional[dict]      # Debug info about routing decision
    _subtask_index: int               # Index into subtasks list
    
    # ========== RAG Context ==========
    retrieved_docs: List[dict]        # Raw docs from ChromaDB
    rag_metadata: Optional[dict]      # RAGMetadata as dict
    context_str: Optional[str]        # Formatted context for prompts
    
    # ========== Scaffolding (LearnLM + Adarsh's escalation) ==========
    escalation_level: int             # 1-4 scaffolding level
    stuck_count: int                  # How many times student said "I don't understand"
    is_stuck: bool                    # Current query indicates confusion
    
    # ========== Output ==========
    response: Optional[str]           # Final text response
    intervention: Optional[dict]      # Polymorphic UI component (as dict)
    sources: List[dict]               # RAG sources used
    
    # ========== Evaluation (from Evaluator Node) ==========
    evaluation: Optional[dict]        # {concept_detected, misconceptions, outcome, etc.}
    
    # ========== Governor (Policy Enforcement) ==========
    approved: bool                    # Whether Governor approved the request
    rejection_reason: Optional[str]   # If rejected: "integrity", "off_topic", "low_relevance"
    governor_checks: Optional[dict]   # {scope: {...}, integrity: {...}, mastery: {...}}
    
    # ========== Observability ==========
    trace_id: Optional[str]           # Langfuse trace ID
    session_id: Optional[str]         # Session grouping
    chat_id: Optional[str]            # Supabase chat ID
    
    # ========== Error Handling ==========
    error: Optional[str]


def create_initial_state(
    query: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    conversation_history: Optional[List[dict]] = None,
    session_id: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> AgentState:
    """Create initial state for a new agent invocation"""
    return AgentState(
        messages=[],
        query=query,
        user_id=user_id,
        user_email=user_email,
        conversation_history=conversation_history or [],
        plan=None,
        current_subtask=None,
        routing_info=None,
        _subtask_index=0,
        retrieved_docs=[],
        rag_metadata=None,
        context_str=None,
        escalation_level=1,
        stuck_count=0,
        is_stuck=False,
        response=None,
        sources=[],
        evaluation=None,
        approved=True,
        rejection_reason=None,
        governor_checks=None,
        trace_id=None,
        session_id=session_id,
        chat_id=chat_id,
        error=None,
    )
