# Agent Contracts & System Invariants
**Version:** 1.0.0
**Audience:** Autonomous Agents & Backend Developers

## 1. State Schema (`AgentState`)
The system of record is the `AgentState` TypedDict in `backend/app/agents/state.py`. All agents must respect this schema.

```python
class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add]  # Append-only chat history
    query: str                                     # Current user turn
    user_id: Optional[str]
    user_email: Optional[str]
    intent: str                                    # Router output: "fast", "coder", "reasoning"
    model_selected: str                            # Allowed: "gemini-2.0-flash", "gemini-1.5-pro-001", Groq model (e.g., "llama-3.3-70b-versatile")
    retrieved_context: List[dict]                  # From ChromaDB
    governor_approved: bool                        # Must be True to proceed
    response: Optional[str]                        # Final output
    error: Optional[str]                           # Error state
```

## 2. Governor Laws (The "Constitution")
The `Governor` node enforces 3 invariants. **Do not bypass.**

1.  **Law of Scope:** All queries must relate to COMP 237.
    -   *Implementation:* Semantic distance check in ChromaDB (< 1.5).
2.  **Law of Integrity:** No complete solutions for graded work.
    -   *Implementation:* Keyword regex ("write code for", "solve assignment").
3.  **Law of Mastery (Future):** Answers must match student's mastery level.

## 3. API Contracts

### 3.1 Chat Streaming (SSE)
**Endpoint:** `POST /api/chat/stream`
**Format:** Server-Sent Events (Vercel AI SDK Data Stream Protocol).

**Event Types:**
-   `text-delta`: Main content chunk. `{ "type": "text-delta", "textDelta": "..." }`
-   `reasoning-delta`: Chain-of-thought chunk. `{ "type": "reasoning-delta", "reasoningDelta": "..." }`
-   `sources`: Citation metadata. `{ "type": "sources", "sources": [...] }`
-   `finish`: Stream end. `{ "type": "finish" }`

### 3.2 Admin Upload
**Endpoint:** `POST /api/admin/upload`
**Payload:** `Multipart/form-data` (file).
**Behavior:** Triggers asynchronous ETL. Does NOT block.

## 4. Data Invariants
-   **ChromaDB Collection:** `comp237_course_materials`
-   **Embedding Dimension:** 768 (Gemini Embedding 001)
-   **Metadata Fields:** `source_filename`, `page_number`, `course_id`.

## 5. LLM Providers (Allowed Only)
- **Gemini (primary):** `gemini-2.0-flash`, `gemini-1.5-pro-001` for chat; `models/embedding-001` for embeddings.
- **Groq (optional inference):** e.g., `llama-3.3-70b-versatile` if wired into supervisor.  
- **Not permitted:** Remove or disable references to other providers/models to avoid 404s and drift.***

## 6. Architecture Alignment (Main Branch Vision)
The current `Governor-Supervisor` architecture implements the "Master Coordinator" vision described in `README.md`.

| Vision (Main) | Current Implementation (`feat/activation-and-docs`) |
| :--- | :--- |
| **Master Coordinator** | `Supervisor` (Router) + `Governor` (Policy Engine) |
| **Navigator Agent** | `intent: syllabus_query` (Routes to Gemini Flash + RAG) |
| **Math Agent** | `intent: reasoning` (Routes to Gemini Flash / Groq) |
| **Educate Agent** | `intent: fast` (General RAG flow) |
| **Evaluator / Study Plan** | *Placeholder* (Reserved for Phase 3 Implementation) |
