#!/usr/bin/env python3
"""Test Educate Mode with both Math Translation Agent and RAG retrieval"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_query(query: str, expected_type: str = ""):
    """Test a single query"""
    print(f"\n{'='*70}")
    print(f"🔍 Testing: {query}")
    print(f"{'='*70}")
    
    response = requests.post(
        f"{API_BASE}/api/query",
        json={"query": query},
        timeout=10
    )
    
    data = response.json()
    
    print(f"✅ Mode: {data['mode']}")
    print(f"✅ Confidence: {data['confidence']}")
    print(f"✅ Reasoning: {data['reasoning']}")
    
    response_data = data.get('response', {})
    formatted_response = response_data.get('formatted_response', '')
    
    # Show preview
    preview = formatted_response[:300] + "..." if len(formatted_response) > 300 else formatted_response
    print(f"\n📄 Response Preview:\n{preview}\n")
    
    # Check response characteristics
    if expected_type == "math":
        has_levels = all(f"Level {i}" in formatted_response for i in [1, 2, 3, 4])
        has_code = "```python" in formatted_response
        has_latex = any(char in formatted_response for char in ['$', '∇', 'θ', 'α'])
        
        print(f"   4-level structure: {'✅' if has_levels else '❌'}")
        print(f"   Python code: {'✅' if has_code else '❌'}")
        print(f"   LaTeX/symbols: {'✅' if has_latex else '❌'}")
        
    elif expected_type == "conceptual":
        has_sources = "Sources" in formatted_response
        has_summary = "Summary" in formatted_response
        
        print(f"   Has summary: {'✅' if has_summary else '❌'}")
        print(f"   Has sources: {'✅' if has_sources else '❌'}")
        
        if 'context_sources' in response_data:
            print(f"   Context sources: {', '.join(response_data['context_sources'][:2])}")
    
    return data

# Test Math Translation Agent
print("\n" + "🧮 TESTING MATH TRANSLATION AGENT ".center(70, "="))
test_query("explain gradient descent", "math")
test_query("what is backpropagation", "math")
test_query("sigmoid activation function", "math")

# Test Conceptual RAG Retrieval  
print("\n" + "📚 TESTING CONCEPTUAL RAG RETRIEVAL ".center(70, "="))
test_query("Explain Week 2 intelligent agents simply", "conceptual")
test_query("what are search algorithms", "conceptual")
test_query("explain heuristic functions", "conceptual")

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETED")
print("="*70)
