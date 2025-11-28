"""
Main Tutor Agent using LangGraph
Implements the Governor-Agent pattern with Supervisor routing

Architecture:
Governor → Supervisor → [Tutor|Math|Agent] → Tools → Evaluator
"""

from typing import Dict, List, Any
import logging
import time
import uuid
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, ToolMessage
import json

from app.agents.state import AgentState
from app.agents.governor import governor_node
from app.agents.supervisor import supervisor_node, Supervisor
from app.agents.evaluator import evaluator_node
from app.agents.pedagogical_tutor import pedagogical_tutor_node
from app.agents.math_agent import math_agent_node
from app.agents.tools import tutor_tools
from app.observability import create_trace, flush_langfuse, get_langfuse_handler
from app.observability.langfuse_client import (
    create_observation,
    update_observation_with_usage,
    calculate_cost,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Course Marshal, an AI tutor for COMP 237: Introduction to AI at Centennial College.
You have access to course materials via tools.
1. ALWAYS use the `retrieve_context` tool to find information before answering.
2. If asked about logistics (due dates, syllabus), use `check_syllabus`.
3. If the answer isn't in the retrieved content, say so.
4. Cite sources.
5. Be pedagogical - explain concepts clearly.
"""

def should_continue(state: AgentState) -> str:
    """
    Conditional edge function
    Determines next step based on governor approval
    """
    if not state.get("governor_approved", False):
        return "end"  # Stop if governor rejected
    return "continue"


def route_by_intent(state: AgentState) -> str:
    """
    Route to specialized agent based on detected intent
    
    Routes:
    - tutor: Pedagogical Socratic agent
    - math: Mathematical reasoning agent
    - default: General agent with tools
    """
    intent = state.get("intent", "fast")
    
    if intent == "tutor":
        return "pedagogical_tutor"
    elif intent == "math":
        return "math_agent"
    else:
        return "agent"


def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    General agent node that invokes the model with tools
    Used for: coder, syllabus_query, fast intents
    """
    supervisor = Supervisor()
    model_name = state.get("model_selected", "gemini-flash")
    model = supervisor.get_model(model_name)
    
    # Bind tools
    model_with_tools = model.bind_tools(tutor_tools)
    
    messages = state["messages"]
    
    # Ensure system prompt is present
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = model_with_tools.invoke(messages)
    
    # Update state with response for legacy compatibility
    return {
        "messages": [response],
        "response": response.content if isinstance(response.content, str) else ""
    }

def route_agent_output(state: AgentState) -> str:
    """
    Determine next step after agent execution
    """
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "evaluator"

def post_tool_processing_node(state: AgentState) -> Dict[str, Any]:
    """
    Process tool outputs and update state with retrieved context
    """
    messages = state["messages"]
    retrieved_context = state.get("retrieved_context", []) or []
    
    # Iterate backwards to find the most recent ToolMessages
    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage):
            break
            
        if msg.name == "retrieve_context":
            try:
                content = msg.content
                if isinstance(content, str):
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            retrieved_context.extend(data)
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                logger.warning(f"Error processing tool output: {e}")
    
    return {"retrieved_context": retrieved_context}

def create_tutor_agent() -> StateGraph:
    """
    Create and configure the tutor agent graph
    
    Graph Structure:
    START → governor → (approved?) → supervisor → [tutor|math|agent] → evaluator → END
                         ↓
                        END (rejected)
    
    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("governor", governor_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("pedagogical_tutor", pedagogical_tutor_node)  # NEW: Socratic scaffolding
    workflow.add_node("math_agent", math_agent_node)  # NEW: Mathematical reasoning
    workflow.add_node("agent", agent_node)  # General agent with tools
    workflow.add_node("tools", ToolNode(tutor_tools))
    workflow.add_node("post_tools", post_tool_processing_node)
    workflow.add_node("evaluator", evaluator_node)
    
    # Set entry point
    workflow.set_entry_point("governor")
    
    # Add conditional edge from governor
    workflow.add_conditional_edges(
        "governor",
        should_continue,
        {
            "continue": "supervisor",
            "end": END,
        }
    )
    
    # Route from supervisor to specialized agents based on intent
    workflow.add_conditional_edges(
        "supervisor",
        route_by_intent,
        {
            "pedagogical_tutor": "pedagogical_tutor",
            "math_agent": "math_agent",
            "agent": "agent"
        }
    )
    
    # Pedagogical tutor goes directly to evaluator (no tools needed)
    workflow.add_edge("pedagogical_tutor", "evaluator")
    
    # Math agent goes directly to evaluator (no tools needed)
    workflow.add_edge("math_agent", "evaluator")
    
    # General agent may use tools
    workflow.add_conditional_edges(
        "agent",
        route_agent_output,
        {
            "tools": "tools",
            "evaluator": "evaluator"
        }
    )
    
    # Loop back from tools to agent via post_tools
    workflow.add_edge("tools", "post_tools")
    workflow.add_edge("post_tools", "agent")
    
    # End after evaluator
    workflow.add_edge("evaluator", END)
    
    # Compile graph
    app = workflow.compile()
    
    logger.info("Tutor agent graph created successfully")
    return app


# Global agent instance
_tutor_agent = None


def get_tutor_agent() -> StateGraph:
    """Get or create tutor agent instance"""
    global _tutor_agent
    if _tutor_agent is None:
        _tutor_agent = create_tutor_agent()
    return _tutor_agent


def run_agent(query: str, user_id: str = None, user_email: str = None, session_id: str = None) -> Dict:
    """
    Run the tutor agent with comprehensive observability and rich metadata tracking
    
    Args:
        query: User query
        user_id: Optional user ID
        user_email: Optional user email
        session_id: Optional session ID
        
    Returns:
        Dictionary with response and metadata
    """

    
    agent = get_tutor_agent()
    execution_start = time.time()
    request_id = str(uuid.uuid4())
    
    # Get Langfuse handler
    langfuse_handler = get_langfuse_handler()
    callbacks = [langfuse_handler] if langfuse_handler else []
    
    # Create comprehensive trace with rich metadata
    span = create_trace(
        name="tutor_agent_execution",
        user_id=user_id,
        session_id=session_id,
        environment="development",  # TODO: get from settings
        version="1.0.0",
        tags=["tutor-agent", "comp237", "educational-ai"],
        metadata={
            "query_length": len(query),
            "query_type": "student_question",  # Could be enhanced with classification
            "user_email": user_email,
            "user_role": "student",  # Could be determined from email domain
            "request_id": request_id,
            "client_type": "chrome_extension",
            "course_context": "COMP237_AI_Fundamentals"
        },
        input_data={
            "query": query,
            "user_context": {
                "user_id": user_id,
                "email": user_email,
                "role": "student"
            }
        }
    )
    
    # Use OpenTelemetry context to link LangChain execution to the span
    from opentelemetry import trace
    
    # Initialize state with all required fields including new pedagogical state
    initial_state: AgentState = {
        # User input
        "messages": [HumanMessage(content=query)],
        "query": query,
        
        # User context
        "user_id": user_id,
        "user_email": user_email,
        "user_role": "student",
        "trace_id": span.trace_id if span else None,
        
        # Routing decisions
        "intent": None,
        "model_selected": None,
        
        # RAG context
        "retrieved_context": [],
        "context_sources": [],
        
        # Policy enforcement
        "governor_approved": False,
        "governor_reason": None,
        
        # Pedagogical state (NEW)
        "scaffolding_level": None,
        "student_confusion_detected": False,
        "thinking_steps": None,
        "bloom_level": None,
        "pedagogical_approach": None,
        
        # Sub-agent outputs
        "syllabus_check": None,
        "math_explanation": None,
        "math_derivation": None,
        "code_suggestion": None,
        "pedagogical_strategy": None,
        
        # Final response
        "response": None,
        "response_sources": [],
        
        # Error handling
        "error": None,
    }
    
    # Run agent
    try:
        if span and hasattr(span, "_otel_span"):
            with trace.use_span(span._otel_span, end_on_exit=False):
                final_state = agent.invoke(
                    initial_state,
                    config={"callbacks": callbacks}
                )
        else:
            final_state = agent.invoke(
                initial_state,
                config={"callbacks": callbacks}
            )
        
        # Extract response from last message if not explicitly set
        response_text = final_state.get("response")
        if not response_text and final_state["messages"]:
            last_msg = final_state["messages"][-1]
            if isinstance(last_msg, BaseMessage):
                response_text = last_msg.content
        
        # Calculate execution metrics
        execution_end = time.time()
        total_execution_time = execution_end - execution_start
        
        # Prepare comprehensive output metadata
        output_metadata = {
            "response": response_text,
            "intent_classification": final_state.get("intent"),
            "model_selection": final_state.get("model_selected"),
            "policy_compliance": {
                "governor_approved": final_state.get("governor_approved"),
                "policy_violations": final_state.get("governor_reason") if not final_state.get("governor_approved") else None
            },
            "execution_metrics": {
                "total_duration_seconds": round(total_execution_time, 3),
                "processing_times_ms": final_state.get("processing_times", {}),
                "context_analysis": {
                    "input_length_chars": len(query),
                    "response_length_chars": len(response_text) if response_text else 0,
                    "context_lengths": final_state.get("context_lengths", {})
                }
            },
            "retrieval_analysis": final_state.get("retrieval_metrics", {}),
            "cost_analysis": final_state.get("cost_tracking", {}),
            "citations_count": len(final_state.get("response_sources", [])),
            "performance_tier": "fast" if total_execution_time < 5.0 else "standard"
        }
        
        # Update trace with comprehensive observability data
        if span:
            update_observation_with_usage(
                span,
                output_data=output_metadata,
                usage_details={
                    "input": final_state.get("cost_tracking", {}).get("token_usage", {}).get("input", 0),
                    "output": final_state.get("cost_tracking", {}).get("token_usage", {}).get("output", 0),
                    "total": final_state.get("cost_tracking", {}).get("token_usage", {}).get("total", 0),
                    "unit": "TOKENS"
                },
                cost_details={
                    "total_cost": final_state.get("cost_tracking", {}).get("total_cost", 0.0)
                },
                level="DEFAULT",
                latency_seconds=total_execution_time
            )
            span.end()
        
        # Flush Langfuse events
        flush_langfuse()
        
        result = {
            "response": response_text,
            "sources": final_state.get("response_sources", []),
            "intent": final_state.get("intent"),
            "model_used": final_state.get("model_selected"),
            "error": final_state.get("error"),
            # Enhanced metadata
            "execution_metrics": {
                "duration_seconds": round(total_execution_time, 3),
                "cost_usd": final_state.get("cost_tracking", {}).get("total_cost", 0.0),
                "tokens_used": final_state.get("cost_tracking", {}).get("token_usage", {}).get("total", 0),
                "performance_tier": "fast" if total_execution_time < 5.0 else "standard"
            },
            "observability": {
                "request_id": request_id,
                "trace_id": span.trace_id if span else None,
                "policy_compliant": final_state.get("governor_approved", False)
            },
            # Return messages for debugging/frontend if needed
            "messages": final_state.get("messages", [])
        }
        
        return result
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        
        # Log comprehensive error information
        execution_end = time.time()
        error_metadata = {
            "error_message": str(e),
            "error_type": type(e).__name__,
            "execution_duration": round(execution_end - execution_start, 3),
            "failed_at": "agent_execution",
            "request_id": request_id,
            "partial_state": {
                "intent_detected": initial_state.get("intent"),
                "model_selected": initial_state.get("model_selected"),
                "governor_status": initial_state.get("governor_approved")
            }
        }
        
        if span:
            update_observation_with_usage(
                span,
                output_data=error_metadata,
                level="ERROR",
                latency_seconds=execution_end - execution_start
            )
            span.end()
        
        flush_langfuse()
        
        return {
            "response": "I apologize, but I encountered an error processing your query.",
            "sources": [],
            "error": str(e),
            "execution_metrics": {
                "duration_seconds": round(execution_end - execution_start, 3),
                "cost_usd": 0.0,
                "tokens_used": 0,
                "performance_tier": "error"
            },
            "observability": {
                "request_id": request_id,
                "trace_id": span.trace_id if span else None,
                "error_type": type(e).__name__
            }
        }


async def astream_agent(query: str, user_id: str = None, user_email: str = None, session_id: str = None):
    """
    Async generator that streams agent events using astream_events (v2)
    """
    agent = get_tutor_agent()
    
    # Get Langfuse handler
    langfuse_handler = get_langfuse_handler()
    callbacks = [langfuse_handler] if langfuse_handler else []
    
    # Create Langfuse trace for observability
    span = create_trace(
        name="tutor_agent_stream",
        user_id=user_id,
        session_id=session_id,
        metadata={
            "query": query,
            "user_email": user_email,
        }
    )
    
    # Use OpenTelemetry context
    from opentelemetry import trace
    
    # Initialize state with all required fields including new pedagogical state
    initial_state: AgentState = {
        # User input
        "messages": [HumanMessage(content=query)],
        "query": query,
        
        # User context
        "user_id": user_id,
        "user_email": user_email,
        "user_role": "student",
        "trace_id": span.trace_id if span else None,
        
        # Routing decisions
        "intent": None,
        "model_selected": None,
        
        # RAG context
        "retrieved_context": [],
        "context_sources": [],
        
        # Policy enforcement
        "governor_approved": False,
        "governor_reason": None,
        
        # Pedagogical state (NEW)
        "scaffolding_level": None,
        "student_confusion_detected": False,
        "thinking_steps": None,
        "bloom_level": None,
        "pedagogical_approach": None,
        
        # Sub-agent outputs
        "syllabus_check": None,
        "math_explanation": None,
        "math_derivation": None,
        "code_suggestion": None,
        "pedagogical_strategy": None,
        
        # Final response
        "response": None,
        "response_sources": [],
        
        # Error handling
        "error": None,
    }
    
    # Stream events
    try:
        # Define the iterator
        iterator = agent.astream_events(initial_state, version="v2", config={"callbacks": callbacks})
        
        # Wrap iteration with OTel span if available
        if span and hasattr(span, "_otel_span"):
            # We need to manually manage the context for async generator if use_span doesn't work across yields
            # But for astream_events, the execution happens during iteration.
            # Let's try wrapping the whole loop.
            with trace.use_span(span._otel_span, end_on_exit=False):
                async for event in iterator:
                    yield await _process_event(event)
        else:
            async for event in iterator:
                yield await _process_event(event)
                
        if span:
            span.end()
            
    except Exception as e:
        logger.error(f"Error in stream agent: {e}")
        if span:
            span.update(output={"error": str(e)}, level="ERROR")
            span.end()
        yield {"type": "error", "error": str(e)}

async def _process_event(event):
    """Helper to process events"""
    kind = event["event"]
    
    if kind == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        if chunk.content:
            return {"type": "text-delta", "textDelta": chunk.content}
    
    elif kind == "on_tool_start":
        return {
            "type": "tool-call",
            "toolName": event["name"],
            "toolInput": event["data"].get("input")
        }
        
    elif kind == "on_tool_end":
        # Generic tool result
        result = {
            "type": "tool-result",
            "toolName": event["name"],
            "toolOutput": str(event["data"].get("output"))
        }
        
        # Special handling for sources from retrieval
        if event["name"] == "retrieve_context":
            output = event["data"].get("output")
            
            # Handle ToolMessage or other wrappers
            if hasattr(output, "artifact") and isinstance(output.artifact, list):
                output = output.artifact
            elif hasattr(output, "content"):
                try:
                    output = json.loads(output.content)
                except:
                    pass
            
            if isinstance(output, list):
                # Extract sources from retrieval output
                sources = []
                seen = set()
                for doc in output:
                    if isinstance(doc, dict):
                        # Try to get source filename from various places
                        source_file = doc.get("source_file") or doc.get("metadata", {}).get("source_file") or "Unknown"
                        page = doc.get("page") or doc.get("metadata", {}).get("page")
                        
                        # Create unique key for deduplication
                        key = f"{source_file}:{page}"
                        if key not in seen:
                            seen.add(key)
                            sources.append({
                                "source_file": source_file,
                                "page": page,
                                "content": doc.get("page_content", "")[:200] + "..."
                            })
                
                if sources:
                    result["sources"] = sources
        
        return result
        
    return {"type": "ping"} # Keepalive/ignored


