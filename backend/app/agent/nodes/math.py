"""
Math Node - Step-by-step mathematical derivations

Handles solve tasks with structured math explanations.
Uses Langfuse v3 context managers for proper trace hierarchy.
"""

import logging
import time
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from app.agent.state import AgentState
from app.agent.tools.rag import get_rag_retriever
from app.agent.prompts import MATH_PROMPT
from app.config import settings
from app.observability import get_langfuse_client

logger = logging.getLogger(__name__)


# Model pricing (same as tutor.py)
MODEL_PRICING = {
    "gemini-2.5-flash": {"input_per_1k": 0.00015, "output_per_1k": 0.0006},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> Dict[str, float]:
    """Calculate cost for model usage."""
    pricing = MODEL_PRICING.get(model, {"input_per_1k": 0, "output_per_1k": 0})
    input_cost = (input_tokens / 1000) * pricing["input_per_1k"]
    output_cost = (output_tokens / 1000) * pricing["output_per_1k"]
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost
    }


def _get_mastery_context(user_id: str) -> str:
    """Get simplified mastery context string for prompts.
    
    TODO: Implement actual mastery lookup from Supabase student_mastery table.
    For now, returns placeholder text.
    """
    if not user_id:
        return "Unknown (no user ID)"
    return "First interaction with this topic (no prior mastery data)"


def _needs_course_context(problem: str) -> bool:
    """Check if math problem needs course context from RAG.
    
    Generic math (algebra, calculus) doesn't need sources.
    Course-specific problems (ML loss functions, ANN math) do.
    """
    problem_lower = problem.lower()
    
    # Course-specific math keywords
    course_keywords = [
        "neural network", "perceptron", "activation function", "sigmoid",
        "loss function", "cross entropy", "mean squared error",
        "gradient descent", "backpropagation", "learning rate",
        "confusion matrix", "precision", "recall", "f1 score",
        "decision tree", "entropy", "information gain",
        "k-means", "clustering", "pca", "dimensionality"
    ]
    
    return any(keyword in problem_lower for keyword in course_keywords)


def math_node(state: AgentState) -> Dict[str, Any]:
    """
    Math node: generates step-by-step mathematical solutions
    
    Uses escalation levels:
    - Level 1-2: Guide without solving
    - Level 3: Partial solution
    - Level 4: Full solution
    
    Uses Langfuse v3 context managers for proper trace hierarchy.
    """
    query = state.get("query", "")
    plan = state.get("plan", {})
    subtasks = plan.get("subtasks", [])
    current_subtask = subtasks[0] if subtasks else {}
    
    payload = current_subtask.get("payload", {})
    problem = payload.get("problem", query)
    escalation_level = state.get("escalation_level", 1)
    
    logger.info(f"[Math] Problem: {problem[:50]}..., Escalation: {escalation_level}")
    
    # Get Langfuse client for tracing
    langfuse = get_langfuse_client()
    start_time = time.time()
    
    # Check if problem needs course context
    needs_context = _needs_course_context(problem)
    
    # Get relevant context with tracing (only if needed)
    if needs_context:
        try:
            retriever = get_rag_retriever()
            
            if langfuse:
                # Use context propagation from root span, not trace_context
                with langfuse.start_as_current_observation(
                    as_type="span",
                    name="rag_retrieval_math",
                    input={"query": problem, "k": 3},
                    metadata={"retriever": "chromadb", "node": "math"}
                ) as rag_span:
                    docs, rag_metadata = retriever.retrieve(problem, k=3)
                    context_str = retriever.format_context(docs)
                    sources = retriever.docs_to_sources(docs)
                    
                    rag_span.update(
                        output={
                            "docs_retrieved": len(docs),
                            "has_comp237": rag_metadata.has_comp237 if rag_metadata else False,
                        }
                    )
            else:
                docs, rag_metadata = retriever.retrieve(problem, k=3)
                context_str = retriever.format_context(docs)
                sources = retriever.docs_to_sources(docs)
                
        except Exception as e:
            logger.error(f"[Math] RAG failed: {e}")
            docs = []
            rag_metadata = None
            context_str = "No course context available."
            sources = []
    else:
        # Generic math - no course context needed
        logger.info(f"[Math] Generic math problem, skipping RAG")
        docs = []
        rag_metadata = None
        context_str = "Generic math problem - no course-specific context needed."
        sources = []
    
    # Get user_id for mastery context
    user_id = state.get("user_id", "")
    mastery_context = _get_mastery_context(user_id)
    
    # Build prompt with mastery context
    prompt = MATH_PROMPT.format(
        context=context_str,
        problem=problem,
        escalation_level=escalation_level,
        mastery_context=mastery_context,
    )
    
    # Generate response with tracing
    try:
        model_name = "gemini-2.5-flash"
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.2,  # Lower temp for math
            google_api_key=settings.google_api_key,
        )
        
        messages = [HumanMessage(content=prompt)]
        
        if langfuse:
            # Use context propagation from root span
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="math_generation",
                model=model_name,
                model_parameters={"temperature": 0.2},
                input=[{"role": "user", "content": prompt[:500] + "..." if len(prompt) > 500 else prompt}],
                metadata={
                    "escalation_level": escalation_level,
                    "problem_preview": problem[:100]
                }
            ) as generation:
                response = llm.invoke(messages)
                response_text = response.content.strip()
                
                # Calculate usage and cost
                input_tokens = response.response_metadata.get("usage_metadata", {}).get("prompt_token_count", 0)
                output_tokens = response.response_metadata.get("usage_metadata", {}).get("candidates_token_count", 0)
                cost_info = calculate_cost(model_name, input_tokens, output_tokens)
                
                generation.update(
                    output=response_text[:500] + "..." if len(response_text) > 500 else response_text,
                    usage={
                        "input": input_tokens,
                        "output": output_tokens,
                        "unit": "TOKENS"
                    },
                    usage_details={
                        "input_cost": cost_info["input_cost"],
                        "output_cost": cost_info["output_cost"],
                        "total_cost": cost_info["total_cost"]
                    }
                )
        else:
            response = llm.invoke(messages)
            response_text = response.content.strip()
        
        logger.info(f"[Math] Generated {len(response_text)} chars in {time.time() - start_time:.2f}s")
        
        # Convert rag_metadata to dict if it's a Pydantic model
        rag_meta_dict = rag_metadata.model_dump() if rag_metadata else {"docs_retrieved": 0, "retrieval_success": False}
        
        return {
            **state,
            "response": response_text,
            "sources": [s.model_dump() for s in sources],
            "retrieved_docs": docs,
            "rag_metadata": rag_meta_dict,
        }
        
    except Exception as e:
        logger.error(f"[Math] Generation failed: {e}")
        return {
            **state,
            "response": "I encountered an error while solving this problem. Please try again.",
            "error": str(e),
            "sources": [],
        }
