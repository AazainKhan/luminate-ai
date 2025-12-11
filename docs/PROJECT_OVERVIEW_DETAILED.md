# Luminate AI – Deep Project Overview

This document gives a comprehensive view of the Luminate AI Course Marshal project: goals, architecture, data flows, services, and developer workflows. Use it as the single place to understand how the platform fits together across backend, frontend, infra, and pedagogy.

---

## 1) Mission & Pedagogy
- **Purpose:** Agentic AI tutor for Centennial College’s COMP 237 course, focused on scaffolding rather than answer‑dumping.
- **Teaching model:** 4-level escalation aligned to LearnLM + Adarsh’s guide  
  1. Diagnostic questions only  
  2. Directed hints/analogies  
  3. Concrete worked example  
  4. Full explanation with metacognition prompt
- **Guardrails:** Governor enforces 3 laws — scope (COMP 237 only), integrity (no homework/exam answers), mastery check (verify understanding).

---

## 2) Repository Layout (high level)
- `backend/` — FastAPI service + LangGraph agent (`app/agent/*`), observability, ETL, RAG helpers.
- `extension/` — Plasmo/React/Tailwind Chrome extension (student + admin side panels).
- `docs/` — How-tos and references (Gemini, Langfuse, Docker, RAG, inline citations, OER, etc.).
- `features/` — Feature specs.
- Root assets: `docker-compose.yml`, `clickhouse-config.xml`, top-level `README.md`.

---

## 3) Backend (FastAPI + LangGraph)
**Entry point:** `backend/main.py` (FastAPI app).  
**Agent graph:** `backend/app/agent/graph.py` defines a 4-node LangGraph compiled once and reused.

### 3.1 Pipeline & Nodes
1. **Planner / Governor (`nodes/planner.py`)**
   - Regex + RAG scope checks (COMP 237 only) and integrity checks (no “do my homework/exam”).
   - Classifies into `TaskType` (`explain`, `code`, `solve`, `reject`); defaults to scaffolded tutoring.
   - Sets stuck signals & escalation level (1–4).
2. **Router (`route_from_plan` in `graph.py`)**
   - explain/code → `tutor`; solve → `math`; reject → `reject`.
3. **Tutor (`nodes/tutor.py`)**
   - Uses prompts in `prompts/tutor.py` to deliver scaffolding by level.
   - Consumes formatted context string + selected sources.
4. **Math (`nodes/math.py`)**
   - Math-first prompt, symbolic reasoning; still scaffolded.
5. **Reject (`nodes/reject.py`)**
   - Returns safe refusal for off-scope/integrity violations.
6. **Evaluator (`nodes/evaluator.py`)**
   - Detects concepts/misconceptions, updates mastery hints, logs observability scores.

### 3.2 State & Scaffolding
- State schema: `agent/state.py` (TypedDict). Key fields: `query`, `plan`, `_subtask_index`, `retrieved_docs`, `rag_metadata`, `context_str`, `escalation_level`, `stuck_count`, `is_stuck`, `sources`, `evaluation`, `approved/rejection_reason`, `trace_id/session_id/chat_id`.
- Escalation levels mirror the 4-phase pedagogy above.

### 3.3 RAG & Tools
- RAG helper: `app/rag/chromadb_client.py` + `app/agent/tools/rag.py` (Chroma over HTTP, Gemini embeddings).
- Sources preserved for citations; `source_selection` tracks reasoning.
- Math tool & other utilities live in `app/agent/tools/`.

### 3.4 API Surface (`app/api/routes/*`)
- `chat.py` — SSE streaming endpoint `/api/chat/stream` (AI SDK v5 events: `trace-id`, `thinking`, `text-delta`, `reasoning-delta`, `sources`, `evaluation`, `finish`), plus feedback scoring.
- `history.py` — Chat persistence (Supabase): create chat, fetch history, save messages, auto-title.
- `mastery.py` — Mastery CRUD and quiz evaluation.
- `execute.py` — E2B code sandbox execution.
- `sources.py` — Source listing/upload helpers.
- `media.py` — Media upload proxying.
- `admin.py` — Admin triggers (e.g., ETL kicks).
- `models.py` — Model selection metadata.

### 3.5 Observability
- Langfuse v3 via `app/observability/*` and `propagate_attributes` in `graph.py`.
- Thinking trace persisted from SSE `thinking` events; feedback `/api/chat/feedback` attaches scores.

### 3.6 Config & Environment
- Settings in `backend/app/config.py`; load from `backend/.env`.
- Required keys: Supabase URL/keys, Google/Anthropic API keys, Chroma host/port, Redis, Langfuse, Neo4j, E2B.

---

## 4) Frontend (Chrome Extension)
**Tech:** Plasmo + React 18 + TypeScript + Tailwind + Shadcn UI (see `components.json`).  
**Entry points:**  
- `src/sidepanel.tsx` — Student tutor UI.  
- `src/admin-sidepanel.tsx` — Admin dashboard.  
- `background.ts` — Extension background scripts.

### 4.1 Types & Streaming
- Message/thinking schemas in `src/types/index.ts` (ThinkingStep types, citations, reasoning, code blocks, suggestions, metadata).
- Streaming matches backend events: accumulates `text-delta` & `reasoning-delta`, records `thinkingTrace`, citations, evaluation, `traceId`, `finish`.
- Supports legacy queue/tool/task structures for backward compatibility.

### 4.2 Components & UX
- Components under `src/components/` (chat UI, inline citations, accordions for thinking trace, admin widgets).
- Hooks under `src/hooks/` (auth, chat, streaming buffer management).
- Inline citation UX guided by `docs/inline-citation.md`; math rendering via KaTeX; code blocks support execution metadata.

### 4.3 Build & Tests
- Scripts (`extension/package.json`): `pnpm dev`, `pnpm build`, `pnpm package`, Playwright e2e (`pnpm test:e2e`/`--headed`/`--ui`).
- Config: `tailwind.config.js`, `playwright.config.ts`, `wdio.conf.ts`.
- Env: `extension/.env.local` (Supabase + API URL).

---

## 5) Data Ingestion & RAG Content
- ETL pipeline: `backend/app/etl/` (e.g., `pipeline.py`, `blackboard_parser.py`, `document_processor.py`) handles Blackboard exports and other course/OER inputs.
- Outputs embedded documents into Chroma (`memory_store` service) using Gemini embeddings; supports multiple collections (see docs on RAG V2, OER setup, data quality).
- Helper docs: `docs/BLACKBOARD_SETUP_QUICK_REFERENCE.md`, `BLACKBOARD_URL_INTEGRATION.md`, `OER_SETUP_GUIDE.md`, `OER_EXPANSION_COMPLETE.md`, `DATA_QUALITY_REPORT.md`.

---

## 6) Infrastructure & Services (`docker-compose.yml`)
- **api_brain** (port 8000) — FastAPI + LangGraph; mounts backend code; depends on data stores below.
- **memory_store** (Chroma, 8001→8000) — Vector DB persistence.
- **redis** (6379) — Caching/session.
- **langfuse-web** (3000) & **langfuse-worker** — Observability stack; uses **postgres** (5432), **clickhouse** (8123/9000), **minio** (S3-compatible, 9090/9091).
- **neo4j** (7474/7687) — Knowledge graph placeholder (future GraphRAG).
- Shared bridge network `luminate_network`; volumes for persistence (Chroma, Redis, Postgres, ClickHouse, Minio, Neo4j).

---

## 7) Authentication & Security Posture
- Supabase passwordless OTP; roles by email domain (`@my.centennialcollege.ca` students, `@centennialcollege.ca` admins).
- RLS on Supabase tables; JWT validation on backend endpoints.
- Governor blocks off-topic/integrity violations; responses routed to `reject` node when necessary.
- Environment files are gitignored; API keys never committed.
- E2B execution sandbox isolates code runs.

---

## 8) Developer Workflows
- **Setup:** Follow root `README.md` prerequisites; create `backend/.env` and `extension/.env.local`.
- **Run locally:** `docker-compose up -d` for data/observability; `uvicorn main:app --reload` in `backend`; `pnpm dev` in `extension` then load unpacked build.
- **Quick backend checks (from README):**
  - `python -c "from app.agents.supervisor import Supervisor; Supervisor().route_intent('Explain gradient descent')"`
  - `python -c "from app.agents.tutor_agent import run_agent; print(run_agent('What is backpropagation?'))"`
- **E2E:** In `extension`, `pnpm build && pnpm test:e2e`.
- **Observability:** Langfuse UI at `http://localhost:3000`; feedback via `/api/chat/feedback`.

---

## 9) Documentation Map (selected)
- High-level guide (this file): `docs/PROJECT_OVERVIEW_DETAILED.md`.
- Quick start & architecture: root `README.md`.
- Docker/infra: `docs/DOCKER_ARCHITECTURE.md`, `docs/docker.md`.
- RAG guides: `docs/RAG_V2_FRONTEND_GUIDE.md`, `RAG_V2_TESTING_CHECKLIST.md`, [RAG_V2_MULTICOLLECTION.md](./RAG_V2_MULTICOLLE%20CTION.md).
- Gemini prompts/structured output: `docs/gemini-*.md`, `prompting-strategies.md`.
- Langfuse: `docs/LANGFUSE_SETUP.md`, `langfuse-gemini.md`, `LANGFUSE_IMPLEMENTATION.md`.
- Inline citations: `docs/inline-citation.md`.
- Auth: `docs/AUTH_OTP_SETUP.md`, `FIX_AUTH_403_ERROR.md`.
- PRD/status: `docs/PROGRESS_REPORT_CODEBASE_COMPARISON.md`, `AiTutor-ProgressReport-FInal (1).md`.

---

## 10) What Happens on a Chat Request (end-to-end)
1. **User asks via extension** → `background.ts` forwards to backend.
2. **`/api/chat/stream`** saves user message, loads recent history, auto-titles chat.
3. **Agent pipeline runs**: Planner enforces laws + classifies → router → tutor/math/reject → evaluator.
4. **Streaming**: SSE emits `trace-id`, `thinking` (scope/integrity/escalation/rag/strategy), `text-delta`, `reasoning-delta`, `sources`, `evaluation`, `finish`.
5. **Frontend renders**: Side panel accumulates content, updates thinking accordion, shows inline citations, reasoning, and sources; stores metadata (traceId, chatId).
6. **Persistence/observability**: Messages + metadata saved to Supabase; Langfuse spans/scores recorded; optional user feedback posted to `/api/chat/feedback`.

---

## 11) Minimal Responsibilities for Contributors
- Keep changes scoped and well-documented.
- Respect pedagogical guardrails (no direct assignment answers; keep scaffolding levels intact).
- Preserve SSE event contract and citation structures.
- Do not commit secrets; rely on `.env` files and docker-compose overrides.
- Prefer existing prompts/components; add new dependencies only when necessary.
