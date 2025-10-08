"""
Educate Mode LangGraph Workflow for Luminate AI.

This StateGraph implements an intelligent tutoring system with:
1. Math Translation (for formula queries)
2. Pedagogical Planning (choose teaching strategy)
3. Interactive Response Generation (hints, quizzes, worked examples)
4. Retrieval (fallback course content)
5. Context enrichment
6. Interactive formatting

Flow: query → math_translate → pedagogical_plan → retrieve → context → interactive_format
"""

from typing import TypedDict, Any, Dict, List
from langgraph.graph import StateGraph, END
from agents.math_translation_agent import explain_formula
from agents.retrieval import retrieval_agent
from agents.context import context_agent
from agents.query_understanding import query_understanding_agent
from agents.pedagogical_planner import pedagogical_planner_agent
from agents.student_model import student_model_agent
from agents.quiz_generator import quiz_generator_agent
from agents.study_planner import study_planner_agent


class EducateState(TypedDict, total=False):
    query: str
    chroma_db: Any
    math_markdown: str
    parsed_query: Dict[str, Any]
    retrieved_chunks: List[Dict]
    enriched_results: List[Dict]
    teaching_strategy: str
    interaction_prompts: Dict[str, Any]
    student_context: Dict[str, Any]
    student_insights: Dict[str, Any]  # From student_model_agent
    quiz_data: Dict[str, Any]  # From quiz_generator_agent
    study_plan: Dict[str, Any]  # From study_planner_agent
    detected_misconception: str  # Detected misconceptions
    formatted_response: Dict[str, Any]


def _math_translate_node(state: EducateState) -> EducateState:
    """Attempt math translation first. If found, set formatted_response and END."""
    query = state.get('query', '')
    md = explain_formula(query)
    if md:
        # Place the markdown into formatted_response.answer for downstream UI
        state['formatted_response'] = {
            'mode': 'educate',
            'answer_markdown': md,
            'is_in_scope': True,
        }
        # Short-circuit the graph by returning state; formatting node will still run
        return state

    # No math translation found; continue to retrieval
    return state


def _generate_visualization_node(state: EducateState) -> EducateState:
    """
    Placeholder for future visualization generation.
    Currently a pass-through node that preserves state.
    """
    # Future: Add visualization generation for concepts like K-means clustering
    # For now, just pass through the state
    return state


def _route_after_retrieval(state: EducateState) -> str:
    """
    Route to appropriate agent based on query intent:
    - Quiz request → quiz_generator
    - Study planning → study_planner
    - Teaching → pedagogical_plan (already handled)
    """
    query = state.get('query', '').lower()
    
    # Check for quiz intent (assessment)
    if any(keyword in query for keyword in ['quiz', 'test me', 'assess', 'check my understanding', 'practice questions']):
        return 'quiz_generator'
    
    # Check for study planning intent (scheduling and organization)
    study_keywords = [
        'study plan', 'create a plan', 'plan my', 'plan for',
        'schedule my', 'study schedule', 'organize my study',
        'what should i study', 'exam prep', 'prepare for exam',
        'plan this week', 'plan next week', 'weekly plan',
        'help me prepare', 'study strategy'
    ]
    if any(keyword in query for keyword in study_keywords):
        return 'study_planner'
    
    # Default: continue to interactive formatting (teaching)
    return 'add_context'


def build_educate_graph():
    graph = StateGraph(EducateState)

    # Add all nodes
    graph.add_node('understand_query', query_understanding_agent)
    graph.add_node('student_model', student_model_agent)  # Track student understanding
    graph.add_node('math_translate', _math_translate_node)
    graph.add_node('pedagogical_plan', pedagogical_planner_agent)
    graph.add_node('retrieve', retrieval_agent)
    graph.add_node('add_context', context_agent)
    graph.add_node('quiz_generator', quiz_generator_agent)  # Generate adaptive quizzes
    graph.add_node('study_planner', study_planner_agent)  # Create study plans
    
    # Import interactive formatter here to avoid circular imports
    from agents.interactive_formatting import interactive_formatting_agent
    graph.add_node('interactive_format', interactive_formatting_agent)

    # Start with understanding to populate parsed_query used by retrieval
    graph.set_entry_point('understand_query')

    # Enhanced Flow with student modeling and intelligent routing:
    # 1. Understand query
    # 2. Update student model (track progress)
    # 3. Math translation (if applicable)
    # 4. Pedagogical planning (choose teaching strategy)
    # 5. Generate visualization (if applicable)
    # 6. Retrieve course content
    # 7. Route based on intent:
    #    - Quiz → quiz_generator → interactive_format
    #    - Study plan → study_planner → interactive_format
    #    - Teaching → add_context → interactive_format
    
    graph.add_edge('understand_query', 'student_model')
    graph.add_edge('student_model', 'math_translate')
    graph.add_edge('math_translate', 'pedagogical_plan')
    graph.add_node('generate_visualization', _generate_visualization_node)
    graph.add_edge('pedagogical_plan', 'generate_visualization')
    graph.add_edge('generate_visualization', 'retrieve')
    
    # Conditional routing after retrieval
    graph.add_conditional_edges(
        'retrieve',
        _route_after_retrieval,
        {
            'quiz_generator': 'quiz_generator',
            'study_planner': 'study_planner',
            'add_context': 'add_context'
        }
    )
    
    # All paths converge at interactive_format
    graph.add_edge('quiz_generator', 'interactive_format')
    graph.add_edge('study_planner', 'interactive_format')
    graph.add_edge('add_context', 'interactive_format')
    graph.add_edge('interactive_format', END)

    return graph.compile()


def query_educate_mode(query: str, chroma_db: Any = None, student_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run Educate mode with interactive pedagogical strategies.
    
    Args:
        query: Student question
        chroma_db: ChromaDB instance for retrieval
        student_context: Student profile (struggling topics, mastery level, history)
        
    Returns:
        Interactive response with teaching strategy and prompts
    """
    educate_graph = build_educate_graph()
    
    # Initialize with student context
    if student_context is None:
        student_context = {
            'struggling_topics': [],
            'mastery_level': 'beginner',
            'session_count': 0
        }
    
    initial_state = {
        'query': query,
        'chroma_db': chroma_db,
        'student_context': student_context
    }
    
    final_state = educate_graph.invoke(initial_state)

    return {
        'formatted_response': final_state.get('formatted_response', {}),
        'teaching_strategy': final_state.get('teaching_strategy'),
        'metadata': {
            'original_query': query,
            'parsed_query': final_state.get('parsed_query', {}),
            'total_results': len(final_state.get('retrieved_chunks', [])),
            'interaction_type': final_state.get('formatted_response', {}).get('interaction_type')
        }
    }


if __name__ == '__main__':
    print('Educate graph test - run from main app')
