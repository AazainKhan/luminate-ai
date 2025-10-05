#!/usr/bin/env python3
"""Debug Wikipedia search"""
import requests
from urllib.parse import quote_plus

query = "convolutional neural networks"
wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(query)}&limit=1&format=json"

print(f"Query: {query}")
print(f"URL: {wiki_search_url}")

response = requests.get(wiki_search_url, timeout=3)
print(f"Status: {response.status_code}")

data = response.json()
print(f"Response length: {len(data)}")
print(f"Data: {data}")

if len(data) > 3 and len(data[3]) > 0:
    print(f"✓ Article URL found: {data[3][0]}")
else:
    print("✗ No article URL found")
