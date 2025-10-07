#!/usr/bin/env python3
"""Test NLP query to verify it finds Natural Language Processing resources"""
import requests

query = "NLP"
print(f"Testing query: {query}")
print("=" * 60)

response = requests.post(
    'http://localhost:8000/external-resources',
    json={'query': query}
)

data = response.json()
print(f"\nTotal resources: {data['count']}")
print("\nResources found:")
print("-" * 60)

for resource in data['resources']:
    print(f"\n✓ {resource['type']}: {resource['title']}")
    if 'neuro' in resource['title'].lower() and 'linguistic' in resource['title'].lower():
        print("  ⚠️  WARNING: Found Neuro-Linguistic Programming (should be NLP = Natural Language Processing)")
    if 'natural language' in resource['title'].lower():
        print("  ✅ CORRECT: Natural Language Processing")
