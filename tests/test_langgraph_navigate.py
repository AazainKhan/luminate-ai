"""
Comprehensive tests for Navigate Mode LangGraph workflow with Gemini.

Tests:
1. Query Understanding Agent - Acronym expansion, topic identification
2. Retrieval Agent - FastAPI integration, re-ranking, deduplication
3. Context Agent - Graph traversal, related topics, prerequisites
4. Formatting Agent - UI-ready output, relevance explanations
5. End-to-end workflow - Full Navigate Mode pipeline
6. Error handling - Empty queries, API failures, malformed data

Run with: python development/tests/test_langgraph_navigate.py
"""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add langgraph module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "langgraph"))

import json
from agents.query_understanding import query_understanding_agent
from agents.retrieval import retrieval_agent
from agents.context import context_agent
from agents.formatting import formatting_agent
from navigate_graph import query_navigate_mode, build_navigate_graph


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add(self, name, passed, message=""):
        self.tests.append({"name": name, "passed": passed, "message": message})
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total: {total} | Passed: {self.passed} ✓ | Failed: {self.failed} ✗")
        print(f"Pass Rate: {(self.passed/total*100) if total > 0 else 0:.1f}%\n")
        
        if self.failed > 0:
            print("Failed Tests:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  ✗ {test['name']}: {test['message']}")


results = TestResults()


def test_query_understanding_agent():
    """Test Query Understanding Agent."""
    print("\n" + "="*70)
    print("TEST CATEGORY 1: Query Understanding Agent")
    print("="*70)
    
    # Test 1: Acronym expansion
    print("\nTest 1.1: Acronym Expansion")
    state = {"query": "What is ML?"}
    result = query_understanding_agent(state)
    parsed = result.get("parsed_query", {})
    
    expanded = parsed.get("expanded_query", "").lower()
    passed = "machine learning" in expanded
    print(f"  Query: 'What is ML?'")
    print(f"  Expanded: {parsed.get('expanded_query')}")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Acronym expansion (ML → machine learning)", passed, 
                f"Got: {parsed.get('expanded_query')}")
    
    # Test 2: Topic identification
    print("\nTest 1.2: Topic Identification")
    state = {"query": "neural network backpropagation"}
    result = query_understanding_agent(state)
    parsed = result.get("parsed_query", {})
    
    category = parsed.get("category", "").lower()
    passed = any(keyword in category for keyword in ["machine learning", "neural", "ml"])
    print(f"  Query: 'neural network backpropagation'")
    print(f"  Category: {parsed.get('category')}")
    print(f"  Search Terms: {', '.join(parsed.get('search_terms', []))}")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Topic identification (neural networks → ML category)", passed,
                f"Got category: {parsed.get('category')}")
    
    # Test 3: Search term extraction
    print("\nTest 1.3: Search Term Extraction")
    state = {"query": "how does BFS algorithm work"}
    result = query_understanding_agent(state)
    parsed = result.get("parsed_query", {})
    
    search_terms = [term.lower() for term in parsed.get("search_terms", [])]
    passed = len(search_terms) >= 3 and any("breadth" in term or "bfs" in term for term in search_terms)
    print(f"  Query: 'how does BFS algorithm work'")
    print(f"  Search Terms: {', '.join(parsed.get('search_terms', []))}")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Search term extraction (3+ terms)", passed,
                f"Got {len(search_terms)} terms: {search_terms}")
    
    # Test 4: Student goal inference
    print("\nTest 1.4: Student Goal Inference")
    state = {"query": "explain neural networks"}
    result = query_understanding_agent(state)
    parsed = result.get("parsed_query", {})
    
    goal = parsed.get("student_goal", "")
    passed = goal in ["learn_concept", "clarify_confusion", "find_example"]
    print(f"  Query: 'explain neural networks'")
    print(f"  Inferred Goal: {goal}")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Student goal inference", passed, f"Got goal: {goal}")
    
    # Test 5: Empty query handling
    print("\nTest 1.5: Empty Query Handling")
    state = {"query": ""}
    result = query_understanding_agent(state)
    parsed = result.get("parsed_query", {})
    
    passed = "expanded_query" in parsed  # Should have fallback
    print(f"  Query: (empty)")
    print(f"  Parsed: {parsed}")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Empty query handling (no crash)", passed)


def test_retrieval_agent():
    """Test Retrieval Agent."""
    print("\n" + "="*70)
    print("TEST CATEGORY 2: Retrieval Agent")
    print("="*70)
    print("\nNote: Requires FastAPI service at http://localhost:8000")
    print("If tests fail, start: cd development/backend/fastapi_service && uvicorn main:app\n")
    
    # Test 1: Basic retrieval
    print("\nTest 2.1: Basic Retrieval")
    state = {
        "query": "machine learning",
        "parsed_query": {
            "expanded_query": "machine learning artificial intelligence",
            "search_terms": ["machine", "learning", "AI"]
        }
    }
    result = retrieval_agent(state)
    
    chunks = result.get("retrieved_chunks", [])
    has_error = "retrieval_error" in result
    passed = len(chunks) > 0 and not has_error
    
    print(f"  Query: 'machine learning'")
    print(f"  Retrieved: {len(chunks)} chunks")
    if has_error:
        print(f"  Error: {result.get('retrieval_error')}")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Basic retrieval (returns results)", passed,
                result.get('retrieval_error', f'Got {len(chunks)} chunks'))
    
    if passed:
        # Test 2: Re-ranking
        print("\nTest 2.2: Re-ranking (BB docs prioritized)")
        metadata = result.get("retrieval_metadata", {})
        
        # Check if first result has BB ID
        first_has_bb = chunks[0].get("metadata", {}).get("bb_doc_id") if chunks else False
        passed = first_has_bb is not False and first_has_bb is not None
        
        print(f"  First result has BB ID: {first_has_bb}")
        print(f"  Rerank score: {chunks[0].get('rerank_score', 0):.2f}" if chunks else "  No results")
        print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
        results.add("Re-ranking (BB docs prioritized)", passed)
        
        # Test 3: Deduplication
        print("\nTest 2.3: Deduplication")
        bb_ids = [c.get("metadata", {}).get("bb_doc_id") for c in chunks if c.get("metadata", {}).get("bb_doc_id")]
        unique_bb_ids = set(bb_ids)
        passed = len(bb_ids) == len(unique_bb_ids)  # No duplicates
        
        print(f"  Total results with BB IDs: {len(bb_ids)}")
        print(f"  Unique BB IDs: {len(unique_bb_ids)}")
        print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
        results.add("Deduplication (no duplicate BB IDs)", passed,
                    f"{len(bb_ids)} total, {len(unique_bb_ids)} unique")
    else:
        # Skip dependent tests
        results.add("Re-ranking (BB docs prioritized)", False, "Skipped - retrieval failed")
        results.add("Deduplication (no duplicate BB IDs)", False, "Skipped - retrieval failed")


def test_context_agent():
    """Test Context Agent."""
    print("\n" + "="*70)
    print("TEST CATEGORY 3: Context Agent")
    print("="*70)
    
    # Mock retrieved chunks
    mock_chunks = [
        {
            "content": "Test content",
            "metadata": {
                "bb_doc_id": "_123456_1",
                "title": "Test Document",
                "module": "Module 1"
            },
            "score": 0.9
        }
    ]
    
    # Test 1: Graph context addition
    print("\nTest 3.1: Graph Context Addition")
    state = {"retrieved_chunks": mock_chunks}
    result = context_agent(state)
    
    enriched = result.get("enriched_results", [])
    passed = len(enriched) > 0
    
    print(f"  Input chunks: {len(mock_chunks)}")
    print(f"  Enriched results: {len(enriched)}")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Graph context addition (processes chunks)", passed)
    
    # Test 2: Graph data loading
    print("\nTest 3.2: Graph Data Loading")
    has_warning = "context_warning" in result
    
    if enriched and enriched[0].get("graph_context"):
        graph_context = enriched[0]["graph_context"]
        has_fields = all(field in graph_context for field in ["module", "related_topics", "prerequisites", "next_steps"])
        passed = has_fields
        print(f"  Graph context fields: {list(graph_context.keys())}")
    else:
        passed = has_warning  # Warning is acceptable if graph not available
        print(f"  Graph context: None (Warning: {result.get('context_warning', 'N/A')})")
    
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Graph data loading", passed)
    
    # Test 3: Empty input handling
    print("\nTest 3.3: Empty Input Handling")
    state = {"retrieved_chunks": []}
    result = context_agent(state)
    
    enriched = result.get("enriched_results", [])
    passed = enriched == []  # Should return empty list
    
    print(f"  Input: Empty chunks")
    print(f"  Output: {len(enriched)} results")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Empty input handling (returns empty)", passed)


def test_formatting_agent():
    """Test Formatting Agent."""
    print("\n" + "="*70)
    print("TEST CATEGORY 4: Formatting Agent")
    print("="*70)
    
    # Mock enriched results
    mock_enriched = [
        {
            "content": "Neural networks are...",
            "metadata": {
                "bb_doc_id": "_123456_1",
                "title": "Introduction to Neural Networks",
                "module": "Module 3: Machine Learning",
                "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/file/_123456_1"
            },
            "score": 0.89,
            "graph_context": {
                "module": "Module 3: Machine Learning",
                "prerequisites": [],
                "next_steps": [],
                "related_topics": []
            }
        }
    ]
    
    # Test 1: Formatted output structure
    print("\nTest 4.1: Formatted Output Structure")
    state = {
        "query": "neural networks",
        "parsed_query": {
            "expanded_query": "neural networks machine learning",
            "category": "machine learning",
            "student_goal": "learn_concept"
        },
        "enriched_results": mock_enriched
    }
    result = formatting_agent(state)
    
    formatted = result.get("formatted_response", {})
    required_fields = ["top_results", "related_topics", "suggested_next_step", "encouragement"]
    has_fields = all(field in formatted for field in required_fields)
    
    print(f"  Required fields: {required_fields}")
    print(f"  Present fields: {list(formatted.keys())}")
    print(f"  Result: {'✓ PASS' if has_fields else '✗ FAIL'}")
    results.add("Formatted output structure (all fields)", has_fields,
                f"Missing: {set(required_fields) - set(formatted.keys())}")
    
    # Test 2: Top results formatting
    print("\nTest 4.2: Top Results Formatting")
    top_results = formatted.get("top_results", [])
    passed = len(top_results) > 0
    
    if top_results:
        first_result = top_results[0]
        has_result_fields = all(field in first_result for field in ["title", "url", "module", "relevance_explanation"])
        passed = passed and has_result_fields
        print(f"  Top results count: {len(top_results)}")
        print(f"  First result fields: {list(first_result.keys())}")
    else:
        print(f"  Top results count: 0")
    
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Top results formatting (has required fields)", passed)
    
    # Test 3: Empty results handling
    print("\nTest 4.3: Empty Results Handling")
    state = {
        "query": "test query",
        "parsed_query": {},
        "enriched_results": []
    }
    result = formatting_agent(state)
    
    formatted = result.get("formatted_response", {})
    has_message = "message" in formatted or "encouragement" in formatted
    passed = has_message
    
    print(f"  Input: Empty results")
    print(f"  Has fallback message: {has_message}")
    print(f"  Message: {formatted.get('message') or formatted.get('encouragement', 'N/A')}")
    print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
    results.add("Empty results handling (provides message)", passed)


def test_end_to_end_workflow():
    """Test End-to-End Navigate Mode Workflow."""
    print("\n" + "="*70)
    print("TEST CATEGORY 5: End-to-End Workflow")
    print("="*70)
    print("\nNote: Requires FastAPI service at http://localhost:8000\n")
    
    test_queries = [
        "What is machine learning?",
        "BFS algorithm",
        "neural networks"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest 5.{i}: '{query}'")
        
        try:
            result = query_navigate_mode(query)
            
            formatted = result.get("formatted_response", {})
            metadata = result.get("metadata", {})
            
            # Check if workflow completed
            has_formatted = "top_results" in formatted
            has_metadata = "parsed_query" in metadata
            passed = has_formatted and has_metadata
            
            if passed:
                print(f"  ✓ Workflow completed")
                print(f"    - Parsed query: {metadata['parsed_query'].get('expanded_query', 'N/A')}")
                print(f"    - Retrieved: {metadata.get('total_results', 0)} chunks")
                print(f"    - Top results: {len(formatted.get('top_results', []))}")
                print(f"    - Related topics: {len(formatted.get('related_topics', []))}")
            else:
                print(f"  ✗ Workflow incomplete")
                print(f"    - Has formatted response: {has_formatted}")
                print(f"    - Has metadata: {has_metadata}")
            
            results.add(f"E2E workflow: '{query}'", passed)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.add(f"E2E workflow: '{query}'", False, str(e))


def test_error_handling():
    """Test Error Handling."""
    print("\n" + "="*70)
    print("TEST CATEGORY 6: Error Handling")
    print("="*70)
    
    # Test 1: Empty query
    print("\nTest 6.1: Empty Query")
    try:
        result = query_navigate_mode("")
        formatted = result.get("formatted_response", {})
        passed = "message" in formatted or "encouragement" in formatted or len(formatted.get("top_results", [])) == 0
        print(f"  Query: (empty)")
        print(f"  Result: {'✓ PASS (handled gracefully)' if passed else '✗ FAIL'}")
        results.add("Error handling: empty query", passed)
    except Exception as e:
        print(f"  ✗ FAIL: Crashed with {e}")
        results.add("Error handling: empty query", False, str(e))
    
    # Test 2: Very long query
    print("\nTest 6.2: Very Long Query")
    long_query = "machine learning " * 100  # 200+ words
    try:
        result = query_navigate_mode(long_query)
        passed = "formatted_response" in result
        print(f"  Query length: {len(long_query)} characters")
        print(f"  Result: {'✓ PASS (handled)' if passed else '✗ FAIL'}")
        results.add("Error handling: very long query", passed)
    except Exception as e:
        print(f"  ✗ FAIL: Crashed with {e}")
        results.add("Error handling: very long query", False, str(e))
    
    # Test 3: Special characters
    print("\nTest 6.3: Special Characters in Query")
    special_query = "What is ML? @#$%^&*() <script>alert('test')</script>"
    try:
        result = query_navigate_mode(special_query)
        passed = "formatted_response" in result
        print(f"  Query: {special_query[:50]}...")
        print(f"  Result: {'✓ PASS (handled)' if passed else '✗ FAIL'}")
        results.add("Error handling: special characters", passed)
    except Exception as e:
        print(f"  ✗ FAIL: Crashed with {e}")
        results.add("Error handling: special characters", False, str(e))


if __name__ == "__main__":
    print("\n" + "="*70)
    print("NAVIGATE MODE LANGGRAPH - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\nTesting 4 agents + end-to-end workflow + error handling")
    print("Total: ~20 tests across 6 categories\n")
    
    # Run all test categories
    test_query_understanding_agent()
    test_retrieval_agent()
    test_context_agent()
    test_formatting_agent()
    test_end_to_end_workflow()
    test_error_handling()
    
    # Print summary
    results.summary()
    
    # Exit code
    sys.exit(0 if results.failed == 0 else 1)
