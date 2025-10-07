"""
Test client for Luminate AI Navigate API
Purpose: Test the FastAPI /query/navigate endpoint

Usage:
    python test_navigate_api.py
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime


class NavigateAPIClient:
    """Simple client for testing the Navigate API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics"""
        response = requests.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        min_score: float = 0.0,
        module_filter: str = None,
        content_type_filter: str = None,
        include_no_url: bool = False
    ) -> Dict[str, Any]:
        """Execute Navigate search query"""
        payload = {
            "query": query,
            "n_results": n_results,
            "min_score": min_score,
            "include_no_url": include_no_url
        }
        
        if module_filter:
            payload["module_filter"] = module_filter
        if content_type_filter:
            payload["content_type_filter"] = content_type_filter
        
        response = requests.post(
            f"{self.base_url}/query/navigate",
            json=payload
        )
        response.raise_for_status()
        return response.json()


def print_separator(title: str = ""):
    """Print formatted separator"""
    if title:
        print(f"\n{'=' * 80}")
        print(f"{title:^80}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'=' * 80}\n")


def print_search_results(response: Dict[str, Any]):
    """Pretty print search results"""
    print(f"Query: '{response['query']}'")
    print(f"Results: {response['total_results']}")
    print(f"Execution time: {response['execution_time_ms']:.2f}ms")
    print()
    
    for i, result in enumerate(response['results'], 1):
        print(f"Result {i} (score: {result['score']:.4f}):")
        print(f"  Title: {result['title']}")
        print(f"  Module: {result['module']}")
        print(f"  Type: {result['content_type']}")
        if result['live_url']:
            print(f"  URL: {result['live_url']}")
        else:
            print(f"  URL: (no Blackboard URL)")
        print(f"  Excerpt: {result['excerpt']}")
        if result['tags']:
            print(f"  Tags: {', '.join(result['tags'])}")
        print()


def run_tests():
    """Run comprehensive API tests"""
    client = NavigateAPIClient()
    
    try:
        # Test 1: Health Check
        print_separator("Test 1: Health Check")
        health = client.health_check()
        print(f"Status: {health['status']}")
        print(f"ChromaDB Documents: {health['chromadb_documents']}")
        print(f"Timestamp: {health['timestamp']}")
        
        # Test 2: Statistics
        print_separator("Test 2: Collection Statistics")
        stats = client.get_stats()
        print(f"Total Documents: {stats['stats']['total_documents']}")
        print(f"Collection: {stats['stats']['collection_name']}")
        print(f"Embedding Model: {stats['stats']['embedding_model']}")
        print(f"Metadata Keys: {', '.join(stats['stats']['sample_metadata_keys'])}")
        
        # Test 3: Sample Queries
        test_queries = [
            {
                "query": "machine learning algorithms",
                "n_results": 5,
                "description": "Basic search for ML content"
            },
            {
                "query": "neural networks deep learning",
                "n_results": 5,
                "min_score": 0.0,
                "description": "Neural networks with no score filter"
            },
            {
                "query": "TCP handshake protocol",
                "n_results": 5,
                "description": "Networking topic search"
            },
            {
                "query": "course syllabus assignment deadlines",
                "n_results": 3,
                "description": "Course admin content"
            },
            {
                "query": "search algorithms breadth first depth first",
                "n_results": 5,
                "module_filter": "Root",
                "description": "Search algorithms filtered by Root module"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print_separator(f"Test {i+2}: {test_case.pop('description')}")
            response = client.search(**test_case)
            print_search_results(response)
        
        # Test 4: Edge Cases
        print_separator("Test: Empty Results (should still work)")
        response = client.search(
            query="quantum computing blockchain cryptocurrency",
            n_results=5
        )
        print_search_results(response)
        
        # Test 5: High Score Threshold
        print_separator("Test: High Score Threshold (min_score=0.3)")
        response = client.search(
            query="artificial intelligence",
            n_results=5,
            min_score=0.3
        )
        print_search_results(response)
        
        print_separator("All Tests Completed Successfully! ✅")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API")
        print("Make sure the FastAPI service is running:")
        print("  python development/backend/fastapi_service/main.py")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Response: {e.response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print_separator("Luminate AI Navigate API Test Client")
    print("Starting tests...\n")
    run_tests()
