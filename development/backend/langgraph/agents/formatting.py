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


FORMATTING_PROMPT = """You are a fast, precise AI assistant for COMP237 course navigation. Be concise and direct.

Student Query: "{original_query}"

Course Content:
{results_summary}

Task: Synthesize course content into a clear, direct answer.

Instructions:
1. Scope Check: Is this COMP237-related (AI, ML, search algorithms, NLP, computer vision, neural networks)?
   - IN SCOPE → Provide clear answer
   - OUT OF SCOPE → State briefly, list related materials if any

2. Brief Summary: One concise sentence (15-20 words) that directly answers the query

3. Answer Format (if IN SCOPE):
   - 3-6 sentences max
   - Use course content excerpts
   - Include key formulas/algorithms if relevant
   - Use markdown for code/math: ```python or $formula$

4. Source Materials: List 1-5 most relevant documents with brief explanation

5. Related Topics: Suggest 2-3 next topics to explore

Output JSON:
{{
  "brief_summary": "One concise sentence answering the query (15-20 words)...",
  "answer": "Clear, direct answer using markdown...",
  "is_in_scope": true/false,
  "top_results": [
    {{"title": "Doc title", "url": "URL", "module": "Week X", "relevance_explanation": "Why relevant..."}}
  ],
  "related_topics": [
    {{"title": "Topic", "why_explore": "Brief reason..."}}
  ]
}}

Keep answers concise but complete. Use bullet points for lists. Return only valid JSON."""


def formatting_agent(state: Dict) -> Dict:
    """
    Format enriched results for Chrome extension display.
    Optimized for Gemini 2.0 Flash (fast retrieval mode).
    
    Args:
        state: Contains 'enriched_results' with contextual information
        
    Returns:
        Updated state with 'formatted_response' containing structured output
    """
    enriched_results = state.get("enriched_results", [])
    external_resources = state.get("external_resources", [])  # NEW: Get external resources
    student_query = state.get("query", "")
    
    # If a math translation (markdown) was already produced by the MathTranslationAgent,
    # preserve it and do not overwrite via fallback formatting.
    existing = state.get("formatted_response")
    if isinstance(existing, dict) and existing.get("answer_markdown"):
        # Ensure external resources attached if applicable and return early
        existing.setdefault('external_resources', external_resources if existing.get('is_in_scope', True) else [])
        state["formatted_response"] = existing
        state["is_in_scope"] = existing.get("is_in_scope", True)
        return state
    
    if not enriched_results:
        # Check if query is likely in scope
        is_in_scope = _is_likely_in_scope(student_query)
        
        if is_in_scope:
            brief_summary = "No specific course materials found for this query."
            answer = "I couldn't find specific course materials for that question. Try rephrasing or asking about AI concepts, machine learning algorithms, neural networks, or course assignments."
        else:
            brief_summary = "This topic is outside COMP237 course scope."
            answer = "That topic appears to be outside the scope of COMP237 (Introduction to Artificial Intelligence). This course focuses on AI concepts, machine learning, neural networks, and intelligent agents. Please ask about topics covered in the course!"
        
        state["formatted_response"] = {
            "brief_summary": brief_summary,
            "answer": answer,
            "is_in_scope": is_in_scope,
            "top_results": [],
            "related_topics": [],
            "external_resources": external_resources if is_in_scope else []  # Only include external resources if in scope
        }
        state["is_in_scope"] = is_in_scope  # Set scope flag for downstream agents
        return state
    
    # Get LLM instance for Navigate mode (Gemini 2.0 Flash - fast)
    llm = get_llm(temperature=0.2, mode="navigate")
    
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
        Formatted string summary INCLUDING content excerpts
    """
    summary_lines = []
    
    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        graph_context = result.get("graph_context", {})
        content = result.get("content", "")
        
        title = metadata.get("title", "Unknown")
        original_module = metadata.get("module", "Unknown Module")
        
        # Extract better module name from title
        module = _extract_module_from_title(title, original_module)
        
        bb_doc_id = metadata.get("bb_doc_id", "N/A")
        url = metadata.get("live_lms_url", f"bb:{bb_doc_id}")
        
        prereqs = len(graph_context.get("prerequisites", [])) if graph_context else 0
        next_steps = len(graph_context.get("next_steps", [])) if graph_context else 0
        
        # Truncate content to first 800 characters for LLM context
        content_excerpt = content[:800] + "..." if len(content) > 800 else content
        
        summary_lines.append(
            f"{i}. {title}\n"
            f"   Module: {module}\n"
            f"   URL: {url}\n"
            f"   Has Prerequisites: {prereqs > 0}\n"
            f"   Has Next Steps: {next_steps > 0}\n"
            f"   Content Excerpt:\n   {content_excerpt}\n"
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
