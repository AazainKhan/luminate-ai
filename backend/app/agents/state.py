"""
Agent State Definition for LangGraph
"""

from typing import TypedDict, List, Optional, Literal
from typing_extensions import Annotated
import operator


class AgentState(TypedDict):
    """State schema for the tutor agent"""
    
    # User input
    messages: Annotated[List[dict], operator.add]
    
    # Current query
    query: str
    
    # User context
    user_id: Optional[str]
    user_email: Optional[str]
    user_role: Optional[Literal["student", "admin"]]
    
    # Routing decisions
    intent: Optional[str]  # "fast", "coder", "reasoning", "syllabus_query"
    model_selected: Optional[str]  # "gemini-flash", "claude-sonnet", "gemini-pro"
    
    # RAG context
    retrieved_context: List[dict]  # Retrieved documents with metadata
    context_sources: List[dict]  # Source summaries with filenames/score
    
    # Policy enforcement
    governor_approved: bool
    governor_reason: Optional[str]
    
    # Sub-agent outputs
    syllabus_check: Optional[dict]
    math_explanation: Optional[str]
    code_suggestion: Optional[str]
    pedagogical_strategy: Optional[str]
    
    # Final response
    response: Optional[str]
    response_sources: List[str]  # Citations
    
    # Error handling
    error: Optional[str]

