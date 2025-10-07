#!/usr/bin/env python3
"""Test external resources endpoint"""
import requests
import json

response = requests.post(
    'http://localhost:8000/external-resources',
    json={'query': 'cnn'}
)

data = response.json()
print(f"Total resources: {data['count']}")
print("\nResource types:")
for resource in data['resources']:
    print(f"  - {resource['type']}: {resource['title']}")
    print(f"    URL: {resource['url']}")
