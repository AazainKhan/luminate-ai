# Luminate AI Course Marshal - AI Agent Instructions

## Project Overview
Agentic AI tutoring platform for Centennial College's COMP 237 (AI course), delivered as a Chrome Extension with a FastAPI backend. Uses **Governor-Agent pattern** with LangGraph for enforcing course policies while providing intelligent tutoring.

## Architecture

### The "Brain" - LangGraph Agent Pipeline (backend/app/agents/)
**Critical: This is NOT a simple chatbot.** The agent follows a cyclical, multi-node architecture:

```
Governor (Policy Engine) → Supervisor (Model Router) → RAG → Syllabus → Generate → Evaluator
```

Key nodes explained:
- **Governor** (`governor.py`): Enforces 3 laws before ANY agent action
  - Law 1: Scope (COMP 237 topics only, verified via ChromaDB query distance)
  - Law 2: Integrity (no full solutions to assignments/tests)
  - Law 3: Mastery (verifies student understanding - implemented in `evaluator.py`)
- **Supervisor** (`supervisor.py`): Routes to 3 models based on task:
  - Gemini Flash (default) - logistics, definitions
  - Claude Sonnet - code generation
  - Gemini Pro - mathematical reasoning
- **Sub-agents** (`sub_agents.py`): RAGAgent, SyllabusAgent, ResponseGenerator
- **State** (`state.py`): AgentState TypedDict defines the shared state passed between nodes

**When modifying agents:** Always preserve the `AgentState` contract. Add new fields to `state.py` first, then update nodes. Test with `tutor_agent.py`'s `run_agent()` function.

### Frontend - Plasmo Chrome Extension (extension/)
Built with Plasmo framework (NOT vanilla Chrome extension APIs):
- **Side Panel** (`src/sidepanel.tsx`): Student chat interface
- **Admin Panel** (`src/admin-sidepanel.tsx`): Faculty file upload dashboard
- **Auth Flow**: Supabase passwordless OTP with email domain validation
  - Students: `@my.centennialcollege.ca`
  - Admins: `@centennialcollege.ca`

**Plasmo conventions:**
- Environment vars MUST be prefixed with `PLASMO_PUBLIC_` (see `extension/.env.local`)
- Entry points detected by filename: `sidepanel.tsx`, `popup.tsx`, etc.
- Build output goes to `extension/build/chrome-mv3-prod/`

### Backend - FastAPI + LangGraph (backend/)
**Critical path for requests:**
1. Extension → `/api/chat/stream` → `chat.py` router
2. Auth middleware validates Supabase JWT → `middleware.py:verify_token()`
3. Chat route invokes `tutor_agent.py:get_tutor_agent()` → LangGraph execution
4. Response streams back via Server-Sent Events (SSE)

**Key modules:**
- `app/api/routes/`: FastAPI endpoints (chat, admin, execute, mastery)
- `app/api/middleware.py`: JWT auth with HS256/RS256 fallback
- `app/etl/`: Blackboard ZIP parsing + document processing
- `app/rag/`: ChromaDB client + Gemini embeddings
- `app/tools/`: E2B code execution sandbox

## Critical Developer Workflows

### Starting the Full Stack
```bash
# Terminal 1: Docker services (ChromaDB, Redis, Langfuse)
docker-compose up -d

# Terminal 2: Backend (FastAPI)
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload

# Terminal 3: Extension (Plasmo dev mode with HMR)
cd extension
pnpm dev  # NOT npm run dev - uses pnpm
```

**Load extension in Chrome:**
1. `chrome://extensions/` → Enable Developer mode
2. Load unpacked → Select `extension/build/chrome-mv3-dev/`
3. Click extension icon → Open side panel

### Testing the Agent Locally
```bash
cd backend
python -c "from app.agents.tutor_agent import run_agent; print(run_agent('What is backpropagation?'))"
```

### Debugging Authentication Issues
**Common failure:** "401 Unauthorized" in extension console
1. Check `backend/.env` has `SUPABASE_JWT_SECRET` (from Supabase project settings)
2. Verify `extension/.env.local` has correct `PLASMO_PUBLIC_SUPABASE_URL`
3. Rebuild extension: `cd extension && pnpm dev`
4. Test JWT manually: `cd backend && python test_auth.py`

### Running the ETL Pipeline (Course Data Ingestion)
**Admin workflow:**
1. Sign in with `@centennialcollege.ca` email
2. Upload Blackboard export ZIP via Admin Panel
3. Backend extracts → parses `imsmanifest.xml` → chunks documents → embeds to ChromaDB

**Manual ETL testing:**
```bash
cd backend
python -c "from app.etl.pipeline import ETLPipeline; ETLPipeline().process_blackboard_export('data/export.zip', 'cleaned_data/', 'COMP237')"
```

## Project-Specific Conventions

### Authentication Pattern
**Backend:** Supabase JWT → FastAPI dependency injection
```python
from app.api.middleware import require_auth

@router.get("/protected")
async def protected_route(user_info: dict = require_auth):
    user_id = user_info["user_id"]  # Always available after auth
```

**Frontend:** Custom `useAuth` hook wraps Supabase client
```typescript
const { user, role, session } = useAuth()  // role is "student" or "admin"
```

### Streaming Chat Pattern
**Backend streams SSE:** `chat.py` uses `async def generate_stream()` generator
**Frontend consumes:** `use-chat.ts` reads `response.body.getReader()` chunks

### Vector Store Conventions
**ChromaDB collections:** Named by course ID (e.g., `COMP237`)
**Metadata schema:**
```python
{
  "course_id": "COMP237",
  "source_file": "module1.pdf",
  "page": 3,
  "chunk_id": "abc123"
}
```

### Generative UI Pattern
**Backend embeds XML in responses:**
```xml
<thinking>Agent reasoning here</thinking>
<quiz>{"question": "...", "options": [...]}</quiz>
<code language="python">print('hello')</code>
```

**Frontend auto-parses:** `ChatMessage.tsx` detects tags → renders `ThinkingAccordion`, `QuizCard`, `CodeBlock`

## Integration Points

### External Services
- **Supabase** (Auth + PostgreSQL): User auth, mastery tracking tables
- **ChromaDB** (Vector DB): Course embeddings, RAG retrieval
- **E2B** (Code Sandbox): Executes student Python code in isolated microVM
- **Langfuse** (Observability): Agent tracing (optional, disabled by default)

### Cross-Component Communication
**Extension → Backend:** REST API with JWT bearer tokens
**Agent nodes → Tools:** Function calling via LangChain tool interface
**ChromaDB queries:** Always include `where={"course_id": course_id}` filter

## Common Pitfalls

1. **Supabase JWT validation fails:** Check `SUPABASE_JWT_SECRET` matches your project (Settings → API → JWT Secret in Supabase dashboard)
2. **Plasmo env vars not loading:** Prefix with `PLASMO_PUBLIC_` and rebuild extension
3. **ChromaDB connection refused:** Ensure Docker `memory_store` container is running on port 8001
4. **Agent loops infinitely:** Check `tutor_agent.py:should_continue()` conditional edges
5. **E2B code execution errors:** Verify `E2B_API_KEY` in `backend/.env` and check quota at e2b.dev

## Key Files to Reference

- **Agent architecture:** `backend/app/agents/tutor_agent.py` (entry point)
- **Policy enforcement:** `backend/app/agents/governor.py` (course constraints)
- **Streaming chat:** `backend/app/api/routes/chat.py` + `extension/src/hooks/use-chat.ts`
- **Auth flow:** `backend/app/api/middleware.py` + `extension/src/lib/supabase.ts`
- **ETL pipeline:** `backend/app/etl/pipeline.py` (Blackboard ingestion)
- **Project status:** `PROJECT_STATUS.md` (feature completion tracker)
- **Database schema:** `docs/database_schema.sql` (Supabase tables)

## Feature Documentation
The `features/` directory contains numbered feature specs (01-11) documenting each major system component. Reference these when modifying existing features or adding new ones.
