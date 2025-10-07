#!/usr/bin/env python3
"""
Quick test script for LangGraph Navigate endpoint
Run this while the backend is running to test the workflow
"""

import requests
import json

def test_langgraph_navigate():
    """Test the LangGraph navigate endpoint"""
    url = "http://localhost:8000/langgraph/navigate"
    
    payload = {
        "query": "what is in module 2"
    }
    
    print("🧪 Testing LangGraph Navigate endpoint...")
    print(f"📤 Query: {payload['query']}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Response received:\n")
            print(f"📝 Message: {data.get('formatted_response', 'N/A')}\n")
            print(f"📚 Top Results: {len(data.get('top_results', []))} results")
            for i, result in enumerate(data.get('top_results', [])[:3], 1):
                print(f"  {i}. {result.get('title', 'Untitled')} - {result.get('module', 'Unknown module')}")
            
            print(f"\n🔗 Related Topics: {len(data.get('related_topics', []))} topics")
            for topic in data.get('related_topics', []):
                if isinstance(topic, dict):
                    print(f"  - {topic.get('title', 'Unknown')}: {topic.get('why_explore', 'N/A')}")
                else:
                    print(f"  - {topic}")
            
            if data.get('next_steps'):
                print(f"\n➡️  Next Steps: {data['next_steps']}")
            
            print("\n" + "="*60)
            print("Full JSON Response:")
            print("="*60)
            print(json.dumps(data, indent=2))
            
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend. Is it running on http://localhost:8000?")
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_langgraph_navigate()
