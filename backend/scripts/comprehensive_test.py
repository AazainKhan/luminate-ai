"""
Comprehensive test suite for the Luminate AI Course Marshal backend
Tests all components and logs results for iterative development
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.agents.tutor_agent import run_agent
from app.rag.chromadb_client import get_chromadb_client
from app.observability import get_langfuse_client, flush_langfuse


class TestResults:
    """Store and format test results"""
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    def add_result(self, test_name, status, details):
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def print_summary(self):
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warning = sum(1 for r in self.results if r["status"] == "WARN")
        
        print(f"\nTotal Tests: {len(self.results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warning}")
        print(f"\nSuccess Rate: {(passed/len(self.results)*100):.1f}%")
        print(f"Duration: {(datetime.now() - self.start_time).total_seconds():.2f}s")
        
    def save_to_file(self, filename="test_results.json"):
        output_path = backend_dir / "test_output" / filename
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                "timestamp": self.start_time.isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_path}")


def test_chromadb_connection(results):
    """Test 1: ChromaDB Connection"""
    print("\n" + "=" * 80)
    print("TEST 1: ChromaDB Connection")
    print("=" * 80)
    
    try:
        client = get_chromadb_client()
        info = client.get_collection_info()
        
        if info.get("count", 0) > 0:
            print(f"✅ PASS: ChromaDB connected")
            print(f"   Collection: {info['name']}")
            print(f"   Documents: {info['count']}")
            results.add_result("ChromaDB Connection", "PASS", info)
            return True
        else:
            print(f"⚠️  WARN: ChromaDB connected but empty")
            results.add_result("ChromaDB Connection", "WARN", "Collection is empty")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.add_result("ChromaDB Connection", "FAIL", str(e))
        return False


def test_langfuse_connection(results):
    """Test 2: Langfuse Connection"""
    print("\n" + "=" * 80)
    print("TEST 2: Langfuse Connection")
    print("=" * 80)
    
    try:
        client = get_langfuse_client()
        
        if client is None:
            print(f"⚠️  WARN: Langfuse not configured")
            results.add_result("Langfuse Connection", "WARN", "Not configured")
            return False
        
        # Try to create a test span
        span = client.start_span(name="test_connection")
        span.end()
        flush_langfuse()
        
        print(f"✅ PASS: Langfuse connected")
        results.add_result("Langfuse Connection", "PASS", "Client initialized")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.add_result("Langfuse Connection", "FAIL", str(e))
        return False


def test_agent_query(query, expected_keywords, results, test_name):
    """Test agent with a specific query"""
    print(f"\n{'=' * 80}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 80}")
    print(f"Query: '{query}'")
    
    try:
        result = run_agent(
            query=query,
            user_id="test_user",
            user_email="test@my.centennialcollege.ca"
        )
        
        response = result.get("response", "")
        error = result.get("error")
        intent = result.get("intent")
        model = result.get("model_used")
        sources = result.get("sources", [])
        
        print(f"\n📤 Response Preview: {response[:200]}...")
        print(f"🎯 Intent: {intent}")
        print(f"🤖 Model: {model}")
        print(f"📚 Sources: {len(sources)} documents")
        
        if error:
            print(f"⚠️  Error: {error}")
        
        # Check if expected keywords are in response
        found_keywords = [kw for kw in expected_keywords if kw.lower() in response.lower()]
        
        if found_keywords:
            print(f"✅ PASS: Found expected content: {found_keywords}")
            results.add_result(test_name, "PASS", {
                "query": query,
                "response_length": len(response),
                "intent": intent,
                "model": model,
                "sources_count": len(sources),
                "found_keywords": found_keywords
            })
            return True
        else:
            print(f"⚠️  WARN: Expected keywords not found: {expected_keywords}")
            results.add_result(test_name, "WARN", {
                "query": query,
                "response": response[:500],
                "expected": expected_keywords,
                "intent": intent
            })
            return False
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.add_result(test_name, "FAIL", str(e))
        return False


def main():
    """Run all tests"""
    print("\n🧪 COMPREHENSIVE BACKEND TEST SUITE")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = TestResults()
    
    # Test 1: Infrastructure
    print("\n\n📦 INFRASTRUCTURE TESTS")
    print("=" * 80)
    
    chromadb_ok = test_chromadb_connection(results)
    langfuse_ok = test_langfuse_connection(results)
    
    # Test 2: Agent Queries
    print("\n\n🤖 AGENT QUERY TESTS")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "Course Information Query",
            "query": "What is COMP 237?",
            "expected": ["COMP", "237", "Artificial Intelligence", "course"]
        },
        {
            "name": "Learning Outcomes Query",
            "query": "What are the learning outcomes for this course?",
            "expected": ["learning", "outcome", "neural", "network"]
        },
        {
            "name": "Schedule Query",
            "query": "When is the midterm exam?",
            "expected": ["midterm", "exam", "week", "date"]
        },
        {
            "name": "Concept Explanation",
            "query": "Explain backpropagation in neural networks",
            "expected": ["backpropagation", "gradient", "neural", "network"]
        },
        {
            "name": "Code Request (Should be Blocked)",
            "query": "Write complete code for Assignment 1",
            "expected": ["cannot", "academic", "integrity", "guidance"]
        },
        {
            "name": "Out of Scope (Should be Blocked)",
            "query": "What's the weather today?",
            "expected": ["COMP 237", "scope", "cannot", "course"]
        }
    ]
    
    for test_case in test_cases:
        test_agent_query(
            query=test_case["query"],
            expected_keywords=test_case["expected"],
            results=results,
            test_name=test_case["name"]
        )
    
    # Print summary
    results.print_summary()
    
    # Save results
    results.save_to_file(f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    # Print recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    failed_tests = [r for r in results.results if r["status"] == "FAIL"]
    warned_tests = [r for r in results.results if r["status"] == "WARN"]
    
    if failed_tests:
        print("\n🔴 Critical Issues:")
        for test in failed_tests:
            print(f"   - {test['test']}: {test['details']}")
    
    if warned_tests:
        print("\n🟡 Warnings:")
        for test in warned_tests:
            print(f"   - {test['test']}")
    
    if not failed_tests and not warned_tests:
        print("\n🎉 All tests passed! System is fully functional.")
    
    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    
    if not chromadb_ok:
        print("1. Fix ChromaDB RAG query issue")
        print("   - Refactor to use LangChain's Chroma wrapper")
        print("   - Test with: python backend/verify_rag.py")
    
    if not langfuse_ok:
        print("2. Configure Langfuse API keys")
        print("   - Get keys from http://localhost:3000")
        print("   - Update backend/.env")
    
    print("3. Test frontend extension")
    print("   - Load in Chrome")
    print("   - Test student chat interface")
    
    print("\n✅ Test suite complete!")


if __name__ == "__main__":
    main()

