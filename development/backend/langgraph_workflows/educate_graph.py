"""
Educate Mode LangGraph Workflow for Luminate AI

This creates a StateGraph that orchestrates educate mode agents:
1. Intent Classification - Determine what student needs
2. Retrieval Agent - Get relevant course content
3. Branch by Intent:
   - Concept: Concept Explanation Agent
   - Problem: Problem Solving Agent (scaffolding)
   - Clarification: Clarification Agent (misconception detection)
   - Assessment: Assessment Agent (quiz generation)
4. Socratic Agent - Add guiding questions (optional)
5. Formatting Agent - Create UI-ready response

Based on educational AI research (VanLehn 2011, AutoTutor, Wood et al. 1976).
"""

from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END

# Import agents
from agents.intent_classification import intent_classification_agent
from agents.retrieval import retrieval_agent  # Reuse from navigate mode
from agents.concept_explanation import concept_explanation_agent, problem_solving_agent
from agents.socratic_dialogue import (
    socratic_dialogue_agent,
    clarification_agent,
    assessment_agent
)
from agents.educate_formatting import educate_formatting_agent


class EducateState(TypedDict, total=False):
    """State for Educate Mode workflow."""
    # Input
    query: str
    conversation_history: List[Dict]
    chroma_db: Any  # ChromaDB instance
    
    # Intent classification output
    intent: str  # concept, problem, clarification, assessment
    parsed_query: Dict[str, Any]
    original_query: str
    
    # Retrieval output
    retrieved_context: List[Dict]
    retrieval_metadata: Dict[str, Any]
    retrieval_error: str
    
    # Explanation/response outputs
    explanation: str
    hints: Dict[str, Any]  # For problem solving
    socratic_questions: List[Dict]  # Guiding questions
    learning_goal: str
    encouragement: str
    clarification_data: Dict[str, Any]  # For misconceptions
    assessment_questions: List[Dict]  # For quizzes
    
    # Response metadata
    response_type: str  # concept, problem, clarification, assessment
    
    # Final output
    formatted_response: Dict[str, Any]


def route_by_intent(state: EducateState) -> str:
    """
    Route to appropriate agent based on classified intent.
    
    Routes:
    - concept → concept_explanation
    - problem → problem_solving
    - clarification → clarification
    - assessment → assessment
    """
    intent = state.get("intent", "concept")
    
    route_map = {
        "concept": "concept_explanation",
        "problem": "problem_solving",
        "clarification": "clarification",
        "assessment": "assessment"
    }
    
    next_node = route_map.get(intent, "concept_explanation")
    print(f"🔀 Routing to: {next_node}")
    
    return next_node


def should_add_socratic(state: EducateState) -> str:
    """
    Decide if we should add Socratic questions.
    
    Add Socratic for:
    - concept (always helpful)
    - problem (if student struggles)
    - clarification (to check understanding)
    
    Skip for:
    - assessment (already has questions)
    """
    intent = state.get("intent", "concept")
    response_type = state.get("response_type", "")
    
    # Skip socratic for assessment
    if intent == "assessment" or response_type == "assessment":
        return "format_response"
    
    # Add socratic for others
    return "add_socratic"


def build_educate_graph():
    """
    Build the Educate Mode StateGraph.
    
    Workflow:
    1. Classify intent
    2. Retrieve relevant content
    3. Branch by intent to specialized agent
    4. Optionally add Socratic questions
    5. Format for UI
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph
    graph = StateGraph(EducateState)
    
    # Add nodes (agents)
    graph.add_node("classify_intent", intent_classification_agent)
    graph.add_node("retrieve", retrieval_agent)
    graph.add_node("concept_explanation", concept_explanation_agent)
    graph.add_node("problem_solving", problem_solving_agent)
    graph.add_node("clarification", clarification_agent)
    graph.add_node("assessment", assessment_agent)
    graph.add_node("add_socratic", socratic_dialogue_agent)
    graph.add_node("format_response", educate_formatting_agent)
    
    # Define workflow edges
    graph.set_entry_point("classify_intent")
    
    # After classification, retrieve context
    graph.add_edge("classify_intent", "retrieve")
    
    # After retrieval, route by intent
    graph.add_conditional_edges(
        "retrieve",
        route_by_intent,
        {
            "concept_explanation": "concept_explanation",
            "problem_solving": "problem_solving",
            "clarification": "clarification",
            "assessment": "assessment"
        }
    )
    
    # After specialized agents, decide on Socratic questions
    for node in ["concept_explanation", "problem_solving", "clarification", "assessment"]:
        graph.add_conditional_edges(
            node,
            should_add_socratic,
            {
                "add_socratic": "add_socratic",
                "format_response": "format_response"
            }
        )
    
    # After Socratic, format
    graph.add_edge("add_socratic", "format_response")
    
    # Final step
    graph.add_edge("format_response", END)
    
    return graph.compile()


def query_educate_mode(
    query: str,
    conversation_history: List[Dict] = None
) -> Dict[str, Any]:
    """
    Execute Educate Mode workflow for a student query.
    
    Args:
        query: Student's question or request
        conversation_history: Previous conversation (for context)
        
    Returns:
        Dictionary with formatted_response and metadata
    """
    # Build graph
    educate_graph = build_educate_graph()
    
    # Initialize state
    initial_state = {
        "query": query,
        "conversation_history": conversation_history or []
    }
    
    print(f"\n{'='*60}")
    print(f"🎓 EDUCATE MODE: {query}")
    print(f"{'='*60}\n")
    
    try:
        # Execute workflow
        final_state = educate_graph.invoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"✅ Educate Mode Complete")
        print(f"Intent: {final_state.get('intent', 'unknown')}")
        print(f"Response Type: {final_state.get('response_type', 'unknown')}")
        print(f"{'='*60}\n")
        
        return {
            "formatted_response": final_state.get("formatted_response", {}),
            "metadata": {
                "original_query": query,
                "intent": final_state.get("intent", ""),
                "parsed_query": final_state.get("parsed_query", {}),
                "response_type": final_state.get("response_type", ""),
                "sources_count": len(final_state.get("retrieved_context", [])),
                "has_socratic": len(final_state.get("socratic_questions", [])) > 0
            }
        }
        
    except Exception as e:
        print(f"❌ Educate Mode Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        return {
            "formatted_response": {
                "response_type": "error",
                "main_content": f"I encountered an error processing your request: {str(e)}. Please try rephrasing your question or check that the backend is running properly.",
                "sources": [],
                "related_concepts": [],
                "follow_up_suggestions": [
                    "Try asking in a different way",
                    "Check if the backend service is running",
                    "Review the query for any issues"
                ]
            },
            "metadata": {
                "error": str(e),
                "original_query": query
            }
        }


# For testing
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "What is backpropagation?",  # concept
        "How do I implement gradient descent?",  # problem
        "I'm confused about the difference between CNN and RNN",  # clarification
        "Quiz me on neural networks"  # assessment
    ]
    
    print("Testing Educate Mode Graph...")
    
    for test_query in test_queries:
        result = query_educate_mode(test_query)
        print(f"\n{'='*80}\n")
        print(f"Query: {test_query}")
        print(f"Intent: {result['metadata']['intent']}")
        print(f"Response Type: {result['metadata']['response_type']}")
        print(f"Response Preview: {result['formatted_response']['main_content'][:200]}...")
        print(f"\n{'='*80}\n")
