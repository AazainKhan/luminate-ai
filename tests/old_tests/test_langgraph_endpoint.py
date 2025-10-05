#!/usr/bin/env python3
"""
Quick test for LangGraph Navigate endpoint
Usage: python test_langgraph_endpoint.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Health check passed")
        print(f"  ChromaDB documents: {data['chromadb_documents']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False
    
    return True


def test_langgraph_navigate(query: str):
    """Test LangGraph Navigate endpoint"""
    print(f"\n🤖 Testing /langgraph/navigate with query: '{query}'")
    
    start_time = datetime.now()
    
    response = requests.post(
        f"{BASE_URL}/langgraph/navigate",
        json={"query": query}
    )
    
    elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ LangGraph Navigate succeeded ({elapsed_ms:.0f}ms)")
        print(f"\n📝 Formatted Response:")
        print(data['formatted_response'][:300] + "...")
        
        print(f"\n📚 Top Results: {len(data['top_results'])}")
        for i, result in enumerate(data['top_results'][:3], 1):
            print(f"\n  {i}. {result.get('metadata', {}).get('title', 'Untitled')}")
            print(f"     Score: {result.get('score', 'N/A')}")
            if result.get('relevance_explanation'):
                print(f"     💡 {result['relevance_explanation']}")
        
        print(f"\n🔗 Related Topics: {', '.join(data['related_topics'][:5])}")
        
        if data.get('next_steps'):
            print(f"\n➡️  Next Steps:")
            for step in data['next_steps'][:3]:
                print(f"   • {step}")
        
        return True
    else:
        print(f"❌ LangGraph Navigate failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing Luminate AI LangGraph Navigate Endpoint")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n❌ Backend is not running. Start with:")
        print("   cd development/backend/fastapi_service")
        print("   uvicorn main:app --reload")
        return
    
    # Test queries
    test_queries = [
        "What is supervised learning?",
        "Explain neural networks",
        "How does gradient descent work?"
    ]
    
    for query in test_queries:
        success = test_langgraph_navigate(query)
        if not success:
            break
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
