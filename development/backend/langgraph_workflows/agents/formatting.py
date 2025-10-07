"""
Formatting Agent for Navigate Mode
Groups results and formats for Chrome extension UI.
"""

from typing import Dict, List
import json
import os
from dotenv import load_dotenv
from llm_config import get_llm

# Load environment variables
load_dotenv()

import json
from typing import Dict, Any, List


FORMATTING_PROMPT = """You are a knowledgeable AI navigator for COMP237 (Artificial Intelligence).

Your task: Determine if the student's question is within course scope, then answer appropriately.

Student Question: "{original_query}"

Available Course Content:
{results_summary}

CRITICAL Instructions:
1. First, determine if the question is WITHIN the scope of COMP237 (Artificial Intelligence course):
   - IN SCOPE: Questions about AI concepts, machine learning, neural networks, agents, search algorithms, NLP, computer vision, ethics in AI, course assignments, etc.
   - OUT OF SCOPE: Questions about other programming languages, web development, databases, networking, personal advice, non-AI topics, etc.

2. If OUT OF SCOPE:
   - Set "answer" to: "That topic is outside the scope of COMP237 (Introduction to Artificial Intelligence). However, I found some related course materials you might find helpful."
   - Only include results if they have SOME connection to the question
   - If NO related materials exist, return empty top_results array

3. If IN SCOPE:
   - Provide a CLEAR, DIRECT answer to the question (2-4 sentences)
   - List the most relevant course materials (1-5 results, only truly relevant ones)
   - For each material, explain WHY it's relevant

4. For each result, explain in 1 sentence WHY it's relevant to their specific question
5. Suggest 2-3 related topics they might want to explore next
6. Keep tone helpful and conversational, not generic or repetitive

Respond ONLY with valid JSON in this exact format:
{{
  "answer": "Direct answer OR out-of-scope message...",
  "is_in_scope": true or false,
  "top_results": [
    {{
      "title": "Document title",
      "url": "Blackboard URL or document ID",
      "module": "Module name (e.g., 'Week 1', 'Week 2')",
      "relevance_explanation": "Why this specific material answers their question..."
    }}
  ],
  "related_topics": [
    {{
      "title": "Related topic title",
      "why_explore": "Brief reason to explore this"
    }}
  ]
}}

Important: 
- Only include results that are truly relevant to the question
- If 1-2 results fully answer the question, that's fine - don't pad with irrelevant content
- Make sure module names are meaningful (like "Week 1", "Week 2", not "root")
- Your answer should actually address their question, not be a generic encouragement

Do not include any text outside the JSON object."""


def formatting_agent(state: Dict) -> Dict:
    """
    Format enriched results for Chrome extension display.
    
    Args:
        state: Contains 'enriched_results' with contextual information
        
    Returns:
        Updated state with 'formatted_response' containing structured output
    """
    enriched_results = state.get("enriched_results", [])
    external_resources = state.get("external_resources", [])  # NEW: Get external resources
    student_query = state.get("query", "")
    
    if not enriched_results:
        # Check if query is likely in scope
        is_in_scope = _is_likely_in_scope(student_query)
        
        if is_in_scope:
            answer = "I couldn't find specific course materials for that question. Try rephrasing or asking about AI concepts, machine learning algorithms, neural networks, or course assignments."
        else:
            answer = "That topic appears to be outside the scope of COMP237 (Introduction to Artificial Intelligence). This course focuses on AI concepts, machine learning, neural networks, and intelligent agents. Please ask about topics covered in the course!"
        
        state["formatted_response"] = {
            "answer": answer,
            "is_in_scope": is_in_scope,
            "top_results": [],
            "related_topics": [],
            "external_resources": external_resources if is_in_scope else []  # Only include external resources if in scope
        }
        state["is_in_scope"] = is_in_scope  # Set scope flag for downstream agents
        return state
    
    # Get LLM instance from centralized config
    llm = get_llm(temperature=0.2)
    
    # Prepare summary for LLM
    results_summary = _prepare_results_summary(enriched_results)
    student_query = state.get("query", "")
    
    # Build prompt
    prompt = FORMATTING_PROMPT.format(
        original_query=student_query,
        results_summary=results_summary
    )
    
    # Get LLM response
    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        formatted_response = json.loads(response_text)
        
        # Add external resources to the response (only if in scope)
        is_in_scope = formatted_response.get("is_in_scope", True)
        formatted_response["external_resources"] = external_resources if is_in_scope else []
        
        state["formatted_response"] = formatted_response
        state["is_in_scope"] = is_in_scope  # Set scope flag for downstream agents
        
    except Exception as e:
        print(f"Error in formatting: {e}")
        # Fallback formatting
        state["formatted_response"] = _fallback_formatting(enriched_results, student_query, external_resources)
    
    return state


def _prepare_results_summary(results: List[Dict]) -> str:
    """
    Create a concise summary of results for the LLM prompt.
    
    Args:
        results: List of enriched search results
        
    Returns:
        Formatted string summary
    """
    summary_lines = []
    
    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        graph_context = result.get("graph_context", {})
        
        title = metadata.get("title", "Unknown")
        original_module = metadata.get("module", "Unknown Module")
        
        # Extract better module name from title
        module = _extract_module_from_title(title, original_module)
        
        bb_doc_id = metadata.get("bb_doc_id", "N/A")
        url = metadata.get("live_lms_url", f"bb:{bb_doc_id}")
        
        prereqs = len(graph_context.get("prerequisites", [])) if graph_context else 0
        next_steps = len(graph_context.get("next_steps", [])) if graph_context else 0
        
        summary_lines.append(
            f"{i}. {title}\n"
            f"   Module: {module}\n"
            f"   URL: {url}\n"
            f"   Has Prerequisites: {prereqs > 0}\n"
            f"   Has Next Steps: {next_steps > 0}"
        )
    
    return "\n\n".join(summary_lines)


def _extract_module_from_title(title: str, original_module: str) -> str:
    """
    Extract a meaningful module name from the title if the original module is 'Root'.
    
    Args:
        title: The content title (e.g., "Topic 8.2: Linear classifiers")
        original_module: The original module value (often "Root")
        
    Returns:
        A more meaningful module name
    """
    import re
    
    # If module is not "Root", use it as-is
    if original_module and original_module.lower() not in ["root", "unknown", "unknown module"]:
        return original_module
    
    # Try to extract "Topic X" or "Week X" from title
    topic_match = re.search(r'Topic\s+(\d+)', title, re.IGNORECASE)
    if topic_match:
        return f"Topic {topic_match.group(1)}"
    
    week_match = re.search(r'Week\s+(\d+)', title, re.IGNORECASE)
    if week_match:
        return f"Week {week_match.group(1)}"
    
    # Check for "Lab" in title
    if re.search(r'\bLab\b', title, re.IGNORECASE):
        return "Lab Materials"
    
    # Check for "Tutorial" in title
    if re.search(r'\bTutorial\b', title, re.IGNORECASE):
        return "Tutorials"
    
    # Fallback to a friendly name instead of "Root"
    return "Course Materials"


def _is_likely_in_scope(query: str) -> bool:
    """
    Quick heuristic to check if query is likely about AI/ML topics.
    
    Args:
        query: User's question
        
    Returns:
        True if likely in scope, False otherwise
    """
    query_lower = query.lower()
    
    # AI/ML related keywords
    in_scope_keywords = [
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'neural network',
        'deep learning', 'agent', 'search', 'algorithm', 'supervised', 'unsupervised',
        'classification', 'regression', 'clustering', 'perceptron', 'backpropagation',
        'gradient', 'activation', 'cnn', 'rnn', 'nlp', 'computer vision', 'reinforcement',
        'training', 'model', 'prediction', 'feature', 'dataset', 'overfitting',
        'bias', 'variance', 'precision', 'recall', 'accuracy', 'loss function',
        'optimizer', 'tensorflow', 'pytorch', 'scikit', 'numpy', 'pandas',
        'assignment', 'lab', 'homework', 'comp237', 'comp 237', 'course',
        'lecture', 'tutorial', 'quiz', 'exam', 'test', 'grade'
    ]
    
    # Check if any in-scope keyword appears
    for keyword in in_scope_keywords:
        if keyword in query_lower:
            return True
    
    # Out of scope indicators
    out_of_scope_keywords = [
        'javascript', 'html', 'css', 'react', 'vue', 'angular', 'node.js',
        'database', 'sql', 'mongodb', 'web design', 'backend', 'frontend',
        'networking', 'cybersecurity', 'devops', 'cloud', 'aws', 'azure',
        'dating', 'relationship', 'health', 'medical', 'legal', 'financial',
        'cooking', 'travel', 'sports', 'music', 'movie', 'game'
    ]
    
    for keyword in out_of_scope_keywords:
        if keyword in query_lower:
            return False
    
    # Default to in-scope if uncertain (let LLM decide in main formatting)
    return True


def _fallback_formatting(results: List[Dict], query: str, external_resources: List[Dict] = None) -> Dict:
    """
    Simple fallback formatting if LLM fails.
    
    Args:
        results: List of enriched results
        query: Original query
        external_resources: List of external educational resources
        
    Returns:
        Basic formatted response
    """
    if external_resources is None:
        external_resources = []
    
    # Check if query is likely in scope
    is_in_scope = _is_likely_in_scope(query)
    
    top_results = []
    
    # Only include top 3 results in fallback (not all 5)
    for result in results[:3]:
        metadata = result.get("metadata", {})
        title = metadata.get("title", "Unknown")
        original_module = metadata.get("module", "Course Material")
        
        # Extract a better module name from the title
        module = _extract_module_from_title(title, original_module)
        
        top_results.append({
            "title": title,
            "url": metadata.get("live_lms_url", f"bb:{metadata.get('bb_doc_id', 'N/A')}"),
            "module": module,
            "relevance_explanation": f"This material covers concepts related to {query}",
        })
    
    # Extract unique modules for related topics (exclude generic ones)
    modules = list(set(
        r.get("module") for r in top_results 
        if r.get("module") and r.get("module") not in ["Course Materials", "Course Content", "Lab Materials", "Tutorials"]
    ))
    
    related_topics = [
        {"title": f"More about {module}", "why_explore": f"Explore additional {module} materials"}
        for module in modules[:2]
    ]
    
    # Determine answer based on scope
    if not is_in_scope:
        answer = "That topic is outside the scope of COMP237 (Introduction to Artificial Intelligence). However, I found some related course materials that might be helpful."
    elif len(top_results) == 0:
        answer = "I couldn't find specific course materials for that question. Try asking about AI concepts, machine learning algorithms, or course assignments."
    else:
        answer = f"I found {len(top_results)} relevant course materials. Check them out below!"
    
    return {
        "answer": answer,
        "is_in_scope": is_in_scope,
        "top_results": top_results,
        "related_topics": related_topics,
        "external_resources": external_resources if is_in_scope else []  # Only include if in scope
    }


if __name__ == "__main__":
    # Test the agent
    print("Testing Formatting Agent\n")
    
    # Mock enriched results
    test_state = {
        "query": "neural networks",
        "parsed_query": {
            "expanded_query": "neural networks machine learning deep learning",
            "category": "machine learning",
            "search_terms": ["neural", "networks", "backpropagation"],
            "student_goal": "learn_concept"
        },
        "enriched_results": [
            {
                "content": "Neural networks are computational models...",
                "metadata": {
                    "bb_doc_id": "_123456_1",
                    "title": "Introduction to Neural Networks",
                    "module": "Module 3: Machine Learning",
                    "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/file/_123456_1"
                },
                "score": 0.89,
                "graph_context": {
                    "module": "Module 3: Machine Learning",
                    "prerequisites": [{"title": "Linear Algebra Basics", "id": "_123455_1"}],
                    "next_steps": [{"title": "Backpropagation Algorithm", "id": "_123457_1"}],
                    "related_topics": []
                }
            },
            {
                "content": "Backpropagation is the key training algorithm...",
                "metadata": {
                    "bb_doc_id": "_123457_1",
                    "title": "Backpropagation Algorithm",
                    "module": "Module 3: Machine Learning",
                    "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/file/_123457_1"
                },
                "score": 0.85,
                "graph_context": {
                    "module": "Module 3: Machine Learning",
                    "prerequisites": [{"title": "Introduction to Neural Networks", "id": "_123456_1"}],
                    "next_steps": [],
                    "related_topics": []
                }
            }
        ]
    }
    
    result = formatting_agent(test_state)
    
    formatted = result["formatted_response"]
    
    print("\n" + "="*60)
    print("FORMATTED RESPONSE")
    print("="*60)
    print(json.dumps(formatted, indent=2))
