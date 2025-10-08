"""
Pedagogical Planner Agent for Educate Mode

Chooses teaching strategy based on query type and student context:
- Direct explanation
- Scaffolded hints (3-tier)
- Worked example
- Quiz generation
- Socratic questioning

Based on ITS research: scaffolding, adaptive feedback, retrieval practice
"""

from typing import Dict, List, Any
import re


class TeachingStrategy:
    """Enum-like class for teaching strategies"""
    DIRECT_EXPLANATION = "direct_explanation"
    SCAFFOLDED_HINTS = "scaffolded_hints"
    WORKED_EXAMPLE = "worked_example"
    QUIZ = "quiz"
    SOCRATIC_DIALOGUE = "socratic_dialogue"
    CONCEPT_MAP = "concept_map"


def pedagogical_planner_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Choose teaching strategy based on query type and context.
    
    Args:
        state: Contains 'query', 'retrieved_chunks', 'student_context'
        
    Returns:
        Updated state with 'teaching_strategy' and 'interaction_prompts'
    """
    query = state.get('query', '').lower()
    retrieved_chunks = state.get('retrieved_chunks', [])
    student_context = state.get('student_context', {})
    
    # Detect query intent
    strategy = _detect_teaching_strategy(query, student_context)
    
    # Build interaction prompts based on strategy
    interaction = _build_interaction_prompts(strategy, query, retrieved_chunks)
    
    state['teaching_strategy'] = strategy
    state['interaction_prompts'] = interaction
    
    return state


def _detect_teaching_strategy(query: str, student_context: Dict) -> str:
    """
    Detect best teaching strategy from query patterns.
    
    Args:
        query: Student question
        student_context: Student history and performance
        
    Returns:
        Teaching strategy name
    """
    # Check for explicit quiz request
    if any(word in query for word in ['quiz', 'test me', 'practice', 'questions']):
        return TeachingStrategy.QUIZ
    
    # Check for "how" or "why" questions (Socratic)
    if query.startswith(('how ', 'why ', 'what if ', 'what is the difference')):
        return TeachingStrategy.SOCRATIC_DIALOGUE
    
    # Check for "explain" or "teach" requests with math/algorithm keywords
    if any(word in query for word in ['explain', 'teach', 'show', 'demonstrate']):
        # If it's a formula/algorithm, use worked example
        if any(word in query for word in ['algorithm', 'formula', 'equation', 'calculate', 'compute', 'implement']):
            return TeachingStrategy.WORKED_EXAMPLE
        else:
            # Otherwise, check if student struggles with topic (use hints)
            topic = _extract_topic(query)
            if student_context.get('struggling_topics', []):
                if topic in student_context['struggling_topics']:
                    return TeachingStrategy.SCAFFOLDED_HINTS
            
            return TeachingStrategy.DIRECT_EXPLANATION
    
    # Check for "relate" or "connect" requests
    if any(word in query for word in ['relate', 'connect', 'difference', 'compare', 'versus']):
        return TeachingStrategy.CONCEPT_MAP
    
    # Default to direct explanation
    return TeachingStrategy.DIRECT_EXPLANATION


def _build_interaction_prompts(strategy: str, query: str, chunks: List[Dict]) -> Dict[str, Any]:
    """
    Build interactive prompts based on teaching strategy.
    
    Args:
        strategy: Selected teaching strategy
        query: Original query
        chunks: Retrieved course content
        
    Returns:
        Interaction structure with prompts, questions, hints, etc.
    """
    if strategy == TeachingStrategy.SCAFFOLDED_HINTS:
        return _build_hint_sequence(query, chunks)
    
    elif strategy == TeachingStrategy.QUIZ:
        return _build_quiz(query, chunks)
    
    elif strategy == TeachingStrategy.WORKED_EXAMPLE:
        return _build_worked_example(query, chunks)
    
    elif strategy == TeachingStrategy.SOCRATIC_DIALOGUE:
        return _build_socratic_questions(query, chunks)
    
    elif strategy == TeachingStrategy.CONCEPT_MAP:
        return _build_concept_map(query, chunks)
    
    else:  # DIRECT_EXPLANATION
        return _build_direct_explanation(query, chunks)


def _build_hint_sequence(query: str, chunks: List[Dict]) -> Dict[str, Any]:
    """Build 3-tier hint sequence for scaffolded learning"""
    topic = _extract_topic(query)
    
    return {
        'type': 'scaffolded_hints',
        'intro': f"Let's work through **{topic}** step by step. I'll give you hints if you need them!",
        'initial_question': f"What do you think is the main purpose of {topic}?",
        'hints': [
            {
                'level': 1,
                'text': f"💡 **Hint 1 (Light):** Think about when you would use {topic} in a problem.",
                'prompt': "Still stuck? Click for another hint."
            },
            {
                'level': 2,
                'text': f"💡 **Hint 2 (Medium):** {topic} is often used to... [synthesize from chunks]",
                'prompt': "Need more help? Click for the full explanation."
            },
            {
                'level': 3,
                'text': "💡 **Hint 3 (Worked Example):** Here's the complete breakdown...",
                'prompt': None
            }
        ],
        'follow_up': f"Now that you understand {topic}, can you think of an example where you'd apply it?"
    }


def _build_quiz(query: str, chunks: List[Dict]) -> Dict[str, Any]:
    """Build quiz questions from course content"""
    topic = _extract_topic(query)
    
    return {
        'type': 'quiz',
        'intro': f"📝 **Quiz Time!** Let's test your understanding of {topic}.",
        'instructions': "I'll ask you questions one at a time. Answer each before moving to the next.",
        'questions': [
            {
                'id': 1,
                'text': f"What is the main concept behind {topic}?",
                'type': 'open',
                'follow_up_correct': "Great! Let's go deeper...",
                'follow_up_incorrect': "Not quite. Let me explain..."
            },
            {
                'id': 2,
                'text': f"Can you identify an example of {topic} from the course materials?",
                'type': 'open',
                'follow_up_correct': "Excellent application!",
                'follow_up_incorrect': "Let's review the examples together..."
            },
            {
                'id': 3,
                'text': f"Why is {topic} important in AI?",
                'type': 'open',
                'follow_up_correct': "Perfect! You've mastered this.",
                'follow_up_incorrect': "Good try. Here's why it matters..."
            }
        ],
        'summary_prompt': "Review your answers and ask if anything is unclear."
    }


def _build_worked_example(query: str, chunks: List[Dict]) -> Dict[str, Any]:
    """Build step-by-step worked example"""
    topic = _extract_topic(query)
    
    return {
        'type': 'worked_example',
        'intro': f"📐 Let's work through a **complete example** of {topic}.",
        'steps_prompt': "I'll break this down into clear steps. Follow along and ask questions anytime!",
        'structure': {
            'step_1': {
                'title': "🎯 **Step 1: Understand the Problem**",
                'content_synthesis': True  # Signal to LLM to synthesize from chunks
            },
            'step_2': {
                'title': "📊 **Step 2: Set Up the Solution**",
                'content_synthesis': True
            },
            'step_3': {
                'title': "🔧 **Step 3: Apply the Algorithm/Formula**",
                'include_code': True,
                'content_synthesis': True
            },
            'step_4': {
                'title': "✅ **Step 4: Verify the Result**",
                'content_synthesis': True
            }
        },
        'follow_up': "Now try this variation: [generate related problem]"
    }


def _build_socratic_questions(query: str, chunks: List[Dict]) -> Dict[str, Any]:
    """Build Socratic dialogue sequence"""
    topic = _extract_topic(query)
    
    return {
        'type': 'socratic_dialogue',
        'intro': f"🤔 Great question! Let's explore {topic} together through some thought-provoking questions.",
        'questions': [
            f"What do you already know about {topic}?",
            f"Why do you think {topic} works the way it does?",
            f"Can you think of a scenario where {topic} might not work?",
            f"How would you explain {topic} to someone else?"
        ],
        'synthesis_prompt': "Based on your responses, here's a complete picture..."
    }


def _build_concept_map(query: str, chunks: List[Dict]) -> Dict[str, Any]:
    """Build concept relationship map"""
    concepts = _extract_concepts(query)
    
    return {
        'type': 'concept_map',
        'intro': f"🗺️ Let's map out how these concepts connect: {', '.join(concepts)}",
        'structure': {
            'core_concepts': concepts,
            'relationships': "I'll show you how these ideas relate...",
            'prerequisites': "What you need to know first:",
            'applications': "Where you'll use this:",
            'connections': "How it fits with other AI topics:"
        },
        'visual_hint': "Think of this as a knowledge tree - some concepts build on others."
    }


def _build_direct_explanation(query: str, chunks: List[Dict]) -> Dict[str, Any]:
    """Build direct but interactive explanation"""
    topic = _extract_topic(query)
    
    return {
        'type': 'direct_explanation',
        'intro': f"Let me explain **{topic}** clearly.",
        'structure': {
            'definition': "✨ **What it is:**",
            'why_important': "🎯 **Why it matters:**",
            'how_works': "⚙️ **How it works:**",
            'example': "📚 **Example from course:**",
            'common_mistakes': "⚠️ **Watch out for:**"
        },
        'follow_up': [
            "Would you like to see an example?",
            "Want to test your understanding with a quick question?",
            "Curious about related topics?"
        ]
    }


def _extract_topic(query: str) -> str:
    """Extract main topic from query"""
    # Remove question words
    topic = re.sub(r'^(explain|what is|how does|why|teach me|show me)\s+', '', query, flags=re.IGNORECASE)
    topic = topic.strip()
    
    # Capitalize for display
    return topic.title() if topic else "this concept"


def _extract_concepts(query: str) -> List[str]:
    """Extract multiple concepts from comparison queries"""
    # Look for "vs", "and", "versus", "difference between"
    if ' vs ' in query or ' versus ' in query:
        parts = re.split(r'\s+vs\s+|\s+versus\s+', query, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]
    
    if 'difference between' in query:
        match = re.search(r'difference between (.+) and (.+)', query, re.IGNORECASE)
        if match:
            return [match.group(1).strip(), match.group(2).strip()]
    
    if 'compare' in query:
        match = re.search(r'compare (.+) and (.+)', query, re.IGNORECASE)
        if match:
            return [match.group(1).strip(), match.group(2).strip()]
    
    # Default: extract main topic
    return [_extract_topic(query)]


if __name__ == "__main__":
    # Test the pedagogical planner
    test_cases = [
        "explain week 3 dfs",
        "quiz me on neural networks",
        "how does backpropagation work",
        "show me how to implement gradient descent",
        "what's the difference between BFS and DFS",
    ]
    
    print("=" * 60)
    print("PEDAGOGICAL PLANNER TEST")
    print("=" * 60)
    
    for query in test_cases:
        print(f"\nQuery: {query}")
        state = {'query': query, 'retrieved_chunks': [], 'student_context': {}}
        result = pedagogical_planner_agent(state)
        
        print(f"Strategy: {result['teaching_strategy']}")
        print(f"Interaction Type: {result['interaction_prompts']['type']}")
        print(f"Intro: {result['interaction_prompts'].get('intro', 'N/A')[:100]}...")
