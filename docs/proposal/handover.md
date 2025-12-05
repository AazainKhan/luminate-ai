# Project Handover & Proposal

## Status Verification
The system is **functionally complete** but **data empty**. The code for the agent, the UI, and the auth is written. The "brain" is empty because the vector database has not been populated.

## Immediate Work Orders (For the Engineer)

### 1. Ingest Data (Priority: Critical)
Run the following command from the project root:
```bash
source venv/bin/activate
python scripts/ingest_course_data.py
```
*Constraint:* Ensure Docker (ChromaDB) is running first.

### 2. Unify Frontend Chat Logic (Priority: High)
Delete `extension/src/lib/api.ts`'s `streamChat` function. Refactor `ChatContainer.tsx` to use the hook in `extension/src/hooks/use-chat.ts`. The hook handles state better and is more React-idiomatic.

### 3. Enable Governor Logging (Priority: Medium)
Uncomment the logging lines in `backend/app/agents/governor.py` to ensure we can see *why* a request was rejected (Scope vs Integrity).

## Resource Requirements
-   **Compute:** The current local setup (Docker) is sufficient for development.
-   **API Costs:** minimal (Gemini Flash is free tier eligible / very cheap).
-   **Personnel:** 1 Full Stack Engineer (Python/React) [YOU].

## Handover Note
Everything you need is in `docs/swe-repo/`. Follow the roadmap. The architecture is sound. Do not over-engineer. Just fill the database and fix the frontend hook.










