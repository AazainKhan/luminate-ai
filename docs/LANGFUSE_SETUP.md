# Langfuse Observability Setup

## Overview
Langfuse is now integrated into the Luminate AI Course Marshal backend for comprehensive observability and tracing of agent executions.

## What's Been Done

### 1. Infrastructure Setup ✅
- Enabled Langfuse services in `docker-compose.yml`:
  - `observer`: Langfuse web UI (port 3000)
  - `langfuse_worker`: Background job processor
  - `postgres`: Database for Langfuse data
  - `clickhouse`: Analytics database
  - `minio`: S3-compatible storage for events

### 2. Backend Integration ✅
- Created `app/observability/langfuse_client.py` with:
  - Langfuse client initialization
  - Callback handler for LangChain integration
  - Trace creation utilities
  
- Integrated into `app/agents/tutor_agent.py`:
  - Automatic trace creation for each query
  - Trace metadata logging (query, user, intent, model)
  - Error tracking in traces
  
- Integrated into `app/agents/supervisor.py`:
  - LLM calls automatically traced via callbacks
  - Model selection and routing logged

### 3. Configuration
The following environment variables control Langfuse:

```bash
# Required (get from Langfuse UI after setup)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Local Langfuse (default)
LANGFUSE_HOST=http://observer:3000
LANGFUSE_BASE_URL=http://localhost:3000
```

## Next Steps (Manual Setup Required)

### Step 1: Access Langfuse UI
1. Open http://localhost:3000 in your browser
2. You should see the Langfuse welcome screen

### Step 2: Create Account
1. Click "Sign Up" or "Get Started"
2. Use your admin email: `admin@centennialcollege.ca`
3. Create a secure password
4. Complete the signup process

### Step 3: Create Project
1. After login, create a new project
2. Project name: **"Luminate AI Course Marshal"**
3. Description: **"AI Tutor for COMP 237 - Centennial College"**

### Step 4: Get API Keys
1. Navigate to **Settings** → **API Keys**
2. You'll see two keys:
   - **Public Key** (starts with `pk-lf-`)
   - **Secret Key** (starts with `sk-lf-`)
3. Copy both keys

### Step 5: Update Backend Configuration
Update `backend/.env` with your keys:

```bash
# Replace these with your actual keys from Step 4
LANGFUSE_PUBLIC_KEY=pk-lf-your-actual-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-actual-secret-key-here

# Keep these as-is for local development
LANGFUSE_HOST=http://observer:3000
LANGFUSE_BASE_URL=http://localhost:3000
```

### Step 6: Restart Backend
```bash
docker compose restart api_brain
```

### Step 7: Verify Integration
Run the verification script:

```bash
cd backend
python scripts/verify_langfuse.py
```

Expected output:
```
✅ Langfuse client initialized
✅ Trace created successfully
✅ Agent executed successfully
📊 Check Langfuse UI for trace: http://localhost:3000
```

## What Langfuse Tracks

### Traces
Every student query creates a trace showing:
- **Query**: The student's question
- **User**: Student ID and email
- **Intent**: Detected intent (fast, coder, reasoning, syllabus)
- **Model**: Selected LLM (Gemini, Groq)
- **Response**: Final answer
- **Duration**: Total execution time

### Spans (Sub-operations)
Each trace contains spans for:
- **Governor**: Policy enforcement (scope, integrity checks)
- **Supervisor**: Intent routing and model selection
- **RAG**: Document retrieval from ChromaDB
- **LLM Calls**: Individual model invocations
- **Response Generation**: Final answer synthesis

### Metadata
- Retrieved context sources
- Governor approval/rejection reasons
- Embedding similarity scores
- Token usage per LLM call

## Using Langfuse UI

### View Traces
1. Go to http://localhost:3000
2. Click **"Traces"** in the sidebar
3. See all agent executions in real-time

### Filter Traces
- By user (student email)
- By intent (fast, coder, reasoning)
- By model (Gemini, Groq)
- By error status
- By date range

### Analyze Performance
- **Latency**: See which steps are slow
- **Token Usage**: Track LLM costs
- **Error Rate**: Monitor failures
- **User Activity**: See most active students

### Debug Issues
1. Click on any trace
2. Expand spans to see detailed logs
3. View input/output for each step
4. Check error messages and stack traces

## Production Considerations

### Langfuse Cloud (Optional)
If you want to use Langfuse Cloud instead of self-hosted:

1. Sign up at https://cloud.langfuse.com
2. Create a project
3. Get API keys
4. Update `.env`:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
   ```
5. Comment out `observer` and `langfuse_worker` in `docker-compose.yml`

### Data Retention
- **Local**: Data persists in Docker volumes (`postgres_data`, `clickhouse_data`)
- **Cloud**: 30-day retention on free tier, unlimited on paid plans

### Privacy
- Langfuse stores query text and responses
- Ensure compliance with student data privacy policies
- Consider anonymizing user IDs in production

## Troubleshooting

### "Langfuse not configured" Warning
- Check that `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set in `.env`
- Restart backend: `docker compose restart api_brain`

### "Connection refused" Error
- Ensure Langfuse services are running: `docker compose ps`
- Check observer logs: `docker compose logs observer`
- Verify health: `curl http://localhost:3000/api/public/health`

### Traces Not Appearing
- Wait 5-10 seconds for traces to flush
- Check backend logs: `docker compose logs api_brain`
- Verify API keys are correct
- Try running `backend/scripts/verify_langfuse.py`

### ClickHouse Errors
- Ensure `CLICKHOUSE_CLUSTER_ENABLED=false` in `docker-compose.yml`
- Restart services: `docker compose restart observer langfuse_worker`

## Resources
- **Langfuse Docs**: https://langfuse.com/docs
- **LangChain Integration**: https://langfuse.com/docs/integrations/langchain
- **Local Setup**: `backend/scripts/setup_langfuse.md`
- **Verification Script**: `backend/scripts/verify_langfuse.py`

## Next Actions
1. Complete manual setup (Steps 1-7 above)
2. Run verification script
3. Test with a few queries
4. Check traces in Langfuse UI
5. Proceed with frontend testing

