# Activation Guide: Human Operator Runbook
**Goal:** Go from "Zero" to "Working AI Tutor".

## Phase 1: The Brain (Backend & Data)

### 1.1 Prerequisites
-   Docker & Docker Compose installed.
-   Python 3.11+ installed.
-   Valid `.env` in `backend/` with `GOOGLE_API_KEY` (AI Studio, Gemini 2.0 access).

### 1.2 Start Infrastructure
```bash
docker compose up -d --build
```
*Verify:* Visit `http://localhost:8000/docs`. You should see FastAPI Swagger UI.

### 1.3 Ingest Data (The "Brain Transplant")
The system starts empty. You must feed it the course data.
```bash
# From project root
cd backend
source venv/bin/activate  # or create one
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8001
python scripts/ingest_course_data.py
```
*Success Criteria:* Output says "✅ ETL Pipeline completed successfully!".

### 1.4 Verify Intelligence
Run the verification script to ensure the brain is connected to the mouth.
```bash
python verify_rag.py
```
*Success Criteria:* "✅ Success: Agent identified the course correctly."

---

## Phase 2: The Face (Frontend Extension)

### 2.1 Install Dependencies
```bash
cd extension
pnpm install
```

### 2.2 Configure Environment
Ensure `extension/.env.local` exists:
```env
PLASMO_PUBLIC_API_URL=http://localhost:8000
PLASMO_PUBLIC_SUPABASE_URL=...
PLASMO_PUBLIC_SUPABASE_ANON_KEY=...
```

### 2.3 Development Mode
```bash
pnpm dev
```
-   Load the extension in Chrome (`chrome://extensions` -> Load Unpacked -> `extension/build/chrome-mv3-dev`).
-   Open Side Panel.
-   Login with email (check terminal for OTP if running locally, or email).

## Phase 3: Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| **404 on Chat** | Wrong Model Name | Update `supervisor.py` to use `gemini-2.0-flash`. |
| **Embeddings Error** | Dimension Mismatch | Run `scripts/delete_collection.py` then re-ingest. |
| **Connection Refused** | Docker down | `docker compose up -d`. |










