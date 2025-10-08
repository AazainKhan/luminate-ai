"""External Resources Agent - Search YouTube, OER Commons, and educational links."""

import os
import re
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup


def search_youtube(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Search YouTube for educational videos using YouTube Data API."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        print("⚠️  YOUTUBE_API_KEY not found. Skipping YouTube search.")
        return []
    
    # Enhance query with AI/ML context
    enhanced_query = _enhance_query_for_ai_context(query)
    
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": enhanced_query,  # Use enhanced query
            "type": "video",
            "maxResults": max_results,
            "videoCategoryId": "27",  # Education category
            "key": api_key,
            "safeSearch": "strict",
            "relevanceLanguage": "en"
        }
        
        # Add referer header to pass HTTP referrer restrictions
        headers = {
            "Referer": "http://localhost:8000/"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            videos.append({
                "title": snippet["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "description": snippet["description"][:200],
                "type": "YouTube Video",
                "channel": snippet["channelTitle"]
            })
        
        return videos
    
    except Exception as e:
        print(f"⚠️  YouTube search error: {e}")
        return []


def search_oer_commons(query: str, max_results: int = 1) -> List[Dict[str, str]]:
    """
    Search OER Commons - returns search page URL with correct format.
    Format: https://oercommons.org/search?search_source=site&f.search={query}
    """
    resources = []
    try:
        # Use correct OER Commons search URL format
        search_url = f"https://oercommons.org/search?search_source=site&f.search={quote_plus(query)}"
        resources.append({
            "title": f"OER Commons: {query}",
            "url": search_url,
            "description": f"Search open educational resources about {query}",
            "type": "OER Commons",
            "channel": "OER Commons"
        })
    except Exception as e:
        print(f"⚠️  OER Commons error: {e}")
    
    return resources


def _enhance_query_for_ai_context(query: str) -> str:
    """
    Enhance query with AI/ML context to avoid ambiguity.
    
    Examples:
    - "NLP" → "natural language processing machine learning"
    - "CNN" → "convolutional neural networks deep learning"
    - "agents" → "intelligent agents artificial intelligence"
    
    Args:
        query: Original search query
        
    Returns:
        Enhanced query with AI/ML context
    """
    query_lower = query.lower()
    
    # Common AI/ML abbreviations that need context
    enhancements = {
        'nlp': 'natural language processing machine learning',
        'cnn': 'convolutional neural networks deep learning',
        'rnn': 'recurrent neural networks deep learning',
        'lstm': 'long short term memory networks',
        'gru': 'gated recurrent unit neural networks',
        'ann': 'artificial neural networks',
        'dnn': 'deep neural networks',
        'gan': 'generative adversarial networks',
        'rl': 'reinforcement learning artificial intelligence',
        'ml': 'machine learning artificial intelligence',
        'ai': 'artificial intelligence machine learning',
        'svm': 'support vector machines machine learning',
        'knn': 'k nearest neighbors algorithm',
        'dt': 'decision tree machine learning',
        'rf': 'random forest machine learning',
        'cv': 'computer vision deep learning',
    }
    
    # Check for exact abbreviation match
    for abbrev, expanded in enhancements.items():
        # Match whole word only (not part of larger word)
        if query_lower == abbrev or f' {abbrev} ' in f' {query_lower} ' or query_lower.startswith(f'{abbrev} ') or query_lower.endswith(f' {abbrev}'):
            return expanded
    
    # If query contains AI/ML keywords, return as-is
    ai_keywords = ['neural', 'machine learning', 'deep learning', 'artificial intelligence', 
                   'reinforcement', 'supervised', 'unsupervised', 'classification', 'regression']
    
    if any(keyword in query_lower for keyword in ai_keywords):
        return query
    
    # Default: append "machine learning" context
    return f"{query} machine learning artificial intelligence"


def search_educational_resources(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Search for educational resources using direct sources."""
    resources = []
    
    # Enhance query with AI/ML context to avoid ambiguity
    enhanced_query = _enhance_query_for_ai_context(query)
    
    # 1. Wikipedia article (direct link via API)
    try:
        wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(enhanced_query)}&limit=1&format=json"
        headers = {
            'User-Agent': 'LuminateAI/1.0 (Educational Assistant; mailto:support@example.com)'
        }
        response = requests.get(wiki_search_url, headers=headers, timeout=3)
        if response.ok:
            data = response.json()
            if len(data) > 3 and len(data[3]) > 0:
                article_url = data[3][0]
                article_title = data[1][0] if len(data[1]) > 0 else query
                resources.append({
                    "title": f"Wikipedia: {article_title}",
                    "url": article_url,
                    "description": f"Comprehensive overview of {article_title}",
                    "type": "Wikipedia",
                    "channel": "Wikipedia"
                })
                print(f"✓ Found Wikipedia article: {article_title}")
        else:
            print(f"⚠️  Wikipedia returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  Wikipedia search error: {e}")
    
    return resources


def external_resources_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search external educational resources for supplementary learning materials.
    
    Searches:
    - YouTube educational videos (3 direct links via API)
    - Wikipedia articles (1 direct link via API)
    - OER Commons (1 search page link)
    """
    original_query = state.get("original_query", "")
    understood_query = state.get("understood_query", original_query)
    
    # Use the understood query for better results
    search_query = understood_query if understood_query else original_query
    
    print(f"🔍 Searching external resources for: {search_query}")
    
    external_resources = []
    
    # Search YouTube (3 videos - direct links via API)
    youtube_results = search_youtube(search_query, max_results=3)
    external_resources.extend(youtube_results)
    print(f"  → YouTube: {len(youtube_results)} videos")
    
    # Search Wikipedia + Khan Academy + MIT OCW (curated direct links)
    edu_results = search_educational_resources(search_query, max_results=10)
    external_resources.extend(edu_results)
    print(f"  → Educational: {len(edu_results)} resources")
    
    # Search OER Commons (1 curated direct link)
    oer_results = search_oer_commons(search_query, max_results=1)
    external_resources.extend(oer_results)
    print(f"  → OER Commons: {len(oer_results)} resources")
    
    print(f"✅ Found {len(external_resources)} total external resources")
    
    state["external_resources"] = external_resources
    return state


def _format_external_resources(resources: List[Dict[str, str]]) -> str:
    """Format external resources for LLM context."""
    if not resources:
        return "No external resources found."
    
    formatted = []
    for i, resource in enumerate(resources, 1):
        formatted.append(
            f"{i}. [{resource['type']}] {resource['title']}\n"
            f"   URL: {resource['url']}\n"
            f"   Description: {resource['description']}"
        )
    
    return "\n\n".join(formatted)
