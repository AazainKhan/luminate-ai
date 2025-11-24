# Ops Playbook (Local Dev)
**Audience:** Humans operating the stack day-to-day  
**Scope:** Local Docker + Plasmo extension; Gemini/Groq only.

## 1) Start/Stop
- Start everything: `docker compose up -d` (brings up backend, Chroma, Postgres, Redis).  
- Stop: `docker compose down` (add `-v` only if you intend to wipe Chroma/Postgres volumes).  
- Health checks: `http://localhost:8000/docs` (API), `curl http://localhost:8001/api/v1/collections` (Chroma).

## 2) Environment
- Backend `.env`: `GOOGLE_API_KEY`, `GROQ_API_KEY` (optional for inference), `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `CHROMADB_HOST=chroma`, `CHROMADB_PORT=8000` (inside docker) or `localhost:8001` when local.  
- Extension `.env.local`: `PLASMO_PUBLIC_API_URL=http://localhost:8000`, Supabase URL/anon key, and any feature flags.  
- Providers: Use explicit model IDs (`gemini-2.0-flash`, `gemini-1.5-pro-001`, Groq model names like `llama-3.1-70b-versatile` if enabled).

## 3) Logging & Debug
- **Backend:** `backend/app/agents/governor.py` has logging hooks; keep them enabled to see scope/integrity denials.  
- **Extension:** Chrome DevTools console + Network tab on `chrome-extension://…` origin; enable “Preserve log”.  
- **ETL:** `scripts/ingest_course_data.py` logs counts; `verify_rag.py` streams response for sanity.

## 4) Common Issues
- 404 from Gemini → use explicit versioned IDs; confirm `GOOGLE_API_KEY` scope.  
- Embedding dimension mismatch → run `scripts/delete_collection.py` then re-ingest (Gemini embeds are 768-d).  
- 401 on chat → Supabase session expired; logout/login in extension.  
- Slow first token → check GPU/CPU load; ensure Docker containers aren’t restarting (Run `docker compose ps`).

## 5) Routine Tasks
- **Rebuild extension:** `pnpm -C extension dev` (dev) or `pnpm -C extension build` (prod).  
- **Backend deps update:** `pip install -r requirements.txt` inside `backend` venv.  
- **Data refresh:** Re-run ETL when raw_data changes; keep collection name consistent (`comp237_course_materials`).

## 6) Safety Rails
- Do not switch embedding providers without updating `app/rag/chromadb_client.py` wrapper.  
- Keep JWT secret/test tokens out of commits; use env vars in CI if added.  
- Limit model list to Gemini/Groq to avoid runtime 404s or unexpected costs.***
