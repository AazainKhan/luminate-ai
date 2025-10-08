"""
Navigate Mode LangGraph Workflow for Luminate AI.

This creates a StateGraph that orchestrates 4 agents:
1. Query Understanding Agent - Parse and enhance student queries
2. Retrieval Agent - Get relevant content from ChromaDB
3. Context Agent - Add graph-based context (prerequisites, next steps)
4. Formatting Agent - Create UI-ready response

Based on educational AI research (VanLehn 2011, AutoTutor).
"""

from typing import TypedDict, List, Dict, Any, Callable, Optional
from langgraph.graph import StateGraph, END
from agents.query_understanding import query_understanding_agent
from agents.retrieval import retrieval_agent
from agents.context import context_agent
from agents.formatting import formatting_agent
from agents.external_resources import external_resources_agent
from datetime import datetime


class NavigateState(TypedDict, total=False):
    """State for Navigate Mode workflow."""
    # Input
    query: str
    chroma_db: Any  # ChromaDB instance
    
    # Agent outputs
    parsed_query: Dict[str, Any]
    retrieved_chunks: List[Dict]
    enriched_results: List[Dict]
    external_resources: List[Dict]  # NEW: YouTube, OER, Khan Academy, etc.
    formatted_response: Dict[str, Any]
    
    # Metadata & errors
    retrieval_metadata: Dict[str, Any]
    retrieval_error: str
    context_warning: str
    is_in_scope: bool  # NEW: Track if query is in COMP237 scope
    
    # For external resources agent
    original_query: str
    understood_query: str
    
    # Agent trace callback
    trace_callback: Optional[Callable]


def _wrap_agent_with_trace(agent_fn, agent_name: str, action_desc: str):
    """Wrap agent function to emit trace before execution."""
    def wrapped(state: NavigateState) -> NavigateState:
        # Emit trace if callback exists
        if state.get("trace_callback"):
            state["trace_callback"]({
                "agent": agent_name,
                "action": action_desc,
                "status": "in_progress",
                "timestamp": datetime.now().isoformat()
            })
        
        # Execute agent
        result = agent_fn(state)
        
        # Emit completion trace
        if state.get("trace_callback"):
            state["trace_callback"]({
                "agent": agent_name,
                "action": action_desc,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
        
        return result
    return wrapped


def build_navigate_graph():
    """
    Build the Navigate Mode StateGraph.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph
    graph = StateGraph(NavigateState)
    
    # Add nodes (agents) with trace wrappers
    graph.add_node("understand_query", _wrap_agent_with_trace(
        query_understanding_agent, "query_understanding", "Analyzing query and extracting key terms"
    ))
    graph.add_node("retrieve", _wrap_agent_with_trace(
        retrieval_agent, "retrieval", "Searching ChromaDB for relevant course materials"
    ))
    graph.add_node("search_external", _wrap_agent_with_trace(
        external_resources_agent, "external_resources", "Finding supplementary learning resources"
    ))
    graph.add_node("add_context", _wrap_agent_with_trace(
        context_agent, "context", "Adding course structure and related topics"
    ))
    graph.add_node("format_response", _wrap_agent_with_trace(
        formatting_agent, "formatting", "Generating UI-ready response with Gemini 2.0"
    ))
    
    # Define edges (workflow)
    graph.set_entry_point("understand_query")
    
    # Sequential flow to avoid state conflicts
    graph.add_edge("understand_query", "retrieve")
    graph.add_edge("retrieve", "search_external")
    graph.add_edge("search_external", "add_context")
    graph.add_edge("add_context", "format_response")
    graph.add_edge("format_response", END)
    
    # Compile graph
    return graph.compile()


def query_navigate_mode(query: str) -> Dict[str, Any]:
    """
    Execute Navigate Mode workflow for a student query.
    
    Args:
        query: Student's search query
        
    Returns:
        Dictionary with formatted_response and metadata
    """
    # Build graph
    navigate_graph = build_navigate_graph()
    
    # Initialize state
    initial_state = {"query": query}
    
    # Execute workflow
    final_state = navigate_graph.invoke(initial_state)
    
    return {
        "formatted_response": final_state.get("formatted_response", {}),
        "metadata": {
            "original_query": query,
            "parsed_query": final_state.get("parsed_query", {}),
            "retrieval_metadata": final_state.get("retrieval_metadata", {}),
            "total_results": len(final_state.get("retrieved_chunks", [])),
            "enriched_count": len(final_state.get("enriched_results", [])),
            "errors": {
                "retrieval": final_state.get("retrieval_error"),
                "context": final_state.get("context_warning")
            }
        }
    }


if __name__ == "__main__":
    # Test the Navigate Mode workflow
    print("="*70)
    print("NAVIGATE MODE LANGGRAPH TEST")
    print("="*70)
    print("\nNote: Requires FastAPI service running at http://localhost:8000")
    print("Start it with: cd development/backend/fastapi_service && uvicorn main:app\n")
    
    # Test queries
    test_queries = [
        "What is ML?",
        "neural networks backpropagation",
        "BFS vs DFS algorithm",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {query}")
        print(f"{'='*70}\n")
        
        try:
            result = query_navigate_mode(query)
            
            # Display metadata
            metadata = result["metadata"]
            print(f"Original Query: {metadata['original_query']}")
            print(f"Expanded Query: {metadata['parsed_query'].get('expanded_query', 'N/A')}")
            print(f"Category: {metadata['parsed_query'].get('category', 'N/A')}")
            print(f"Student Goal: {metadata['parsed_query'].get('student_goal', 'N/A')}")
            print(f"\nRetrieval:")
            print(f"  Total Results: {metadata['retrieval_metadata'].get('total_results', 0)}")
            print(f"  After Dedup: {metadata['retrieval_metadata'].get('after_dedup', 0)}")
            print(f"  Final Count: {metadata['retrieval_metadata'].get('final_count', 0)}")
            
            # Display formatted response
            formatted = result["formatted_response"]
            print(f"\nFormatted Response:")
            print(f"  Top Results: {len(formatted.get('top_results', []))}")
            print(f"  Related Topics: {len(formatted.get('related_topics', []))}")
            print(f"  Encouragement: {formatted.get('encouragement', 'N/A')}")
            print(f"  Next Step: {formatted.get('suggested_next_step', 'N/A')[:100]}...")
            
            # Show top 2 results
            if formatted.get('top_results'):
                print(f"\nTop Results:")
                for j, res in enumerate(formatted['top_results'][:2], 1):
                    print(f"\n  {j}. {res.get('title', 'N/A')}")
                    print(f"     Module: {res.get('module', 'N/A')}")
                    print(f"     Relevance: {res.get('relevance_explanation', 'N/A')}")
                    print(f"     URL: {res.get('url', 'N/A')[:80]}...")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n")
