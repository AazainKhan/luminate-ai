"""
Auto Mode Router - Intelligent query routing with streaming support.
Routes queries to Navigate or Educate mode based on orchestrator decision.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import asyncio
import logging

from pydantic import BaseModel, Field

# Get logger
logger = logging.getLogger(__name__)

# Import orchestrator and workflows
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "langgraph"))

from orchestrator import classify_mode, OrchestratorState
from educate_graph import query_educate_mode

router = APIRouter()


class ConversationMessage(BaseModel):
    """Single message in conversation history."""
    role: str  # "user" or "assistant"
    content: str
    mode: Optional[str] = None  # "navigate" or "educate"
    timestamp: str


class AutoQueryRequest(BaseModel):
    """Request model for auto mode endpoint."""
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    student_id: Optional[str] = Field(default="anonymous", description="Student identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    conversation_history: List[ConversationMessage] = Field(default=[], description="Recent conversation history")
    stream: bool = Field(default=False, description="Enable streaming response")


class AutoQueryResponse(BaseModel):
    """Response model for auto mode endpoint."""
    selected_mode: str  # "navigate" or "educate"
    confidence: float  # 0-1
    reasoning: str  # Why this mode was selected
    should_confirm: bool  # Whether to ask user for confirmation
    response_data: Dict[str, Any]  # The actual response from the selected mode
    is_follow_up: bool  # Whether this was detected as a follow-up
    mode_switch_count: int  # Number of mode switches in session
    execution_time_ms: float
    timestamp: str


async def stream_auto_response(
    request: AutoQueryRequest,
    orchestrator_state: OrchestratorState,
    mode_result: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    Stream the auto response in chunks.
    
    Format:
    1. First chunk: Orchestrator decision (mode, confidence, reasoning)
    2. Subsequent chunks: Response data from selected mode
    3. Final chunk: Complete response metadata
    """
    
    # Chunk 1: Orchestrator decision
    decision_chunk = {
        "type": "orchestrator_decision",
        "selected_mode": orchestrator_state["mode"],
        "confidence": orchestrator_state["confidence"],
        "reasoning": orchestrator_state["reasoning"],
        "should_confirm": orchestrator_state["should_confirm"],
        "is_follow_up": orchestrator_state["is_follow_up"]
    }
    yield f"data: {json.dumps(decision_chunk)}\n\n"
    await asyncio.sleep(0.1)  # Small delay for smooth UX
    
    # Chunk 2: Response data
    response_chunk = {
        "type": "response_data",
        "data": mode_result
    }
    yield f"data: {json.dumps(response_chunk)}\n\n"
    await asyncio.sleep(0.05)
    
    # Chunk 3: Completion
    completion_chunk = {
        "type": "complete",
        "timestamp": datetime.now().isoformat()
    }
    yield f"data: {json.dumps(completion_chunk)}\n\n"


@router.post("/api/auto", response_model=AutoQueryResponse)
async def auto_query(req: AutoQueryRequest, request: Request):
    """
    Auto mode: Intelligently route query to Navigate or Educate mode.
    
    Process:
    1. Orchestrator analyzes query + conversation history
    2. Selects appropriate mode (Navigate or Educate)
    3. Routes to selected pipeline
    4. Returns unified response with mode metadata
    
    If stream=True, returns Server-Sent Events stream.
    """
    start_time = datetime.now()
    
    logger.info(f"🤖 Auto query: '{req.query[:50]}...'")
    
    # Get dependencies from app state
    chroma_db = request.app.state.chroma_db
    navigate_workflow = request.app.state.navigate_workflow
    
    try:
        # Convert conversation history to dict format
        conv_history = [
            {
                "role": msg.role,
                "content": msg.content,
                "mode": msg.mode or "",
                "timestamp": msg.timestamp
            }
            for msg in req.conversation_history
        ]
        
        # Generate session ID if not provided
        session_id = req.session_id or f"auto-session-{int(datetime.now().timestamp())}"
        
        # Step 1: Orchestrator classification
        orchestrator_state = OrchestratorState(
            query=req.query,
            student_id=req.student_id or "anonymous",
            session_id=session_id,
            conversation_history=conv_history,
            mode="navigate",  # Will be updated
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result_state = classify_mode(orchestrator_state)
        mode = result_state['mode']
        confidence = result_state['confidence']
        reasoning = result_state['reasoning']
        should_confirm = result_state['should_confirm']
        is_follow_up = result_state['is_follow_up']
        mode_switch_count = result_state['mode_switch_count']
        
        logger.info(f"🎯 Orchestrator: {mode.upper()} (confidence={confidence:.2f})")
        logger.info(f"   Reasoning: {reasoning}")
        logger.info(f"   Follow-up: {is_follow_up}, Switches: {mode_switch_count}")
        
        # Step 2: Route to appropriate pipeline
        response_data = {}
        
        if mode == "navigate":
            # Collect agent traces for execution plan
            agent_traces = []
            def trace_callback(trace):
                agent_traces.append(trace)
            
            workflow_result = navigate_workflow.invoke({
                "query": req.query,
                "chroma_db": chroma_db,
                "trace_callback": trace_callback
            })
            formatted_data = workflow_result.get("formatted_response", {})
            
            # Ensure proper structure for frontend
            if isinstance(formatted_data, str):
                formatted_data = {"answer": formatted_data, "brief_summary": "", "top_results": [], "related_topics": []}
            
            response_data = {
                "formatted_response": formatted_data.get("answer", formatted_data.get("encouragement", "Here are relevant materials.")),
                "brief_summary": formatted_data.get("brief_summary", ""),
                "top_results": formatted_data.get("top_results", []),
                "related_topics": formatted_data.get("related_topics", []),
                "external_resources": formatted_data.get("external_resources", []),
                "agent_traces": agent_traces,
            }
        else:  # educate mode
            workflow_result = query_educate_mode(req.query, chroma_db=chroma_db)
            formatted_data = workflow_result.get('formatted_response', {})
            
            # Ensure proper structure for frontend
            if isinstance(formatted_data, str):
                response_data = {
                    "formatted_response": formatted_data,
                    "level": "conceptual",
                    "agent_traces": []  # TODO: Add trace support to educate_graph
                }
            elif isinstance(formatted_data, dict) and formatted_data.get("answer_markdown"):
                # Math translation response
                response_data = {
                    "formatted_response": formatted_data["answer_markdown"],
                    "level": "4-level-translation",
                    "math_translation": {
                        "available": True,
                        "levels": ["intuition", "mathematical", "code", "misconceptions"]
                    },
                    "agent_traces": []  # TODO: Add trace support to educate_graph
                }
            else:
                # Interactive/pedagogical response
                response_data = {
                    "formatted_response": formatted_data.get("content", formatted_data.get("answer", "")),
                    "teaching_strategy": formatted_data.get("teaching_strategy"),
                    "interaction_type": formatted_data.get("interaction_type"),
                    "tasks": formatted_data.get("tasks", []),
                    "show_task_view": formatted_data.get("show_task_view", False),
                    "agent_traces": []  # TODO: Add trace support to educate_graph
                }
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Step 3: Handle streaming vs. regular response
        if req.stream:
            return StreamingResponse(
                stream_auto_response(req, result_state, response_data),
                media_type="text/event-stream"
            )
        
        # Regular response
        return AutoQueryResponse(
            selected_mode=mode,
            confidence=confidence,
            reasoning=reasoning,
            should_confirm=should_confirm,
            response_data=response_data,
            is_follow_up=is_follow_up,
            mode_switch_count=mode_switch_count,
            execution_time_ms=round(execution_time_ms, 2),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"❌ Auto query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/auto/feedback")
async def record_feedback(
    query: str,
    predicted_mode: str,
    actual_mode: str,
    confidence: float,
    reasoning: str = "",
    student_id: str = "anonymous",
    session_id: str = "",
    was_follow_up: bool = False
):
    """
    Record feedback when user manually switches modes.
    This helps improve the orchestrator over time.
    """
    try:
        from feedback_loop import record_mode_switch
        
        record_mode_switch(
            query=query,
            predicted_mode=predicted_mode,
            actual_mode=actual_mode,
            confidence=confidence,
            reasoning=reasoning,
            student_id=student_id,
            session_id=session_id,
            was_follow_up=was_follow_up
        )
        
        logger.info(f"📊 Feedback recorded: {predicted_mode} → {actual_mode}")
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully"
        }
    
    except Exception as e:
        logger.error(f"❌ Feedback recording error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/auto/stats")
async def get_orchestrator_stats(days: int = 7):
    """
    Get orchestrator performance statistics.
    Useful for monitoring and debugging.
    """
    try:
        from feedback_loop import get_feedback_stats
        
        stats = get_feedback_stats(days=days)
        
        return {
            "status": "success",
            "stats": stats,
            "period_days": days
        }
    
    except Exception as e:
        logger.error(f"❌ Stats retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

