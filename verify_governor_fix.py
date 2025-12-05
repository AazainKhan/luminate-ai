import sys
import os
import logging

# Set dummy API key to satisfy config validation
os.environ["GOOGLE_API_KEY"] = "dummy_key"

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.agents.governor import Governor
from app.agents.state import AgentState

from unittest.mock import patch, MagicMock

# Mock the vector store client BEFORE importing Governor if it's used at module level,
# but here it's used in __init__, so we can patch it.

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock the dependency
sys.modules["app.rag.langchain_chroma"] = MagicMock()
sys.modules["app.rag.langchain_chroma"].get_langchain_chroma_client = MagicMock()

from app.agents.governor import Governor
from app.agents.state import AgentState

def test_governor_smart_bypass():
    """Test that Governor allows queries when Reasoning Node is confident"""
    print("\n=== Testing Governor Smart Bypass ===")
    
    governor = Governor()
    
    # Mock state with high confidence reasoning
    state = AgentState(
        query="What is backpropagation?",
        reasoning_intent="tutor",
        reasoning_confidence=0.9,
        key_concepts_detected=["backpropagation", "neural networks"],
        messages=[]
    )
    
    # Mock _check_integrity to always pass (we are testing scope)
    governor._check_integrity = lambda q: {"approved": True, "reason": "Pass"}
    
    # Mock vector store to fail (simulate "out of scope" in vector space)
    # This ensures we are testing the BYPASS logic, not the vector store
    class MockVectorStore:
        def similarity_search_with_score(self, *args, **kwargs):
            # Return a high distance score (bad match)
            return [("doc", 0.95)] 
            
    governor.vectorstore = MockVectorStore()
    
    # Run check
    result = governor.check_policies(state)
    
    print(f"Query: {state['query']}")
    print(f"Reasoning Confidence: {state['reasoning_confidence']}")
    print(f"Result: {result}")
    
    if result["approved"]:
        print("✅ PASS: Governor respected Reasoning Node confidence (Approved despite high vector distance)")
    else:
        print("❌ FAIL: Governor did not respect Reasoning Node")

def test_governor_low_confidence_fallback():
    """Test that Governor falls back to vector store when Reasoning is unsure"""
    print("\n=== Testing Governor Low Confidence Fallback ===")
    
    governor = Governor()
    
    # Mock state with LOW confidence reasoning
    state = AgentState(
        query="What is the capital of France?",
        reasoning_intent="fast",
        reasoning_confidence=0.4, # Low confidence
        key_concepts_detected=[],
        messages=[]
    )
    
    governor._check_integrity = lambda q: {"approved": True, "reason": "Pass"}
    
    # Mock vector store to fail (correctly blocking out of scope)
    class MockVectorStore:
        def similarity_search_with_score(self, *args, **kwargs):
            return [("doc", 0.95)] # High distance = bad match
            
    governor.vectorstore = MockVectorStore()
    
    # Run check
    result = governor.check_policies(state)
    
    print(f"Query: {state['query']}")
    print(f"Reasoning Confidence: {state['reasoning_confidence']}")
    print(f"Result: {result}")
    
    if not result["approved"] and "not clearly covered" in result["reason"]:
        print("✅ PASS: Governor correctly blocked out-of-scope query with low reasoning confidence")
    else:
        print(f"❌ FAIL: Governor should have blocked. Result: {result}")

if __name__ == "__main__":
    try:
        test_governor_smart_bypass()
        test_governor_low_confidence_fallback()
    except Exception as e:
        print(f"Error running tests: {e}")
