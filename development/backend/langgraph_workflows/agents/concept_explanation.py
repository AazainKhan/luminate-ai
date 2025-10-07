"""
Concept Explanation Agent for Educate Mode

Purpose: Provide clear, structured concept explanations
Uses: Google Gemini 1.5 Pro (deeper reasoning)
"""

from typing import Dict, Any, List
from llm_config import get_llm


def concept_explanation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate clear concept explanation with examples.
    
    Structure:
    1. Simple definition (1-2 sentences)
    2. Why it matters (real-world context)
    3. Key components or steps
    4. Example from course materials
    5. Common misconceptions to avoid
    
    Args:
        state: Workflow state with query and retrieved_context
        
    Returns:
        Updated state with 'explanation'
    """
    query = state.get("query", "")
    parsed_query = state.get("parsed_query", {})
    retrieved_context = state.get("retrieved_context", [])
    
    # Build context from retrieved chunks
    context_text = "\n\n".join([
        f"Source: {chunk.get('title', 'Untitled')}\n{chunk.get('text', '')[:500]}"
        for chunk in retrieved_context[:5]
    ]) if retrieved_context else "No specific course content found."
    
    # Get key concepts
    key_concepts = parsed_query.get("key_concepts", [])
    concepts_str = ", ".join(key_concepts) if key_concepts else "the topic"
    
    # Determine complexity level
    complexity = parsed_query.get("complexity_level", "intermediate")
    
    # Adjust explanation depth based on complexity
    depth_guidance = {
        "beginner": "Use simple language, avoid jargon, include basic analogies",
        "intermediate": "Use technical terms with explanations, include examples",
        "advanced": "Assume prior knowledge, focus on nuances and edge cases"
    }
    
    prompt = f"""You are an expert AI tutor for COMP237 (Artificial Intelligence course).

The student asked: "{query}"

Key concepts to explain: {concepts_str}
Student level: {complexity}

Course Content Reference:
{context_text}

Provide a comprehensive yet clear explanation following this structure:

## 📚 Definition
[1-2 sentence simple definition]

## 🎯 Why It Matters
[Real-world relevance and applications - 2-3 sentences]

## 🔑 Key Components
[Bullet points of main concepts/steps]

## 💡 Example
[Concrete example from course materials or analogous scenario]

## ⚠️ Common Misconceptions
[What students often get wrong - 2-3 points]

## 🔗 Related Concepts
[Topics to explore next]

Guidelines:
- {depth_guidance[complexity]}
- Use markdown formatting
- Be conversational and encouraging
- Reference course content when possible
- Keep it under 500 words total
- Use emojis for visual structure

Generate the explanation now:"""
    
    try:
        # Use Gemini 1.5 Pro for deeper reasoning
        llm = get_llm(
            temperature=0.4,  # Moderate creativity
            model="gemini-1.5-pro"
        )
        
        response = llm.invoke(prompt)
        explanation = response.content if hasattr(response, 'content') else str(response)
        
        print(f"📖 Generated concept explanation ({len(explanation)} chars)")
        
        return {
            **state,
            "explanation": explanation,
            "response_type": "concept"
        }
        
    except Exception as e:
        print(f"⚠️  Concept explanation error: {e}")
        
        # Fallback explanation
        fallback = f"""# {concepts_str.title()}

I'm having trouble generating a detailed explanation right now, but here's what I found in the course materials:

{context_text[:500]}

**What to explore next:**
- Review the source materials above
- Ask me specific questions about any part you don't understand
- Try breaking down the concept into smaller pieces

I'm here to help! Feel free to ask follow-up questions."""
        
        return {
            **state,
            "explanation": fallback,
            "response_type": "concept",
            "error": str(e)
        }


def problem_solving_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guide student through problem-solving with scaffolding.
    
    Scaffolding Levels:
    - Light: General guidance
    - Medium: Specific hints
    - Full: Complete solution
    
    Args:
        state: Workflow state
        
    Returns:
        Updated state with hints at multiple levels
    """
    query = state.get("query", "")
    parsed_query = state.get("parsed_query", {})
    retrieved_context = state.get("retrieved_context", [])
    
    # Build context
    context_text = "\n\n".join([
        f"**{chunk.get('title', 'Untitled')}**\n{chunk.get('text', '')[:400]}"
        for chunk in retrieved_context[:3]
    ]) if retrieved_context else "No specific course content found."
    
    prompt = f"""You are a problem-solving tutor using scaffolded learning.

Student Problem: "{query}"

Course Context:
{context_text}

Provide hints at THREE levels using scaffolding pedagogy (Wood et al., 1976):

1. **Light Hint**: Give general guidance without revealing the solution. Help student think about the problem.

2. **Medium Hint**: Point to specific concepts, algorithms, or steps. Give more direction but still require student thinking.

3. **Full Solution**: Complete worked example with:
   - Step-by-step breakdown
   - Explanation of each step
   - Code example (if applicable)
   - Why this approach works

Respond with ONLY valid JSON (no markdown, no backticks):
{{
  "light_hint": "General guidance here...",
  "medium_hint": "More specific direction here...",
  "full_solution": {{
    "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "explanation": "Detailed explanation...",
    "code_example": "// Code if applicable",
    "key_insights": ["Insight 1", "Insight 2"]
  }},
  "current_hint_level": "light",
  "recommended_approach": "Brief statement of best approach"
}}"""
    
    try:
        llm = get_llm(
            temperature=0.3,
            model="gemini-1.5-pro"
        )
        
        import json
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean response
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join([
                line for line in lines 
                if not line.strip().startswith("```")
            ])
        
        hints = json.loads(response_text)
        
        print(f"💡 Generated scaffolded hints (3 levels)")
        
        return {
            **state,
            "hints": hints,
            "explanation": hints.get("light_hint", ""),  # Start with light hint
            "response_type": "problem"
        }
        
    except Exception as e:
        print(f"⚠️  Problem solving error: {e}")
        
        fallback_hints = {
            "light_hint": f"Think about the key concepts involved in: {query}. What steps would you take to approach this?",
            "medium_hint": "Consider the algorithms and data structures from the course materials above. Which ones might apply?",
            "full_solution": {
                "steps": ["Review relevant course materials", "Break down the problem", "Apply learned concepts"],
                "explanation": "Review the context above and try to identify the approach.",
                "code_example": "# Solution would go here",
                "key_insights": ["Practice problem-solving step by step"]
            },
            "current_hint_level": "light",
            "recommended_approach": "Break the problem into smaller parts"
        }
        
        return {
            **state,
            "hints": fallback_hints,
            "explanation": fallback_hints["light_hint"],
            "response_type": "problem",
            "error": str(e)
        }
