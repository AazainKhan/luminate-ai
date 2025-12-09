# Progress Report vs Codebase

Comparison of claims in `AiTutor-ProgressReport-FInal (1).md` to the current repository.

## Aligns with implementation
- **LangGraph agent with planner-driven routing**: Report describes LangGraph routing with a PlannerAgent (AiTutor-ProgressReport-FInal (1).md:286). Code implements a 4-node LangGraph pipeline (`backend/app/agent/graph.py:1-105`) with heuristic + LLM classification in the planner (`backend/app/agent/nodes/planner.py:240-520`).
- **RAG via ChromaDB**: Report cites ChromaDB-backed retrieval (AiTutor-ProgressReport-FInal (1).md:286, 365). Implementation uses Gemini embeddings over multi-collection Chroma (course, OER, embedded) in `backend/app/agent/tools/rag.py:1-220`.
- **4-level scaffolding and stuck detection**: Report claims a 4-level escalation system (AiTutor-ProgressReport-FInal (1).md:286, 640). Code defines the levels and stuck flags (`backend/app/agent/state.py:13-55`), detects confusion patterns (`backend/app/agent/nodes/planner.py:240-320`), and prompts enforce the laddered responses (`backend/app/agent/prompts/tutor.py:1-200`).
- **Supabase-backed chat persistence and auth**: Report recommends Supabase/Postgres storage (AiTutor-ProgressReport-FInal (1).md:155, 813). Code saves chats/messages to Supabase (`backend/app/api/routes/history.py:34-138`), enforces Supabase JWT auth (`backend/app/api/middleware.py:1-110`), and streams chat replies via FastAPI (`backend/app/api/routes/chat.py:32-185`).
- **Dockerized services with persistent ChromaDB**: Report suggests Docker deployment and persisting Chroma embeddings (AiTutor-ProgressReport-FInal (1).md:813-814). `docker-compose.yml:36-64` provisions ChromaDB with a volume alongside Redis/Langfuse/Minio.

## Divergences / updates needed
- **MathAgent computation stack**: Report claims SymPy + Wolfram Alpha computation with progressive hints (AiTutor-ProgressReport-FInal (1).md:286, 370, 449, 462, 1060). Current math node uses Gemini 2.5 Flash only (`backend/app/agent/nodes/math.py:24-205`); SymPy/Wolfram are absent from `backend/requirements.txt`, and no computation tool calls exist. Report should drop/fix this or the code needs those tool integrations.
- **FeedbackAgent and weekly LLaMA3 QA loop**: Report describes a FeedbackAgent running weekly cron analyses of low-rated chats with LLaMA 3 and writing critiques (AiTutor-ProgressReport-FInal (1).md:286, 640-769, 1271). Codebase has no FeedbackAgent node, cron, or analytics_insights table—LangGraph only includes planner/tutor/math/reject/evaluator (`backend/app/agent/graph.py:1-105`) and no LLaMA integration.
- **Ratings / analytics storage**: Report says ratings and analytics are stored in PostgreSQL (AiTutor-ProgressReport-FInal (1).md:371, 421-423, 450). Implementation streams feedback only to Langfuse (`backend/app/api/routes/chat.py:28-78`) and writes chats/messages to Supabase (`backend/app/api/routes/history.py:34-99`); no rating persistence or analytics_insights table exists.
- **Model roster**: Report references LLaMA 3 and Claude usage (AiTutor-ProgressReport-FInal (1).md:286, 450, 459), but agents call Gemini models exclusively (`backend/app/agent/nodes/planner.py:432-506`, `backend/app/agent/nodes/tutor.py:124-213`, `backend/app/agent/nodes/math.py:159-205`). No switching to non-Gemini models is wired.
- **API surface naming**: Report mentions REST endpoints like `/ask` and `/feedback/run` during deployment guidance (AiTutor-ProgressReport-FInal (1).md:141-149). Actual API exposes `/api/chat/stream` (SSE chat) and `/api/chat/feedback` plus `/api/execute/` and `/api/sources/generate-description` (`backend/app/api/routes/chat.py`, `backend/app/api/routes/execute.py`, `backend/app/api/routes/sources.py`); docs should reflect current paths.

## Detailed verification (with headings and pinpointed gaps)

### Executive Summary
- Claimed: Multi-agent system with SymPy/Wolfram MathAgent, LLaMA3 FeedbackAgent, Chroma RAG, 4-level scaffolding.
- Code: Only planner→tutor/math/reject/evaluator graph (`backend/app/agent/graph.py`). Math is Gemini text-only; no SymPy/Wolfram deps or calls. No FeedbackAgent or LLaMA integration. RAG and scaffolding are present.

### 1. Introduction / Problem / Significance
- Claimed: COMP237-only scope, Socratic scaffolding pedagogy.
- Code: Scope/off-topic/integrity checks in planner (`backend/app/agent/nodes/planner.py:84-173`). Socratic/scaffolding prompts enforced (`backend/app/agent/prompts/tutor.py`).

### 1.4 Literature Review / 1.5 Exploratory Data Analysis
- Claimed: Corpus analyzed and validated for scale/coverage.
- Code: ETL/ingestion scripts exist (`backend/app/etl/*`), but no runtime metrics, validation, or surfaced corpus health in agent/API.

### 2. Methodology – System Architecture
- Claimed: Distinct Governor, Supervisor, Feedback agents; weekly QA loop.
- Code: Governor checks folded into planner; no supervisor or feedback nodes; no cron/scheduled QA.

### 2.2 Agent Overview / Technology Stack
- Claimed: FastAPI, LangGraph, Chroma, SymPy/Wolfram, LLaMA3/Claude available.
- Code: FastAPI/LangGraph/Chroma/Gemini present. SymPy/Wolfram/LLaMA3/Claude absent from requirements and code paths. Neo4j provisioned (docker-compose, `backend/app/rag/graph_rag.py`) but unused by tutor/math nodes.

### 2.3 LangGraph Multi-Agent Architecture
- Claimed: Rich output schemas and performance metrics for each agent.
- Code: Minimal state (`backend/app/agent/state.py`); evaluator logs mastery/interaction metadata only. No performance metric collection.

### 2.4 Scaffolding Pedagogy
- Claimed: Four-level escalation, stuck detection, progressive hints, math verification.
- Code: Levels/stuck detection implemented (planner patterns; prompts). Math hints are prompt-only; no computation-backed verification, no adaptive pacing logic.

### 2.5 LangGraph Orchestration / State Management
- Claimed: Structured queue/init flow and robust shared state.
- Code: Streaming “thinking” events for UI (`backend/app/agent/graph.py:120-218`); no queue/backpressure or retry orchestration. State is per invocation.

### 2.6 Introspection and Monitoring
- Claimed: Real-time performance tracking and weekly retrospective analysis.
- Code: Langfuse tracing/scoring only. No cron jobs, batch exports, ratings storage, or analytics_insights table.

### 2.7 Implementation Details (RAG, Hybrid Routing)
- Claimed: Chroma RAG, hybrid routing, possible provider fallback.
- Code: Multi-collection Chroma RAG implemented. “Hybrid routing” = heuristics + Gemini classification; no multi-LLM/provider fallback.

### 2.8 Authentication and Security
- Claimed: Secure auth, secret handling, RLS.
- Code: Supabase JWT verification and domain-based roles (`backend/app/api/middleware.py`). RLS/audit logging not expressed in code; relies on Supabase config. Secrets via env vars; no rotation/management layer.

### 3. Deployment Strategy
- Claimed: Containerized deploy, cloud/on-prem/edge, model hosting guidance.
- Code: Docker Compose runs FastAPI, Chroma, Redis, Langfuse, Minio, ClickHouse, Neo4j. Supabase and LLMs are external; models not hosted locally (Gemini APIs only).

### 4. Results / Functional Tests
- Claimed: Functional test results achieved.
- Code: No automated tests for agent routing/RAG/scaffolding; no CI asserting those claims.

### 5–6 Conclusions / Recommendations
- Claimed: A/B testing scaffolding, controlled studies, richer personalization roadmap.
- Code: No feature flags, experiment toggles, or telemetry hooks to run A/Bs. Personalization limited to mastery prompt text; no experimentation infra.

### Appendices (Use Cases, Requirements, System Design)
- Claimed: Computation-backed math tutoring; feedback analytics; graph/Neo4j components; inline citation enforcement.
- Code: Math is LLM-only (no SymPy/Wolfram). No feedback analytics storage or analytics_insights table. GraphRAG/Neo4j exists but is not used by tutor/math pipeline. Inline citation UX exists in extension (`extension/src/components/ai-elements/sources.tsx`) and guidance (`docs/inline-citation.md`), but backend only streams sources; it does not enforce inline citation placement in responses.
