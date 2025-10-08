"""
Simple Orchestrator Classification Function
Exports a standalone function for FastAPI to use without full graph dependencies.
"""

from typing import Dict, Literal

# Mode classification keywords
NAVIGATE_INDICATORS = {
    "find", "search", "look up", "get", "fetch",
    "show me", "give me", "what is", "who is", "when is", "where is",
    "video", "youtube", "tutorial", "article", "resource",
    "example", "documentation", "reference",
    "definition", "overview", "summary", "introduction",
}

EDUCATE_INDICATORS = {
    "explain", "understand", "learn", "teach", "why", "how",
    "confused", "don't get", "struggling", "help me",
    "formula", "equation", "math", "calculation", "derive",
    "what does this mean", "break down", "simplify",
    "solve", "implement", "code", "algorithm", "step by step",
    "quiz me", "test me", "practice", "check my understanding",
}

# COMP-237 core topics (always educate)
COMP237_TOPICS = {
    "dfs", "bfs", "a* search", "a star", "ucs", "greedy search",
    "gradient descent", "logistic regression", "linear regression",
    "neural network", "backpropagation", "activation function",
    "naive bayes", "tf-idf", "bag of words",
    "k-means", "clustering", "computer vision",
    "intelligent agent", "heuristic", "admissible",
}


def classify_query_mode(query: str) -> Dict[str, any]:
    """
    Classify query into Navigate or Educate mode.
    
    Returns:
        {
            'mode': 'navigate' or 'educate',
            'confidence': float (0-1),
            'reasoning': str
        }
    """
    query_lower = query.lower()
    
    # Check for COMP-237 topics
    comp237_matches = [topic for topic in COMP237_TOPICS if topic in query_lower]
    if comp237_matches:
        return {
            'mode': 'educate',
            'confidence': 0.95,
            'reasoning': f"Query contains COMP-237 core topic: {comp237_matches[0]}"
        }
    
    # Count keyword indicators
    navigate_score = sum(1 for kw in NAVIGATE_INDICATORS if kw in query_lower)
    educate_score = sum(1 for kw in EDUCATE_INDICATORS if kw in query_lower)
    
    # Decision logic
    if navigate_score > educate_score and navigate_score >= 2:
        return {
            'mode': 'navigate',
            'confidence': min(0.85, 0.6 + navigate_score * 0.1),
            'reasoning': f"Information retrieval pattern detected ({navigate_score} navigate indicators)"
        }
    
    elif educate_score > navigate_score and educate_score >= 2:
        return {
            'mode': 'educate',
            'confidence': min(0.85, 0.6 + educate_score * 0.1),
            'reasoning': f"Learning/tutoring pattern detected ({educate_score} educate indicators)"
        }
    
    elif navigate_score > educate_score:
        return {
            'mode': 'navigate',
            'confidence': 0.65,
            'reasoning': "Slight preference for information retrieval"
        }
    
    else:
        # Default to Educate for COMP-237 context
        return {
            'mode': 'educate',
            'confidence': 0.60,
            'reasoning': "Default to tutoring mode for educational context"
        }
