"""
Mode Delegator Agent - Routes queries to Navigate or Educate mode
Analyzes student query intent and determines appropriate workflow.
"""

from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from llm_config import get_llm


def mode_delegator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    FAST keyword-based query classifier - no LLM calls!
    
    Determine if query requires Navigate (search) or Educate (learn) mode.
    
    Navigate Mode - Student wants to FIND course materials:
    - "Find videos on X"
    - "Show me the lecture about Y"
    - "Where is the assignment on Z?"
    - "Search for materials about W"
    - Keywords: find, show, where, search, locate, get, material, assignment, lecture, video
    
    Educate Mode - Student wants to LEARN/UNDERSTAND:
    - "What is X?"
    - "Explain Y"
    - "How does Z work?"
    - "Help me understand W"
    - Keywords: what, explain, how, why, define, understand, teach, help, learn
    
    Args:
        state: Current workflow state with "query" key
        
    Returns:
        Updated state with "mode" key ("navigate" or "educate")
    """
    query = state.get("query", "")
    query_lower = query.lower()
    
    print(f"\n🤖 Mode Delegator (fast): '{query}'")
    
    # Use fast keyword-based classification (no LLM call!)
    mode = _simple_mode_classification(query)
    
    print(f"✅ Mode: {mode.upper()} (instant)")
    
    return {
        **state,
        "mode": mode,
        "delegator_confidence": "high"
    }


# Simple keyword-based fallback (FAST - no LLM needed!)
def _simple_mode_classification(query: str) -> str:
    """
    FAST keyword-based classification - NO LLM CALL!
    Used for instant query routing without API delays.
    
    Args:
        query: Original search query
        
    Returns:
        "navigate" or "educate"
    """
    query_lower = query.lower()
    
    # Navigate keywords (search/find intent) - MUST come first in query
    navigate_triggers = [
        'find', 'search', 'show me', 'show', 'where is', 'where', 'locate', 
        'get', 'give me', 'i need', 'looking for', 'get me',
        'material', 'materials', 'assignment', 'lecture', 'video', 'videos',
        'resource', 'resources', 'download', 'link', 'access', 'content'
    ]
    
    # Educate keywords (learning intent)
    educate_triggers = [
        'what is', 'what are', 'what\'s', 'whats',
        'explain', 'describe', 'tell me about',
        'how does', 'how do', 'how to', 'how can',
        'why does', 'why do', 'why is', 'why',
        'define', 'definition of',
        'understand', 'help me understand', 'help me learn',
        'teach', 'teach me', 'learn', 'difference between'
    ]
    
    # Check navigate keywords first (if query starts with these, it's navigate)
    for keyword in navigate_triggers:
        if query_lower.startswith(keyword) or f' {keyword} ' in f' {query_lower} ':
            return "navigate"
    
    # Check educate keywords
    for keyword in educate_triggers:
        if keyword in query_lower:
            return "educate"
    
    # Default: If no clear keywords, assume educate (safer for learning)
    return "educate"


if __name__ == "__main__":
    """Test the mode delegator with sample queries"""
    
    print("="*70)
    print("MODE DELEGATOR TEST")
    print("="*70)
    
    test_queries = [
        # Navigate queries
        "Find videos about neural networks",
        "Show me the lecture on backpropagation",
        "Where is the assignment about CNNs?",
        "Search for materials on reinforcement learning",
        
        # Educate queries
        "What is backpropagation?",
        "Explain how CNNs work",
        "How do I implement a neural network?",
        "Why do we use activation functions?",
        
        # Ambiguous queries
        "Neural networks",
        "Tell me about and show me videos on AI ethics"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        
        state = {"query": query}
        result = mode_delegator_agent(state)
        
        mode = result.get("mode")
        confidence = result.get("delegator_confidence")
        
        print(f"   → Mode: {mode.upper()} (confidence: {confidence})")
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print("="*70)
