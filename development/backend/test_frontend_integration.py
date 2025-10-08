#!/usr/bin/env python3
"""
Frontend Integration Test for Math Translation Agent
Tests the complete flow from API to Chrome Extension
"""

import requests
import json
import sys
from typing import Dict, Any

API_BASE = "http://localhost:8000"

def test_api_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        data = response.json()
        print("✅ Backend Health Check:")
        print(f"   Status: {data['status']}")
        print(f"   ChromaDB Documents: {data['chromadb_documents']}")
        return True
    except Exception as e:
        print(f"❌ Backend Health Check Failed: {e}")
        return False

def test_math_formula(query: str, expected_mode: str = "educate") -> bool:
    """Test math formula translation"""
    try:
        response = requests.post(
            f"{API_BASE}/api/query",
            json={"query": query},
            timeout=10
        )
        data = response.json()
        
        # Validate response structure
        assert "mode" in data, "Missing 'mode' field"
        assert "confidence" in data, "Missing 'confidence' field"
        assert "response" in data, "Missing 'response' field"
        assert "formatted_response" in data["response"], "Missing 'formatted_response'"
        
        # Validate mode
        assert data["mode"] == expected_mode, f"Expected mode '{expected_mode}', got '{data['mode']}'"
        
        # Check for 4-level structure in math formulas
        if expected_mode == "educate":
            content = data["response"]["formatted_response"]
            assert "Level 1: Intuition" in content, "Missing Level 1"
            assert "Level 2:" in content, "Missing Level 2"
            assert "Level 3:" in content, "Missing Level 3"
            assert "Level 4:" in content, "Missing Level 4"
            assert "```python" in content, "Missing code example"
            assert "$$" in content or "\\[" in content, "Missing LaTeX formula"
        
        print(f"✅ Math Formula Test: {query}")
        print(f"   Mode: {data['mode']} (confidence: {data['confidence']*100:.0f}%)")
        print(f"   Response length: {len(data['response']['formatted_response'])} chars")
        print(f"   Preview: {data['response']['formatted_response'][:100]}...")
        print()
        return True
        
    except AssertionError as e:
        print(f"❌ Math Formula Test Failed: {query}")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Math Formula Test Failed: {query}")
        print(f"   Error: {e}")
        return False

def test_navigate_mode(query: str) -> bool:
    """Test navigate mode query"""
    try:
        response = requests.post(
            f"{API_BASE}/api/query",
            json={"query": query},
            timeout=10
        )
        data = response.json()
        
        assert data["mode"] == "navigate", f"Expected navigate mode, got {data['mode']}"
        assert "top_results" in data["response"], "Missing top_results"
        
        print(f"✅ Navigate Mode Test: {query}")
        print(f"   Results: {data['response'].get('total_results', 0)}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Navigate Mode Test Failed: {query}")
        print(f"   Error: {e}")
        return False

def main():
    print("=" * 80)
    print("LUMINATE AI - FRONTEND INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Test 1: Backend Health
    print("TEST 1: Backend Health Check")
    print("-" * 80)
    if not test_api_health():
        print("\n❌ Backend is not running. Please start it first:")
        print("   cd development/backend")
        print("   source .venv/bin/activate")
        print("   python -m uvicorn fastapi_service.main:app --reload")
        sys.exit(1)
    print()
    
    # Test 2: Math Translation Agent (5 formulas)
    print("TEST 2: Math Translation Agent")
    print("-" * 80)
    
    math_tests = [
        "explain gradient descent",
        "what is backpropagation",
        "cross-entropy loss",
        "sigmoid function",
        "bayes theorem"
    ]
    
    math_results = [test_math_formula(q) for q in math_tests]
    
    # Test 3: Navigate Mode
    print("TEST 3: Navigate Mode")
    print("-" * 80)
    
    navigate_tests = [
        "find week 3 slides",
        "search for assignment 3"
    ]
    
    navigate_results = [test_navigate_mode(q) for q in navigate_tests]
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    math_passed = sum(math_results)
    math_total = len(math_results)
    nav_passed = sum(navigate_results)
    nav_total = len(navigate_results)
    
    print(f"Math Translation Agent: {math_passed}/{math_total} tests passed")
    print(f"Navigate Mode: {nav_passed}/{nav_total} tests passed")
    print()
    
    if math_passed == math_total and nav_passed == nav_total:
        print("✅ ALL TESTS PASSED!")
        print()
        print("🎉 Your Chrome extension is ready to use!")
        print()
        print("To test in Chrome:")
        print("1. Open chrome://extensions/")
        print("2. Enable 'Developer mode'")
        print("3. Click 'Load unpacked'")
        print("4. Select: /Users/aazain/Documents/GitHub/luminate-ai/chrome-extension/dist")
        print("5. Open any webpage and click the extension icon")
        print("6. Try these queries in Educate Mode:")
        for q in math_tests[:3]:
            print(f"   - {q}")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the errors above and fix them.")
        sys.exit(1)

if __name__ == "__main__":
    main()
