# ETL Runbook: COMP 237 Ingestion (Gemini/Groq Safe)
**Audience:** Humans & Agents who operate the data pipeline  
**Goal:** Keep ChromaDB populated with COMP 237 materials using Gemini embeddings (models/embedding-001). Groq is not used for embeddings; keep it for inference only.

## 1) Prerequisites
- Docker + Docker Compose running locally (`docker compose up -d`).
- Python 3.11+ with access to `backend/requirements.txt`.
- Env vars: `GOOGLE_API_KEY` (Gemini), `CHROMADB_HOST=localhost`, `CHROMADB_PORT=8001`. Optional: `GROQ_API_KEY` (for inference validation), but not needed for ETL.
- Data source present at `raw_data/` (default COMP 237 export).

## 2) Start Services
```bash
docker compose up -d chroma postgres redis backend
```
*Check:* `curl http://localhost:8001/api/v1/collections` should return without connection errors.

## 3) Ingest Course Data
```bash
cd backend
python -m venv venv && source venv/bin/activate  # or reuse existing
pip install -r requirements.txt                  # if not already installed
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8001
export GOOGLE_API_KEY=...                        # Gemini key with embed permissions
python scripts/ingest_course_data.py
```
*Success criteria:* Script logs `✅ ETL Pipeline completed successfully!` with non-zero counts for files/chunks/ingested.

## 4) Verify the Collection
```bash
python verify_rag.py
```
- Expect SSE stream mentioning COMP 237 and sources in stdout.  
- If you want a quick count check inside Python:
```python
from app.rag.chromadb_client import get_chromadb_client
print(get_chromadb_client().get_collection_info())
```

## 5) Re-ingest / Reset Procedure
Only if embeddings are mismatched or data is stale:
```bash
python scripts/delete_collection.py   # drops comp237_course_materials
python scripts/ingest_course_data.py  # re-run ingestion
```
*Guardrail:* Ensure `GOOGLE_API_KEY` points to the intended project; otherwise embeddings may shift.

## 6) Troubleshooting
- **Symptom:** 404/permission errors from Gemini.  
  **Fix:** Use explicit model IDs: `models/embedding-001` for embeddings; `gemini-2.0-flash` / `gemini-1.5-pro-001` for chat. Check API key scope in AI Studio.
- **Symptom:** Dimension mismatch in Chroma.  
  **Fix:** Run `delete_collection.py`, confirm you’re on Gemini embeds (768 dims), then re-ingest.
- **Symptom:** Empty retrievals.  
  **Fix:** Confirm `raw_data/` exists and contains PDFs/DOCX/TXT; check log counts after ingestion.

## 7) Operational Notes for Agents
- Collection name is fixed: `comp237_course_materials`.
- Embedding generator is Gemini-only; do not swap to other providers without updating the wrapper in `app/rag/chromadb_client.py`.
- Keep course_id metadata as `COMP237` unless explicitly running multi-course experiments.***
