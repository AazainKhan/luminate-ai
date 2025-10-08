"""
Router for the main unified query endpoint.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..main import chroma_db, navigate_workflow, logger
from ..models import UnifiedQueryRequest, UnifiedQueryResponse

# This is a placeholder for the real orchestrator logic
from langgraph.orchestrator import classify_mode, OrchestratorState
from langgraph.educate_graph import query_educate_mode

router = APIRouter()

@router.post("/api/query", response_model=UnifiedQueryResponse, tags=["Query"], summary="Unified Query Endpoint")
async def unified_query(request: UnifiedQueryRequest):
    """
    Main entry point for all user queries. Routes to Navigate or Educate mode.
    """
    start_time = datetime.now()
    logger.info(f"📨 Unified query request: '{request.query[:50]}...'" )

    try:
        # Step 1: Orchestrator classification
        orchestrator_state = OrchestratorState(
            query=request.query,
            student_id=request.student_id or "anonymous",
            session_id=request.session_id or f"session-{int(datetime.now().timestamp())}",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={}
        )
        
        result_state = classify_mode(orchestrator_state)
        mode = result_state['mode']
        confidence = result_state['confidence']
        reasoning = result_state['reasoning']
        
        logger.info(f"🎯 Orchestrator: {mode} ({confidence:.2f}) - {reasoning}")

        response_data = {}
        # Step 2: Route to appropriate pipeline
        if mode == "navigate":
            workflow_result = navigate_workflow.invoke({
                "query": request.query,
                "chroma_db": chroma_db
            })
            response_data = workflow_result.get("formatted_response", {})
        else: # educate mode
            workflow_result = query_educate_mode(request.query, chroma_db=chroma_db)
            response_data = workflow_result.get('formatted_response', {})

        return UnifiedQueryResponse(
            mode=mode,
            confidence=confidence,
            reasoning=reasoning,
            response=response_data,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"❌ Unified query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
