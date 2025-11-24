# Langfuse Local Setup Guide

## Step 1: Access Langfuse UI
Langfuse is now running at: http://localhost:3000

## Step 2: Create Account
1. Open http://localhost:3000 in your browser
2. Sign up with any email (e.g., `admin@centennialcollege.ca`)
3. Create a password

## Step 3: Create Project
1. After login, create a new project called "Luminate AI Course Marshal"
2. Navigate to **Settings** → **API Keys**
3. Copy the **Public Key** and **Secret Key**

## Step 4: Update Backend .env
Update the following variables in `backend/.env`:

```bash
# Replace with your local Langfuse keys
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Use local Langfuse (not cloud)
LANGFUSE_HOST=http://observer:3000
LANGFUSE_BASE_URL=http://localhost:3000
```

## Step 5: Restart Backend
```bash
docker compose restart api_brain
```

## Step 6: Verify Integration
Run the verification script:
```bash
cd backend
python scripts/verify_langfuse.py
```

## What Langfuse Tracks
- **Traces**: Full conversation flows (Governor → Supervisor → Sub-agents)
- **Spans**: Individual agent steps (RAG retrieval, LLM calls, policy checks)
- **Scores**: Governor approval/rejection decisions
- **Metadata**: User context, model selection, retrieved sources

## Accessing Traces
1. Go to http://localhost:3000
2. Navigate to **Traces** tab
3. Click on any trace to see the full execution graph
4. Use filters to find specific queries or errors

