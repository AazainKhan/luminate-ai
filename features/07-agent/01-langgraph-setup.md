# Feature 07: LangGraph Agent Architecture - Setup

## Goal
Setup LangGraph StateGraph with AgentState TypedDict

## Tasks Completed
- [x] Define AgentState TypedDict
- [x] Create StateGraph structure
- [x] Define node flow
- [x] Add conditional edges
- [x] Compile graph

## Files Created
- `backend/app/agents/state.py` - State schema definition
- `backend/app/agents/tutor_agent.py` - Main agent graph

## State Schema
AgentState includes:
- User input (messages, query, user context)
- Routing decisions (intent, model_selected)
- RAG context (retrieved_context, context_sources)
- Policy enforcement (governor_approved, governor_reason)
- Sub-agent outputs
- Final response

## Graph Structure
```
Entry → Governor → Supervisor → RAG → Syllabus → Generate → End
         ↓ (if rejected)
         End
```

## Next Steps
- Feature 07: Implement Governor (Policy Engine)
- Feature 07: Implement Supervisor (Router)
- Feature 07: Implement sub-agents

