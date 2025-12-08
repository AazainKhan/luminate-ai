"""
LangGraph Agent - 4-node architecture

Pipeline: Planner (with policy checks) → Router → [Tutor|Math|Reject] → Evaluator → End

Planner enforces 3 Laws (Scope, Integrity, Mastery) via regex + RAG checks before classification.
Includes proper Langfuse v3 tracing with nested spans and generations.
"""

import logging
import json
import uuid
import time
from typing import Dict, Any, Optional, AsyncGenerator, List

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage

from app.agent.state import AgentState, create_initial_state
from app.agent.schemas import TaskType, Source
from app.agent.nodes import planner_node, tutor_node, math_node, reject_node, evaluator_node
from app.observability import get_langfuse_client, flush_langfuse
from langfuse import propagate_attributes

logger = logging.getLogger(__name__)


# =============================================================================
# Router Logic
# =============================================================================

def route_from_plan(state: AgentState) -> str:
    """
    Route to appropriate node based on plan.
    
    Routes:
    - explain, code → tutor (with scaffolding)
    - solve → math (with scaffolding)
    - reject → reject
    
    NOTE: No "quick" route - all questions get scaffolded teaching.
    """
    plan = state.get("plan", {})
    subtasks = plan.get("subtasks", [])
    
    if not subtasks:
        return "reject"
    
    task = subtasks[0].get("task", "explain")
    
    if task in [TaskType.SOLVE.value, "solve"]:
        return "math"
    elif task in [TaskType.REJECT.value, "reject"]:
        return "reject"
    else:
        # explain, code all go to tutor with scaffolding
        return "tutor"


# =============================================================================
# Graph Builder
# =============================================================================

def create_agent() -> StateGraph:
    """Create the LangGraph agent.
    
    Architecture:
        START → planner → router → [tutor|math|reject] → evaluator → END
        
    The Planner node handles both policy checks and query classification.
    """
    # Build graph
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("planner", planner_node)
    builder.add_node("tutor", tutor_node)
    builder.add_node("math", math_node)
    builder.add_node("reject", reject_node)
    builder.add_node("evaluator", evaluator_node)
    
    # Add edges
    builder.add_edge(START, "planner")
    
    # Conditional routing after planner
    builder.add_conditional_edges(
        "planner",
        route_from_plan,
        {
            "tutor": "tutor",
            "math": "math",
            "reject": "reject",
        }
    )
    
    # All agent nodes go to evaluator
    builder.add_edge("tutor", "evaluator")
    builder.add_edge("math", "evaluator")
    builder.add_edge("reject", "evaluator")
    
    # Evaluator goes to END
    builder.add_edge("evaluator", END)
    
    return builder.compile()


# =============================================================================
# Agent Execution
# =============================================================================

# Singleton agent instance
_agent = None


def get_agent():
    """Get or create the singleton agent"""
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def run_agent(
    query: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    session_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    conversation_history: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    """
    Run the agent synchronously with proper Langfuse v3 tracing.
    
    Uses context managers for automatic span lifecycle management.
    
    Args:
        query: User's question
        user_id: User ID for personalization
        user_email: User email
        session_id: Session ID for Langfuse
        chat_id: Chat ID for persistence
        conversation_history: Previous messages
        
    Returns:
        Dict with response, sources, metadata
    """
    agent = get_agent()
    
    # Create initial state
    state = create_initial_state(
        query=query,
        user_id=user_id,
        user_email=user_email,
        conversation_history=conversation_history,
        session_id=session_id,
        chat_id=chat_id,
    )
    
    # Add query as message
    state["messages"] = [HumanMessage(content=query)]
    
    # Get Langfuse client
    langfuse = get_langfuse_client()
    trace_id = None
    
    try:
        if langfuse:
            # Create root span with context manager for proper lifecycle
            with langfuse.start_as_current_span(name="agent_execution") as root_span:
                # Propagate trace attributes to all child observations
                with propagate_attributes(
                    user_id=user_id,
                    session_id=session_id,
                    metadata={
                        "query": str(query[:100]) if query else "",
                        "chat_id": str(chat_id) if chat_id else "none",
                        "agent_architecture": "4-node-langgraph"
                    },
                    tags=["tutor-agent", "comp237"]
                ):
                    trace_id = root_span.trace_id
                    state["trace_id"] = trace_id
                    
                    # Run agent
                    result = agent.invoke(state)
                    
                    # Update root span with final output
                    root_span.update(
                        input={"query": query},
                        output={
                            "response_preview": result.get("response", "")[:200],
                            "intent": _extract_intent(result),
                            "escalation_level": result.get("escalation_level", 1),
                            "approved": result.get("approved", True)
                        }
                    )
        else:
            # No Langfuse - run without tracing
            result = agent.invoke(state)
        
        # Extract intent from plan
        intent = _extract_intent(result)
        
        return {
            "response": result.get("response", ""),
            "sources": result.get("sources", []),
            "intent": intent,
            "escalation_level": result.get("escalation_level", 1),
            "rag_metadata": result.get("rag_metadata", {}),
            "routing_info": result.get("routing_info", {}),
            "evaluation": result.get("evaluation", {}),
            "governor_checks": result.get("governor_checks", {}),
            "approved": result.get("approved", True),
            "rejection_reason": result.get("rejection_reason"),
            "trace_id": trace_id,
            "error": result.get("error"),
        }
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "response": "I encountered an error. Please try again.",
            "error": str(e),
            "trace_id": trace_id,
        }
    finally:
        flush_langfuse()


def _extract_intent(result: Dict[str, Any]) -> str:
    """Extract intent from agent result"""
    plan = result.get("plan") or {}
    subtasks = plan.get("subtasks", [])
    intent = subtasks[0].get("task", "explain") if subtasks else "explain"
    
    # If rejected, use rejection reason as intent
    if not result.get("approved", True):
        intent = result.get("rejection_reason", "reject")
    
    return intent


async def astream_agent(
    query: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    session_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    conversation_history: Optional[List[dict]] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream agent execution with AI SDK v5 compatible events.
    
    Uses Langfuse v3 with proper context propagation for nested spans.
    Child spans from nodes automatically nest under the root span via
    OpenTelemetry context propagation when using propagate_attributes.
    
    Yields events in format:
    - {"type": "queue-init", "queue": [...]}
    - {"type": "queue-update", "queueItemId": "...", "status": "..."}
    - {"type": "thinking", "step": "...", "status": "...", "result": {...}, "message": "..."}
    - {"type": "sources", "sources": [...]}
    - {"type": "text-delta", "textDelta": "..."}
    - {"type": "trace-id", "traceId": "..."}
    - {"type": "evaluation", "evaluation": {...}}
    - {"type": "finish", "chatId": "...", "traceId": "..."}
    """
    agent = get_agent()
    
    # Create initial state
    state = create_initial_state(
        query=query,
        user_id=user_id,
        user_email=user_email,
        conversation_history=conversation_history,
        session_id=session_id,
        chat_id=chat_id,
    )
    state["messages"] = [HumanMessage(content=query)]
    
    # Get Langfuse client
    langfuse = get_langfuse_client()
    trace_id = None
    root_span = None
    root_span_ctx = None

    # Create root span and trace with proper context manager pattern
    if langfuse:
        try:
            # Start root span with trace name set upfront
            root_span_ctx = langfuse.start_as_current_observation(
                name="agent_stream",
                as_type="span",
                input={"query": query, "chat_id": chat_id},
                metadata={"agent_architecture": "4-node-langgraph", "streaming": True}
            )
            root_span = root_span_ctx.__enter__()
            
            # CRITICAL: Set trace name immediately and propagate user context
            # This ensures child spans inherit the correct trace name
            root_span.update_trace(
                name=f"Chat: {query[:60]}...",
                user_id=user_id,
                session_id=session_id,
                input={"query": query, "chat_id": chat_id},
                tags=["tutor-agent", "comp237", "streaming"],
                metadata={"streaming": True}
            )
            
            trace_id = root_span.trace_id
            state["trace_id"] = trace_id
            state["parent_span_id"] = root_span.id
            logger.info(f"[Stream] Created trace: {trace_id} ('{query[:40]}...'), root span: {root_span.id}")
            
        except Exception as e:
            logger.error(f"Failed to create root trace: {e}")
            root_span_ctx = None
            root_span = None
    
    # Emit trace ID early
    if trace_id:
        yield {"type": "trace-id", "traceId": trace_id}
    
    # NOTE: Removed queue-init/queue-update events - now using only 'thinking' events
    # The frontend thinkingTrace component provides a cleaner, more structured UI
    # that shows: scope_check → escalation → classification → rag_retrieval → strategy
    
    evaluation_result = None
    
    async def process_events():
        """Process agent stream events and yield formatted results."""
        nonlocal evaluation_result
        
        async for event in agent.astream_events(state, version="v2"):
            event_type = event.get("event")
            
            if event_type == "on_chain_start":
                name = event.get("name", "")
                if name == "planner":
                    # Scope check starts
                    yield {
                        "type": "thinking",
                        "step": "scope_check",
                        "status": "processing",
                        "message": "Checking if question is within COMP237 scope..."
                    }
                elif name in ["tutor", "math"]:
                    yield {
                        "type": "thinking",
                        "step": "strategy",
                        "status": "processing",
                        "message": "Selecting teaching strategy..."
                    }
                # reject and evaluator don't need explicit start events
            
            elif event_type == "on_chain_end":
                name = event.get("name", "")
                if name == "planner":
                    output = event.get("data", {}).get("output", {})
                    
                    # Emit thinking events for planner decisions
                    routing_info = output.get("routing_info", {})
                    escalation_level = output.get("escalation_level", 1)
                    is_stuck = output.get("is_stuck", False)
                    
                    # Scope check result
                    if output.get("approved", True):
                        yield {
                            "type": "thinking",
                            "step": "scope_check",
                            "status": "completed",
                            "result": {"in_scope": True},
                            "message": "✓ Question is within COMP237 scope"
                        }
                    else:
                        yield {
                            "type": "thinking",
                            "step": "scope_check",
                            "status": "completed",
                            "result": {"in_scope": False, "reason": output.get("rejection_reason")},
                            "message": f"✗ Out of scope: {output.get('rejection_reason', 'off-topic')}"
                        }
                    
                    # Escalation decision
                    yield {
                        "type": "thinking",
                        "step": "escalation",
                        "status": "completed",
                        "result": {"level": escalation_level, "is_stuck": is_stuck},
                        "message": f"Scaffolding level {escalation_level}" + (" (student needs more help)" if is_stuck else "")
                    }
                    
                    # Classification result
                    task = routing_info.get("task", "explain")
                    yield {
                        "type": "thinking",
                        "step": "classification",
                        "status": "completed",
                        "result": {"task": task, "method": routing_info.get("method", "unknown")},
                        "message": f"Task type: {task}"
                    }
                    
                    if not output.get("approved", True):
                        yield {
                            "type": "policy-rejection",
                            "reason": output.get("rejection_reason", "policy"),
                            "routing_info": routing_info,
                        }
                    else:
                        yield {
                            "type": "thinking",
                            "step": "rag_retrieval",
                            "status": "processing",
                            "message": "Searching course materials..."
                        }
                        if routing_info:
                            yield {
                                "type": "routing",
                                "intent": task,
                                "method": routing_info.get("method", "unknown"),
                                "escalation_level": escalation_level
                            }
                
                elif name in ["tutor", "math", "reject"]:
                    output = event.get("data", {}).get("output", {})
                    sources = output.get("sources", [])
                    reasoning = output.get("reasoning", "")
                    
                    # RAG results
                    if sources:
                        yield {
                            "type": "thinking",
                            "step": "rag_retrieval",
                            "status": "completed",
                            "result": {"docs_found": len(sources)},
                            "message": f"Found {len(sources)} relevant course materials"
                        }
                        yield {"type": "sources", "sources": sources}
                    else:
                        yield {
                            "type": "thinking",
                            "step": "rag_retrieval",
                            "status": "completed",
                            "result": {"docs_found": 0},
                            "message": "No specific course materials found"
                        }
                    
                    # Strategy selected (final thinking step)
                    yield {
                        "type": "thinking",
                        "step": "strategy",
                        "status": "completed",
                        "message": "Response generated with scaffolding"
                    }
                    
                    response = output.get("response", "")
                    
                    # Stream Gemini's reasoning AFTER all thinking steps complete
                    # This shows the LLM's internal thought process after planning
                    if reasoning:
                        logger.debug(f"[Stream] Streaming reasoning after thinking steps: {len(reasoning)} chars")
                        # Stream reasoning in chunks
                        reasoning_chunk_size = 100
                        for i in range(0, len(reasoning), reasoning_chunk_size):
                            chunk = reasoning[i:i + reasoning_chunk_size]
                            yield {"type": "reasoning-delta", "reasoningDelta": chunk}
                    if response:
                        # Larger chunks to preserve markdown formatting
                        chunk_size = 200
                        for i in range(0, len(response), chunk_size):
                            chunk = response[i:i + chunk_size]
                            yield {"type": "text-delta", "textDelta": chunk}
                
                elif name == "evaluator":
                    output = event.get("data", {}).get("output", {})
                    evaluation_result = output.get("evaluation", {})
                    if evaluation_result:
                        detected_concept = evaluation_result.get("detected_concept")
                        if detected_concept:
                            yield {
                                "type": "thinking",
                                "step": "concept_detection",
                                "status": "completed",
                                "result": {"concept": detected_concept},
                                "message": f"Detected concept: {detected_concept}"
                            }
                        yield {"type": "evaluation", "evaluation": evaluation_result}
    
    try:
        # Run with Langfuse context propagation for proper span nesting
        if langfuse and root_span:
            with propagate_attributes(
                user_id=user_id,
                session_id=session_id,
                metadata={"streaming": "true", "chat_id": str(chat_id) if chat_id else "none"},
            ):
                async for item in process_events():
                    yield item
        else:
            async for item in process_events():
                yield item
        
        # Update and end root span
        if root_span:
            root_span.update(
                output=json.dumps({
                    "evaluation": evaluation_result,
                    "completed": True
                }),
                metadata={"streaming_complete": True}
            )
            if root_span_ctx:
                root_span_ctx.__exit__(None, None, None)
            else:
                root_span.end()
            
            logger.info(f"[Stream] Closed trace {trace_id} successfully")
        
        yield {"type": "finish", "chatId": chat_id, "traceId": trace_id}
        
    except Exception as e:
        logger.error(f"Stream error: {e}")
        if root_span:
            root_span.update(output=json.dumps({"error": str(e)}), level="ERROR")
            if root_span_ctx:
                root_span_ctx.__exit__(None, None, None)
            else:
                root_span.end()
        yield {"type": "error", "error": str(e)}
        yield {"type": "finish", "chatId": chat_id, "traceId": trace_id}
    
    finally:
        flush_langfuse()
