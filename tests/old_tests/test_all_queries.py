#!/usr/bin/env python3
"""Test external resources with different queries"""
import requests

queries = [
    "convolutional neural networks",
    "natural language processing",
    "reinforcement learning",
    "linear algebra"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    response = requests.post(
        'http://localhost:8000/external-resources',
        json={'query': query}
    )
    
    data = response.json()
    print(f"Total: {data['count']} resources\n")
    
    for resource in data['resources']:
        print(f"✓ {resource['type']}: {resource['title']}")
