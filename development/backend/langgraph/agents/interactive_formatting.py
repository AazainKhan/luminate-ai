"""
Interactive Formatting Agent for Educate Mode

Formats responses based on teaching strategy with interactive elements:
- Scaffolded hints with progressive reveal
- Quiz questions with follow-ups
- Worked examples with step-by-step breakdown
- Socratic dialogue prompts
- Concept maps
- Study plans with task visualization

Uses LLM to generate content following pedagogical structure.
"""

from typing import Dict, List, Any
import json
from llm_config import get_llm
from .task_formatter import (
    study_plan_to_tasks,
    quiz_progress_to_tasks,
    teaching_strategy_to_tasks
)


def interactive_formatting_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format educate response with interactive pedagogical elements.
    
    Args:
        state: Contains 'teaching_strategy', 'interaction_prompts', 'enriched_results', 'query'
        
    Returns:
        Updated state with 'formatted_response' containing interactive structure
    """
    # If math translation already provided, preserve it
    existing = state.get("formatted_response")
    if isinstance(existing, dict) and existing.get("answer_markdown"):
        # Add interactive follow-up
        existing["interactive"] = {
            "type": "math_translation",
            "follow_up_prompts": [
                "🧮 Want to see this formula in action with an example?",
                "💻 Would you like to see the code implementation?",
                "❓ Have questions about any of the steps?"
            ]
        }
        state["formatted_response"] = existing
        return state
    
    teaching_strategy = state.get("teaching_strategy")
    interaction_prompts = state.get("interaction_prompts", {})
    enriched_results = state.get("enriched_results", [])
    query = state.get("query", "")
    
    # Check for study plan or quiz data
    study_plan = state.get("study_plan")
    plan_type = state.get("plan_type")
    quiz_data = state.get("quiz_data")
    student_insights = state.get("student_insights")
    
    if not teaching_strategy or not interaction_prompts:
        # Fallback to simple response
        return _fallback_interactive(state)
    
    # Generate interactive response based on strategy
    if teaching_strategy == "scaffolded_hints":
        response = _format_scaffolded_hints(query, interaction_prompts, enriched_results)
    elif teaching_strategy == "quiz":
        response = _format_quiz(query, interaction_prompts, enriched_results, quiz_data, student_insights)
    elif teaching_strategy == "worked_example":
        response = _format_worked_example(query, interaction_prompts, enriched_results)
    elif teaching_strategy == "socratic_dialogue":
        response = _format_socratic(query, interaction_prompts, enriched_results)
    elif teaching_strategy == "concept_map":
        response = _format_concept_map(query, interaction_prompts, enriched_results)
    else:  # direct_explanation
        response = _format_direct_explanation(query, interaction_prompts, enriched_results)
    
    # Add task visualization if study plan exists
    if study_plan and plan_type:
        response["tasks"] = study_plan_to_tasks(study_plan, plan_type)
        response["show_task_view"] = True
    
    # Add task visualization for teaching strategies
    if teaching_strategy in ["scaffolded_hints", "worked_example", "socratic_dialogue"]:
        # Extract topic from query (simplified)
        topic = query.split()[:3] if query else ["Learning"]
        topic_str = " ".join(topic)
        response["tasks"] = teaching_strategy_to_tasks(teaching_strategy, interaction_prompts, topic_str)
    
    state["formatted_response"] = response
    return state


def _format_scaffolded_hints(query: str, prompts: Dict, results: List[Dict]) -> Dict:
    """Format scaffolded hint sequence"""
    llm = get_llm(temperature=0.3, mode="educate")  # Use Gemini 2.5 Flash for deep reasoning
    
    # Build content summary from results
    content = _extract_content_summary(results)
    
    # Optimized prompt for Gemini 2.5 Flash with structured thinking
    hint_prompt = f"""You are an expert AI tutor using Bloom's taxonomy and scaffolding pedagogy.

Student Question: "{query}"

Course Content:
{content[:2000]}

Task: Create a 3-tier scaffolded hint sequence that guides discovery without giving away the answer.

Think step-by-step:
1. Identify the core concept the student needs to grasp
2. Design hints that build on each other progressively
3. Ensure each hint provides just enough information to advance understanding

Output Format (JSON):
{{
  "intro": "Warm, encouraging intro (1 sentence)",
  "hint_1": "Light guiding question or subtle clue (2 sentences max)",
  "hint_2": "Medium hint revealing key concept but not full solution (3 sentences max)",
  "hint_3": "Complete explanation with concrete example from course materials (5 sentences max)"
}}

Guidelines:
- Hint 1: Activates prior knowledge, asks guiding questions
- Hint 2: Reveals partial concept, shows connections
- Hint 3: Full breakdown with worked example
- Use markdown formatting for code/formulas
- Keep language conversational and supportive"""
    
    try:
        response = llm.invoke(hint_prompt)
        hints_data = json.loads(_extract_json(response.content))
    except:
        # Fallback hints
        hints_data = {
            "intro": f"Let's work through this step by step!",
            "hint_1": "Think about the main purpose and when you'd use this concept.",
            "hint_2": "This concept helps solve problems by... [review course materials]",
            "hint_3": "Here's the complete explanation from your course materials."
        }
    
    intro_text = prompts.get('intro', hints_data.get('intro'))
    
    return {
        "type": "interactive",
        "interaction_type": "scaffolded_hints",
        "answer": f"## {query}\n\n{intro_text}\n\nI'll guide you through this step by step with progressive hints.",
        "content": f"## {query}\n\n{intro_text}",
        "intro": intro_text,
        "initial_question": prompts.get('initial_question', f"What do you think this concept is about?"),
        "hints": [
            {
                "level": 1,
                "revealed": False,
                "text": f"💡 **Hint 1 (Light):** {hints_data.get('hint_1', 'Think about when you would use this.')}",
                "button_text": "Show Hint 1"
            },
            {
                "level": 2,
                "revealed": False,
                "text": f"💡 **Hint 2 (Medium):** {hints_data.get('hint_2', 'Consider the key concept...')}",
                "button_text": "Show Hint 2"
            },
            {
                "level": 3,
                "revealed": False,
                "text": f"💡 **Full Explanation:** {hints_data.get('hint_3', 'Complete breakdown...')}",
                "button_text": "Show Full Answer"
            }
        ],
        "follow_up_prompts": [
            "💬 Ask a follow-up question",
            "🎯 Want to test your understanding?",
            "📚 See related course materials"
        ],
        "sources": _format_sources(results[:3])
    }


def _format_quiz(query: str, prompts: Dict, results: List[Dict], quiz_data: Dict = None, student_insights: Dict = None) -> Dict:
    """Format interactive quiz"""
    llm = get_llm(temperature=0.4)
    
    content = _extract_content_summary(results)
    
    quiz_prompt = f"""Generate 3 quiz questions about: "{query}"

Course Content:
{content[:2000]}

Create varied, thought-provoking questions:
- Mix factual recall and conceptual understanding
- Include one "why" or "how" question
- Make questions specific to the course content

Format as JSON:
{{
  "questions": [
    {{"q": "question text", "type": "open", "hint": "optional hint"}},
    ...
  ]
}}

Keep questions clear and concise."""
    
    try:
        response = llm.invoke(quiz_prompt)
        quiz_data = json.loads(_extract_json(response.content))
        questions = quiz_data.get('questions', [])
    except:
        questions = [
            {"q": f"What is the main concept behind this topic?", "type": "open"},
            {"q": f"Can you give an example from the course?", "type": "open"},
            {"q": f"Why is this important in AI?", "type": "open"}
        ]
    
    return {
        "type": "interactive",
        "interaction_type": "quiz",
        "intro": prompts.get('intro', "📝 **Quiz Time!** Let's test your understanding."),
        "instructions": "Answer each question one at a time. I'll provide feedback!",
        "questions": [
            {
                "id": i+1,
                "text": q.get('q', ''),
                "hint": q.get('hint'),
                "awaiting_response": i == 0  # First question active
            }
            for i, q in enumerate(questions[:3])
        ],
        "current_question": 1,
        "follow_up_prompts": [
            "✅ Submit your answer",
            "💡 Need a hint?",
            "📖 Review course materials"
        ],
        "sources": _format_sources(results[:3])
    }


def _format_worked_example(query: str, prompts: Dict, results: List[Dict]) -> Dict:
    """Format step-by-step worked example"""
    llm = get_llm(temperature=0.3, mode="educate")  # Gemini 2.5 Flash for structured reasoning
    
    content = _extract_content_summary(results)
    
    # Optimized prompt leveraging Gemini 2.5's step-by-step reasoning
    example_prompt = f"""You are an expert AI tutor creating a worked example for deep understanding.

Student Question: "{query}"

Course Content:
{content[:3000]}

Task: Create a comprehensive worked example with 4 clear steps.

Reasoning Process:
1. Analyze what conceptual understanding the student needs
2. Identify the best concrete example from course materials
3. Break down the solution into logical phases
4. Design a practice problem at same difficulty level

Output Format (JSON):
{{
  "steps": [
    {{
      "title": "Step 1: Understand the Problem",
      "content": "Clearly state what we're solving and why (3-4 sentences)",
      "code": null
    }},
    {{
      "title": "Step 2: Set Up the Solution",
      "content": "Define variables, constraints, approach (3-4 sentences)",
      "code": "# Setup code if applicable"
    }},
    {{
      "title": "Step 3: Apply the Algorithm/Formula",
      "content": "Execute solution step-by-step with explanations (5-6 sentences)",
      "code": "# Implementation with inline comments"
    }},
    {{
      "title": "Step 4: Verify the Result",
      "content": "Check correctness, interpret output, discuss complexity (3-4 sentences)",
      "code": "# Verification code if applicable"
    }}
  ],
  "practice_problem": "Similar problem for student to solve independently with same structure"
}}

Guidelines:
- Use markdown formatting for formulas: $x^2 + y^2$
- Include Python code blocks with ```python when relevant
- Connect each step with clear transitions
- Practice problem should test same concepts, different numbers/context"""
    
    try:
        response = llm.invoke(example_prompt)
        example_data = json.loads(_extract_json(response.content))
        steps = example_data.get('steps', [])
        practice = example_data.get('practice_problem', '')
    except:
        steps = [
            {"title": "Step 1: Understand the Problem", "content": "Let's break down what we're trying to solve..."},
            {"title": "Step 2: Set Up the Solution", "content": "Here's what we need..."},
            {"title": "Step 3: Apply the Method", "content": "Now we execute..."},
            {"title": "Step 4: Verify", "content": "Let's check our work..."}
        ]
        practice = "Try a similar problem on your own!"
    
    return {
        "type": "interactive",
        "interaction_type": "worked_example",
        "intro": prompts.get('intro', "📐 Let's work through a **complete example** step by step."),
        "steps": [
            {
                "number": i+1,
                "title": step.get('title', f"Step {i+1}"),
                "content": step.get('content', ''),
                "code": step.get('code'),
                "revealed": i == 0  # First step revealed
            }
            for i, step in enumerate(steps)
        ],
        "practice_problem": practice,
        "follow_up_prompts": [
            "📖 Show next step",
            "💬 Ask about this step",
            "🎯 Try the practice problem"
        ],
        "sources": _format_sources(results[:3])
    }


def _format_socratic(query: str, prompts: Dict, results: List[Dict]) -> Dict:
    """Format Socratic dialogue"""
    return {
        "type": "interactive",
        "interaction_type": "socratic_dialogue",
        "intro": prompts.get('intro', "🤔 Great question! Let's explore this together."),
        "questions": prompts.get('questions', [
            "What do you already know about this topic?",
            "Why do you think it works this way?",
            "Can you think of an example?"
        ]),
        "current_question_index": 0,
        "follow_up_prompts": [
            "💬 Answer this question",
            "💡 Give me a hint",
            "⏭️ Skip to explanation"
        ],
        "sources": _format_sources(results[:3])
    }


def _format_concept_map(query: str, prompts: Dict, results: List[Dict]) -> Dict:
    """Format concept relationship map"""
    llm = get_llm(temperature=0.3)
    
    content = _extract_content_summary(results)
    
    map_prompt = f"""Create a concept map for: "{query}"

Course Content:
{content[:2000]}

Identify:
- Core concepts (2-3 main ideas)
- How they relate
- Prerequisites needed
- Where they're applied

Format as JSON:
{{
  "concepts": ["concept1", "concept2"],
  "relationships": "how they connect",
  "prerequisites": ["prereq1", "prereq2"],
  "applications": ["use1", "use2"]
}}

Keep concise."""
    
    try:
        response = llm.invoke(map_prompt)
        map_data = json.loads(_extract_json(response.content))
    except:
        map_data = {
            "concepts": ["Core Concept 1", "Core Concept 2"],
            "relationships": "These concepts are related because...",
            "prerequisites": ["Foundation knowledge needed"],
            "applications": ["Where you'll use this"]
        }
    
    return {
        "type": "interactive",
        "interaction_type": "concept_map",
        "intro": "🗺️ Let's map out how these concepts connect.",
        "concepts": map_data.get('concepts', []),
        "relationships": map_data.get('relationships', ''),
        "prerequisites": map_data.get('prerequisites', []),
        "applications": map_data.get('applications', []),
        "follow_up_prompts": [
            "🔍 Explore a concept deeper",
            "📚 See course materials",
            "❓ Ask a question"
        ],
        "sources": _format_sources(results[:3])
    }


def _format_direct_explanation(query: str, prompts: Dict, results: List[Dict]) -> Dict:
    """Format interactive direct explanation"""
    llm = get_llm(temperature=0.3)
    
    content = _extract_content_summary(results)
    
    explain_prompt = f"""Explain clearly for a student: "{query}"

Course Content:
{content[:3000]}

Structure your explanation:
- What it is (definition)
- Why it matters
- How it works
- Example from course
- Common mistakes

Format as JSON:
{{
  "definition": "clear definition",
  "importance": "why it matters",
  "how_it_works": "explanation",
  "example": "concrete example",
  "common_mistakes": ["mistake1", "mistake2"]
}}

Use markdown. Be clear and educational."""
    
    try:
        response = llm.invoke(explain_prompt)
        explain_data = json.loads(_extract_json(response.content))
    except:
        explain_data = {
            "definition": "This concept refers to...",
            "importance": "It's important because...",
            "how_it_works": "It works by...",
            "example": "For example...",
            "common_mistakes": ["Watch out for..."]
        }
    
    # Build complete answer text
    answer_text = f"""## {query}

### ✨ What it is
{explain_data.get('definition', '')}

### 🎯 Why it matters
{explain_data.get('importance', '')}

### ⚙️ How it works
{explain_data.get('how_it_works', '')}

### 📚 Example
{explain_data.get('example', '')}

### ⚠️ Common Mistakes
{chr(10).join(f"- {m}" for m in explain_data.get('common_mistakes', []))}
"""
    
    return {
        "type": "interactive",
        "interaction_type": "direct_explanation",
        "answer": answer_text,
        "content": answer_text,
        "sections": [
            {"title": "✨ What it is", "content": explain_data.get('definition', '')},
            {"title": "🎯 Why it matters", "content": explain_data.get('importance', '')},
            {"title": "⚙️ How it works", "content": explain_data.get('how_it_works', '')},
            {"title": "📚 Example", "content": explain_data.get('example', '')},
            {"title": "⚠️ Common Mistakes", "content": "\n".join(f"- {m}" for m in explain_data.get('common_mistakes', []))}
        ],
        "follow_up_prompts": [
            "📝 Want to see an example problem?",
            "❓ Test your understanding with a quiz",
            "🗺️ Explore related topics"
        ],
        "sources": _format_sources(results[:3])
    }


def _fallback_interactive(state: Dict) -> Dict:
    """Simple fallback if pedagogical planning failed"""
    query = state.get("query", "")
    enriched_results = state.get("enriched_results", [])
    
    # Extract content from first result
    content_text = ""
    if enriched_results:
        first_result = enriched_results[0]
        content_text = first_result.get("content", "")[:500]
    
    # Build a proper answer from the query and content
    if content_text:
        answer_content = f"## {query}\n\n{content_text}"
    else:
        answer_content = f"## {query}\n\nI found some information related to your question. Please review the course materials below."
    
    response = {
        "type": "interactive",
        "interaction_type": "direct_explanation",
        "answer": answer_content,
        "content": answer_content,
        "sections": [
            {"title": "Overview", "content": content_text if content_text else "Review the course materials for more information."}
        ],
        "follow_up_prompts": [
            "💬 Ask a follow-up question",
            "📚 See course materials"
        ],
        "sources": _format_sources(enriched_results[:3])
    }
    
    state["formatted_response"] = response
    return state


def _extract_content_summary(results: List[Dict]) -> str:
    """Extract content text from retrieved chunks"""
    texts = []
    for r in results[:5]:
        content = r.get('content', '')
        metadata = r.get('metadata', {})
        title = metadata.get('title', 'Unknown')
        texts.append(f"[{title}]\n{content[:500]}")
    
    return "\n\n".join(texts)


def _format_sources(results: List[Dict]) -> List[Dict]:
    """Format source citations"""
    sources = []
    for r in results:
        metadata = r.get('metadata', {})
        sources.append({
            "title": metadata.get('title', 'Course Material'),
            "module": metadata.get('module', 'Unknown'),
            "url": metadata.get('live_lms_url', '')
        })
    return sources


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response"""
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()
