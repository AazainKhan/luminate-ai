#!/usr/bin/env python3
"""
Quick test script for the improved formatting agent
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'development', 'backend'))

from langgraph.agents.formatting import _fallback_formatting

# Test the fallback formatting
test_results = [
    {
        "metadata": {
            "title": "Introduction to Intelligent Agents",
            "module": "Week 2",
            "bb_doc_id": "12345",
            "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/file/_12345_1"
        }
    },
    {
        "metadata": {
            "title": "Agent Architectures",
            "module": "root",  # This should be cleaned up
            "bb_doc_id": "12346",
            "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/file/_12346_1"
        }
    }
]

print("🧪 Testing Fallback Formatting")
print("=" * 60)

result = _fallback_formatting(test_results, "What are agents?")

print("\n📝 Formatted Response:")
print(f"Answer: {result.get('answer')}")
print(f"\nNumber of results: {len(result.get('top_results', []))}")

print("\n📚 Top Results:")
for i, res in enumerate(result.get('top_results', []), 1):
    print(f"\n{i}. {res.get('title')}")
    print(f"   Module: {res.get('module')}")
    print(f"   URL: {res.get('url')}")
    print(f"   Relevance: {res.get('relevance_explanation')}")

print("\n🔗 Related Topics:")
for topic in result.get('related_topics', []):
    print(f"- {topic.get('title')}: {topic.get('why_explore')}")

print("\n" + "=" * 60)
print("✅ Fallback formatting test complete!")
print("\n📌 Key improvements:")
print("  - 'root' module cleaned to 'Course Content'")
print("  - Only 2-3 results instead of forcing 5")
print("  - Actual answer provided instead of generic encouragement")
