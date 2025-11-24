# Collaboration Plan & Documentation Strategy
**Date:** November 24, 2025
**Context:** Handover to Agent Team & Human Operators

## 1. Alignment & Strategy Response

You asked for a plan that serves two masters: **Agents** (strict, structural, schematic) and **Humans** (operational, strategic, "how-to"). Here is my proposed approach:

### 1.1 Documentation Structure (docs/swe-repo-2betterthan1)
We will separate concerns to avoid "context pollution" for agents and "information overload" for humans.

**For Agents (The "Brain" Context):**
-   `agent_contracts.md`: Defines `AgentState`, `Governor` laws, and routing logic strictly.
-   `api_spec.md`: JSON/Pydantic schemas for every tool input/output and the SSE stream format.
-   `etl_manifest.md`: Precise file structure expectations for the data pipeline.

**For Humans (The "Hands" Context):**
-   `activation_guide.md`: A "Zero to Hero" runbook. Combined steps for Ingest -> Fix Frontend -> Deploy.
-   `architecture_decisions.md`: Why we chose Plasmo, why we use Chroma locally, why Governor exists.
-   `gtm_brief.md`: The "Sales Pitch" and pilot strategy in one page.

### 1.2 Scope & Priority
1.  **Critical Path (Phase 1):** `activation_guide.md` + Data Ingestion verification.
2.  **Technical Debt (Phase 2):** `api_spec.md` + Chat Unification (Refactoring `ChatContainer`).
3.  **Expansion (Phase 3):** GTM assets.

**Constraint Update:** We stuck to `gemini-1.5-flash` as the primary driver. We are currently debugging API connectivity issues (404s) which must be resolved before the "Brain" is functional.

---

## 2. Immediate Execution Plan

1.  **Fix the Brain:** The backend is throwing 404s for Gemini models. I will rotate the model identifiers to stable versions (`gemini-1.5-flash-001` or `gemini-pro`) until one bites.
2.  **Verify RAG:** Once the model talks, run `verify_rag.py` to confirm it knows about "COMP 237".
3.  **Refactor Frontend:** Switch `ChatContainer` to `useChat` hook.
4.  **Write the Docs:** Populate `docs/swe-repo-2betterthan1` with the live, working state.

Proceeding with **Step 1: Fix the Brain**.

