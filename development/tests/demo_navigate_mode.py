#!/usr/bin/env python3
"""
Demo script for Navigate Mode with LangGraph
Shows the multi-agent workflow in action with different LLM providers.
"""

import sys
from pathlib import Path

# Add langgraph to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "langgraph"))

from navigate_graph import query_navigate_mode
import json


def demo_query(query: str):
    """Run Navigate Mode for a query and display results."""
    print(f"\n{'='*80}")
    print(f"🔍 Query: {query}")
    print(f"{'='*80}")
    
    try:
        result = query_navigate_mode(query)
        
        # Show parsed query
        if "parsed_query" in result:
            parsed = result["parsed_query"]
            print(f"\n📝 Query Understanding:")
            print(f"   Expanded: {parsed.get('expanded_query', 'N/A')}")
            print(f"   Category: {parsed.get('category', 'N/A')}")
            print(f"   Goal: {parsed.get('student_goal', 'N/A')}")
        
        # Show retrieval stats
        if "retrieved_chunks" in result:
            chunks = result["retrieved_chunks"]
            print(f"\n📚 Retrieval: Found {len(chunks)} relevant documents")
        
        # Show formatted response
        if "formatted_response" in result:
            formatted = result["formatted_response"]
            
            # Top results
            top_results = formatted.get("top_results", [])
            print(f"\n✅ Top Results ({len(top_results)}):")
            for i, res in enumerate(top_results[:3], 1):
                print(f"\n   {i}. {res.get('title', 'Unknown')}")
                print(f"      Module: {res.get('module', 'N/A')}")
                print(f"      Relevance: {res.get('relevance_explanation', 'N/A')[:80]}...")
                print(f"      URL: {res.get('url', 'N/A')[:60]}...")
            
            # Related topics
            related = formatted.get("related_topics", [])
            if related:
                print(f"\n🔗 Related Topics ({len(related)}):")
                for topic in related:
                    print(f"   - {topic}")
            
            # Next steps
            next_step = formatted.get("suggested_next_step", "")
            if next_step:
                print(f"\n➡️  Next Step: {next_step}")
        
        print(f"\n{'='*80}\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run Navigate Mode demo with sample queries."""
    print("\n" + "="*80)
    print("NAVIGATE MODE DEMO - LangGraph Multi-Agent System")
    print("="*80)
    print("\nThis demo shows the 4-agent workflow:")
    print("  1. Query Understanding  - Expands acronyms, identifies topics")
    print("  2. Retrieval Agent      - Searches ChromaDB via FastAPI")
    print("  3. Context Agent        - Adds related topics from graph")
    print("  4. Formatting Agent     - Structures output for UI")
    print("\n" + "="*80)
    
    # Sample queries
    queries = [
        "What is ML?",
        "neural networks basics",
        "BFS vs DFS algorithms"
    ]
    
    print(f"\nRunning {len(queries)} demo queries...")
    
    results = []
    for query in queries:
        success = demo_query(query)
        results.append((query, success))
    
    # Summary
    print("\n" + "="*80)
    print("DEMO SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for query, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{status}: {query}")
    
    print(f"\n{passed}/{total} queries successful ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 Navigate Mode is working perfectly with LangGraph!")
    else:
        print(f"\n⚠️  {total - passed} query(ies) failed.")
    
    print("\nYou can switch LLM providers by editing .env:")
    print("  LLM_PROVIDER=gemini|openai|anthropic|ollama")
    print("  MODEL_NAME=gemini-2.0-flash|gpt-4o-mini|claude-3-5-sonnet|llama3.2")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
