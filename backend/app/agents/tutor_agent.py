"""
Main Tutor Agent using LangGraph
Implements the Governor-Agent pattern with Supervisor routing
"""

from typing import Dict
import logging
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.governor import governor_node
from app.agents.supervisor import supervisor_node
from app.agents.sub_agents import rag_node, syllabus_node, generate_response_node
from app.observability import create_trace, flush_langfuse

logger = logging.getLogger(__name__)


def should_continue(state: AgentState) -> str:
    """
    Conditional edge function
    Determines next step based on governor approval
    """
    if not state.get("governor_approved", False):
        return "end"  # Stop if governor rejected
    return "continue"


def create_tutor_agent() -> StateGraph:
    """
    Create and configure the tutor agent graph
    
    Returns:
        Configured StateGraph
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("governor", governor_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("syllabus", syllabus_node)
    workflow.add_node("generate", generate_response_node)
    
    # Set entry point
    workflow.set_entry_point("governor")
    
    # Add conditional edge from governor
    workflow.add_conditional_edges(
        "governor",
        should_continue,
        {
            "continue": "supervisor",
            "end": END,
        }
    )
    
    # Add edges
    workflow.add_edge("supervisor", "rag")
    workflow.add_edge("rag", "syllabus")
    workflow.add_edge("syllabus", "generate")
    workflow.add_edge("generate", END)
    
    # Compile graph
    app = workflow.compile()
    
    logger.info("Tutor agent graph created successfully")
    return app


# Global agent instance
_tutor_agent = None


def get_tutor_agent() -> StateGraph:
    """Get or create tutor agent instance"""
    global _tutor_agent
    if _tutor_agent is None:
        _tutor_agent = create_tutor_agent()
    return _tutor_agent


def run_agent(query: str, user_id: str = None, user_email: str = None) -> Dict:
    """
    Run the tutor agent with a query
    
    Args:
        query: User query
        user_id: Optional user ID
        user_email: Optional user email
        
    Returns:
        Dictionary with response and metadata
    """
    agent = get_tutor_agent()
    
    # Create Langfuse trace for observability (v3 pattern)
    span = create_trace(
        name="tutor_agent_query",
        user_id=user_id,
        metadata={
            "query": query,
            "user_email": user_email,
        }
    )
    
    # Initialize state
    initial_state: AgentState = {
        "messages": [],
        "query": query,
        "user_id": user_id,
        "user_email": user_email,
        "user_role": "student",
        "intent": None,
        "model_selected": None,
        "retrieved_context": [],
        "context_sources": [],
        "governor_approved": False,
        "governor_reason": None,
        "syllabus_check": None,
        "math_explanation": None,
        "code_suggestion": None,
        "pedagogical_strategy": None,
        "response": None,
        "response_sources": [],
        "error": None,
    }
    
    # Run agent
    try:
        final_state = agent.invoke(initial_state)
        
        # Log trace metadata
        if span:
            span.update(
                output={
                    "response": final_state.get("response"),
                    "intent": final_state.get("intent"),
                    "model_used": final_state.get("model_selected"),
                    "governor_approved": final_state.get("governor_approved"),
                }
            )
            span.end()
        
        # Flush Langfuse events
        flush_langfuse()
        
        return {
            "response": final_state.get("response"),
            "sources": final_state.get("response_sources", []),
            "intent": final_state.get("intent"),
            "model_used": final_state.get("model_selected"),
            "error": final_state.get("error"),
        }
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        
        # Log error to trace
        if span:
            span.update(
                output={"error": str(e)},
                level="ERROR"
            )
            span.end()
        
        flush_langfuse()
        
        return {
            "response": "I apologize, but I encountered an error processing your query.",
            "sources": [],
            "error": str(e),
        }

