#!/usr/bin/env python3
"""Test enhanced query context"""
import sys
sys.path.insert(0, '/Users/aazain/Documents/GitHub/luminate-ai/development/backend/langgraph/agents')

from external_resources import _enhance_query_for_ai_context

test_queries = [
    "NLP",
    "CNN", 
    "natural language processing",
    "convolutional neural networks",
    "agents",
    "linear algebra",
    "AI"
]

print("Query Enhancement Test")
print("=" * 60)

for query in test_queries:
    enhanced = _enhance_query_for_ai_context(query)
    print(f"Original: {query:30} → Enhanced: {enhanced}")
