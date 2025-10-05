"""
Query Understanding Agent for Navigate Mode
Expands acronyms, identifies topics, and extracts search terms.
"""

from typing import Dict
import json
import os
from dotenv import load_dotenv
from llm_config import get_llm

# Load environment variables
load_dotenv()

import json
from typing import Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


# Initialize Ollama LLM
llm = ChatOllama(model="llama3.2:latest", temperature=0.3)


QUERY_UNDERSTANDING_PROMPT = """You are a query parser for COMP237 (Introduction to Artificial Intelligence) at Centennial College.

Your task: Analyze the student's search query and extract structured information to improve search results.

COMP237 Common Acronyms:
- ML = Machine Learning
- DL = Deep Learning  
- NN = Neural Networks
- CNN = Convolutional Neural Networks
- RNN = Recurrent Neural Networks
- NLP = Natural Language Processing
- AI = Artificial Intelligence
- BFS = Breadth-First Search
- DFS = Depth-First Search
- A* = A-star search algorithm
- KNN = K-Nearest Neighbors

Common Topics in COMP237:
- Search algorithms (BFS, DFS, A*, heuristics)
- Machine learning (supervised, unsupervised, reinforcement)
- Neural networks (perceptrons, backpropagation, deep learning)
- Natural language processing
- Knowledge representation
- Logic and reasoning
- Computer vision

Your job:
1. Expand any acronyms in the query
2. Identify the main topic category from COMP237
3. Extract 3-5 key search terms (include synonyms)
4. Infer the student's goal (one of: learn_concept, find_assignment, review_for_exam, clarify_confusion, find_example)

Student Query: "{query}"

Respond ONLY with valid JSON in this exact format:
{{
  "expanded_query": "the query with acronyms expanded",
  "category": "main topic category",
  "search_terms": ["term1", "term2", "term3", "term4", "term5"],
  "student_goal": "learn_concept|find_assignment|review_for_exam|clarify_confusion|find_example",
  "reasoning": "brief explanation of your analysis"
}}

Do not include any text outside the JSON object."""


def query_understanding_agent(state: Dict) -> Dict:
    """
    Parse and enhance student query.
    
    Args:
        state: Contains 'query' key with raw student input
        
    Returns:
        Updated state with 'parsed_query' containing:
        - expanded_query: Query with acronyms expanded
        - category: Main topic category
        - search_terms: List of key terms
        - student_goal: Inferred intent
    """
    query = state["query"]
    
    # Get LLM instance from centralized config
    llm = get_llm(temperature=0.3)
    
    # Build prompt
    prompt = QUERY_UNDERSTANDING_PROMPT.format(query=query)
    
    # Get LLM response
    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        parsed_query = json.loads(response_text)
        
        state["parsed_query"] = parsed_query
        
        # Also set these for external resources agent
        state["original_query"] = query
        state["understood_query"] = parsed_query.get("expanded_query", query)
        
    except Exception as e:
        print(f"Error in query understanding: {e}")
        # Fallback: basic parsing
        state["parsed_query"] = {
            "expanded_query": query,
            "category": "general",
            "search_terms": query.split()[:5],
            "student_goal": "learn_concept",
            "reasoning": "fallback due to parsing error"
        }
        # Also set these for external resources agent in fallback case
        state["original_query"] = query
        state["understood_query"] = query
    
    return state


if __name__ == "__main__":
    # Test the agent
    print("Testing Query Understanding Agent\n")
    
    test_queries = [
        "What is ML?",
        "NN backpropagation",
        "BFS vs DFS",
        "neural network training",
        "how does A* algorithm work"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        state = {"query": query}
        result = query_understanding_agent(state)
        
        parsed = result["parsed_query"]
        print(f"\nExpanded: {parsed['expanded_query']}")
        print(f"Category: {parsed['category']}")
        print(f"Search Terms: {', '.join(parsed['search_terms'])}")
        print(f"Goal: {parsed['student_goal']}")
        print(f"Reasoning: {parsed['reasoning']}")
