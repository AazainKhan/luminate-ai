"""
Formatting Agent for Educate Mode

Purpose: Structure responses for Chrome extension UI
Uses: Light LLM processing (Gemini Flash) or template-based
"""

from typing import Dict, Any, List


def educate_formatting_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format educate mode response for Chrome extension.
    
    Output Structure:
    {
        "response_type": "concept|problem|clarification|assessment|socratic",
        "main_content": "Primary response",
        "hints": {...} (for problem type),
        "socratic_questions": [...] (for socratic mode),
        "sources": [...] (from ChromaDB),
        "related_concepts": [...],
        "follow_up_suggestions": [...],
        "misconception_alert": "..." (if detected)
    }
    
    Args:
        state: Workflow state with all agent outputs
        
    Returns:
        Updated state with 'formatted_response'
    """
    response_type = state.get("response_type", "concept")
    intent = state.get("intent", "concept")
    explanation = state.get("explanation", "")
    retrieved_context = state.get("retrieved_context", [])
    parsed_query = state.get("parsed_query", {})
    
    # Extract sources from retrieved context
    sources = [
        {
            "title": chunk.get("title", "Untitled"),
            "url": chunk.get("url", ""),
            "module": chunk.get("module", ""),
            "relevance_explanation": chunk.get("relevance_explanation", "")
        }
        for chunk in retrieved_context[:5]
    ] if retrieved_context else []
    
    # Get key concepts for related topics
    key_concepts = parsed_query.get("key_concepts", [])
    
    # Build formatted response based on intent type
    formatted_response = {
        "response_type": response_type,
        "main_content": explanation,
        "sources": sources,
        "metadata": {
            "intent": intent,
            "complexity_level": parsed_query.get("complexity_level", "intermediate"),
            "key_concepts": key_concepts
        }
    }
    
    # Add hints for problem-solving
    if response_type == "problem" and "hints" in state:
        formatted_response["hints"] = state["hints"]
    
    # Add Socratic questions
    if "socratic_questions" in state:
        formatted_response["socratic_questions"] = state["socratic_questions"]
        formatted_response["learning_goal"] = state.get("learning_goal", "")
        formatted_response["encouragement"] = state.get("encouragement", "")
    
    # Add clarification data
    if "clarification_data" in state:
        clarification = state["clarification_data"]
        if clarification.get("misconception_detected"):
            formatted_response["misconception_alert"] = clarification.get("misconception_description", "")
            formatted_response["correct_understanding"] = clarification.get("correct_understanding", "")
    
    # Add assessment questions
    if "assessment_questions" in state:
        formatted_response["assessment_questions"] = state["assessment_questions"]
    
    # Generate follow-up suggestions based on intent
    follow_up_suggestions = _generate_follow_ups(intent, key_concepts)
    formatted_response["follow_up_suggestions"] = follow_up_suggestions
    
    # Generate related concepts
    related_concepts = _generate_related_concepts(key_concepts, retrieved_context)
    formatted_response["related_concepts"] = related_concepts
    
    print(f"✅ Formatted {response_type} response with {len(sources)} sources")
    
    return {
        **state,
        "formatted_response": formatted_response
    }


def _generate_follow_ups(intent: str, key_concepts: List[str]) -> List[str]:
    """Generate contextual follow-up suggestions."""
    
    concepts_str = ", ".join(key_concepts[:2]) if key_concepts else "this topic"
    
    follow_ups = {
        "concept": [
            f"Can you give a practical example of {concepts_str}?",
            f"How does {concepts_str} compare to similar concepts?",
            f"Quiz me on {concepts_str} to test my understanding"
        ],
        "problem": [
            "Can I see the next hint level?",
            "Show me a similar example problem",
            "Explain the underlying concept more deeply"
        ],
        "clarification": [
            "Can you explain the difference in more detail?",
            "Show me examples of the correct approach",
            "Are there other common misconceptions I should know?"
        ],
        "assessment": [
            "Explain the answers in more detail",
            "Give me harder questions on this topic",
            "What should I study next?"
        ]
    }
    
    return follow_ups.get(intent, follow_ups["concept"])


def _generate_related_concepts(key_concepts: List[str], retrieved_context: List[Dict]) -> List[Dict[str, str]]:
    """Generate related concept suggestions."""
    
    related = []
    
    # From key concepts
    for concept in key_concepts[:3]:
        related.append({
            "title": f"Deep dive into {concept}",
            "why_explore": f"Build stronger understanding of {concept} fundamentals"
        })
    
    # From retrieved context (get unique modules/topics)
    seen_modules = set()
    for chunk in retrieved_context[:5]:
        module = chunk.get("module", "")
        if module and module not in seen_modules:
            seen_modules.add(module)
            related.append({
                "title": f"Explore more from {module}",
                "why_explore": "Review related course materials"
            })
            if len(related) >= 5:
                break
    
    # Add general suggestions if we don't have enough
    if len(related) < 3:
        related.extend([
            {
                "title": "Review fundamental concepts",
                "why_explore": "Strengthen your foundation"
            },
            {
                "title": "Practice with similar problems",
                "why_explore": "Apply your knowledge"
            },
            {
                "title": "Explore advanced topics",
                "why_explore": "Expand your understanding"
            }
        ])
    
    return related[:5]  # Limit to 5
