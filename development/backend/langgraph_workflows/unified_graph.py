"""
Unified Workflow - Single entry point that routes to Navigate or Educate mode
Uses mode delegator to automatically determine appropriate workflow.
"""

from typing import Dict, Any, List, Optional
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langgraph_workflows.agents.mode_delegator import mode_delegator_agent
from langgraph_workflows.navigate_graph import query_navigate_mode
from langgraph_workflows.educate_graph import query_educate_mode


def unified_workflow(
    query: str, 
    chroma_db=None, 
    conversation_history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Unified entry point - automatically routes to Navigate or Educate mode.
    
    Flow:
    1. Mode Delegator analyzes query intent
    2. Routes to appropriate workflow:
       - Navigate: For finding course materials
       - Educate: For learning and understanding concepts
    3. Returns formatted response from selected mode
    
    Args:
        query: Student's query
        chroma_db: ChromaDB collection for retrieval
        conversation_history: Previous conversation context
        
    Returns:
        Dictionary with response and metadata including selected mode
    """
    print(f"\n{'='*70}")
    print(f"🌟 UNIFIED WORKFLOW")
    print(f"{'='*70}")
    print(f"📝 Query: {query}")
    
    # Step 1: Determine mode using delegator agent
    initial_state = {
        "query": query,
        "chroma_db": chroma_db,
        "conversation_history": conversation_history or []
    }
    
    delegated_state = mode_delegator_agent(initial_state)
    mode = delegated_state.get("mode", "educate")
    
    print(f"🎯 Routing to: {mode.upper()} MODE")
    print(f"{'='*70}\n")
    
    # Step 2: Route to appropriate workflow
    try:
        if mode == "navigate":
            # Navigate Mode - Find course materials
            result = query_navigate_mode(
                query=query,
                chroma_db=chroma_db
            )
            
            # Add mode to metadata
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["selected_mode"] = "navigate"
            result["metadata"]["delegator_confidence"] = delegated_state.get("delegator_confidence", "high")
            
        else:
            # Educate Mode - Learn and understand
            result = query_educate_mode(
                query=query,
                conversation_history=conversation_history or [],
                chroma_db=chroma_db
            )
            
            # Add mode to metadata
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["selected_mode"] = "educate"
            result["metadata"]["delegator_confidence"] = delegated_state.get("delegator_confidence", "high")
        
        print(f"✅ {mode.upper()} mode completed successfully\n")
        return result
        
    except Exception as e:
        print(f"❌ Error in {mode} mode: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback response
        return {
            "formatted_response": {
                "main_content": f"I encountered an error processing your request. Please try rephrasing your question.",
                "response_type": "error",
                "sources": [],
                "related_concepts": [],
                "follow_up_suggestions": ["Try asking in a different way", "Be more specific about what you need"]
            },
            "metadata": {
                "selected_mode": mode,
                "error": str(e)
            }
        }


def query_unified_mode(
    query: str,
    chroma_db=None,
    conversation_history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Convenience wrapper for unified_workflow.
    Matches the signature of navigate/educate query functions.
    """
    return unified_workflow(query, chroma_db, conversation_history)


if __name__ == "__main__":
    """Test the unified workflow"""
    
    print("\n" + "="*70)
    print("UNIFIED WORKFLOW TEST")
    print("="*70)
    print("\nNote: This test requires ChromaDB and server dependencies.")
    print("Run from backend directory: cd development/backend\n")
    
    # Test queries
    test_cases = [
        {
            "query": "Find videos about neural networks",
            "expected_mode": "navigate",
            "description": "Search query - should route to Navigate"
        },
        {
            "query": "What is backpropagation?",
            "expected_mode": "educate",
            "description": "Learning query - should route to Educate"
        },
        {
            "query": "Explain CNNs",
            "expected_mode": "educate",
            "description": "Explanation query - should route to Educate"
        },
        {
            "query": "Show me the lecture on reinforcement learning",
            "expected_mode": "navigate",
            "description": "Material request - should route to Navigate"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {test['description']}")
        print(f"{'='*70}")
        print(f"Query: '{test['query']}'")
        print(f"Expected: {test['expected_mode'].upper()}")
        
        # Note: Actual execution requires ChromaDB setup
        print(f"\n⏭️  Skipping execution (requires full backend setup)")
        print(f"   To run: python -c 'from unified_graph import unified_workflow; unified_workflow(\"{test['query']}\")'")
    
    print(f"\n{'='*70}")
    print("To test with full backend:")
    print("1. Start server: python simple_server.py")
    print("2. Send request to: POST http://localhost:8000/langgraph/query")
    print("="*70 + "\n")
