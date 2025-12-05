# Luminate AI Course Marshal - Testing Guide

## Overview
This guide walks you through testing the complete system: backend AI agent, frontend extension, and Langfuse observability.

## Prerequisites

### 1. Services Running
Ensure all Docker services are running:
```bash
docker compose ps
```

Expected services:
- ✅ `api_brain` (Backend API - port 8000)
- ✅ `memory_store` (ChromaDB - port 8001)
- ✅ `cache_layer` (Redis - port 6379)
- ✅ `observer` (Langfuse UI - port 3000)
- ✅ `langfuse_worker` (Langfuse background jobs)
- ✅ `langfuse_postgres` (Langfuse database)
- ✅ `clickhouse` (Langfuse analytics)
- ✅ `minio` (Langfuse storage)

### 2. Course Data Ingested
Verify ChromaDB has course data:
```bash
python3 backend/scripts/check_chroma_status.py
```

Expected output:
```
✅ ChromaDB collection exists: comp237_course_materials
✅ Collection has 219 documents
```

If empty, run:
```bash
python3 backend/scripts/ingest_course_data.py
```

### 3. Langfuse Configured
Verify Langfuse integration:
```bash
python3 backend/scripts/verify_langfuse.py
```

Expected output:
```
✅ Langfuse client initialized
✅ Trace created successfully
✅ Agent executed successfully
🎉 All tests passed!
```

## Frontend Testing

### Step 1: Build the Extension

The extension should be building in the background. Check the build output:
```bash
cd extension && npm run dev
```

Wait for:
```
✅ Ready in X.XXs
🔵 INFO   | View the extension at: chrome://extensions
```

### Step 2: Load Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Navigate to: `/Users/aazain/Documents/GitHub/luminate-ai/extension/build/chrome-mv3-dev`
5. Select the folder
6. The extension should now appear in your extensions list

### Step 3: Test Student Chat Interface

#### 3.1 Login as Student

1. Click the extension icon in Chrome toolbar
2. Click **"Open Side Panel"** or use the side panel button
3. Enter a student email: `test.student@my.centennialcollege.ca`
4. Click **"Send Magic Link"**
5. Check your email for the magic link (or check Supabase logs)
6. Click the magic link to authenticate

#### 3.2 Test Chat Functionality

**Test 1: Course Information Query**
- **Query**: "What is the course code for this class?"
- **Expected**: Should respond with "COMP 237" from the course outline
- **Check**: Response should cite sources (e.g., "[Source: COMP_237_COURSEOUTLINE.pdf]")

**Test 2: Syllabus Query**
- **Query**: "What are the learning outcomes for this course?"
- **Expected**: Should list the learning outcomes from the course outline
- **Check**: Should include specific outcomes like "Implement neural networks"

**Test 3: Assignment Query**
- **Query**: "When is Assignment 1 due?"
- **Expected**: Should provide the due date from the course schedule
- **Check**: Should not provide full solutions (Governor Law of Integrity)

**Test 4: Code Explanation**
- **Query**: "Explain how backpropagation works in neural networks"
- **Expected**: Should provide a conceptual explanation
- **Check**: Should route to "reasoning" intent, use Gemini model

**Test 5: Code Request (Should be Blocked)**
- **Query**: "Write the complete code for Assignment 1"
- **Expected**: Should be rejected by Governor
- **Check**: Response should explain academic integrity policy

**Test 6: Out-of-Scope Query (Should be Blocked)**
- **Query**: "What's the weather like today?"
- **Expected**: Should be rejected by Governor (Law of Scope)
- **Check**: Response should explain it only answers COMP 237 questions

#### 3.3 Verify Streaming

- **Check**: Messages should appear word-by-word (streaming)
- **Check**: Sources should appear after the main response
- **Check**: No full-page reloads or flickering

#### 3.4 Verify Langfuse Tracing

1. Open Langfuse UI: http://localhost:3000
2. Navigate to **"Traces"** tab
3. You should see traces for each query
4. Click on a trace to see:
   - **Governor** node (policy enforcement)
   - **Supervisor** node (intent routing)
   - **RAG** node (document retrieval)
   - **Generate** node (response synthesis)
5. Check trace metadata:
   - `user_email`: Should show student email
   - `query`: Should show the question
   - `intent`: Should show detected intent (fast, coder, reasoning, syllabus)
   - `model_selected`: Should show which LLM was used

### Step 4: Test Admin Dashboard

#### 4.1 Login as Admin

1. Logout from student account (if logged in)
2. Enter an admin email: `admin@centennialcollege.ca`
3. Click **"Send Magic Link"**
4. Authenticate via magic link

#### 4.2 Test System Health

1. Navigate to **"System Health"** tab in the side panel
2. Verify metrics display:
   - ✅ **ChromaDB Status**: Should show "Connected" with document count
   - ✅ **Redis Status**: Should show "Connected"
   - ✅ **Backend API**: Should show "Healthy"
   - ✅ **Langfuse**: Should show "Connected"

#### 4.3 Test File Upload

1. Navigate to **"Upload Materials"** tab
2. Click **"Choose File"**
3. Select a test PDF (e.g., a sample lecture slide)
4. Click **"Upload"**
5. Verify:
   - Upload progress indicator appears
   - Success message displays
   - File appears in the upload history

#### 4.4 Test ETL Job Monitoring

1. After uploading a file, check **"ETL Jobs"** tab
2. Verify job status:
   - **Pending**: Job is queued
   - **Processing**: Job is running
   - **Completed**: Job finished successfully
   - **Failed**: Job encountered an error (check logs)

3. Check ChromaDB status again:
   - Document count should increase after successful ETL

## Backend Testing

### Test 1: Direct API Call

Test the chat endpoint directly:

```bash
# Get a JWT token from Supabase (or use test_auth.py)
python3 backend/test_auth.py
```

Then test the chat endpoint:

```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is COMP 237?"}
    ]
  }'
```

Expected: SSE stream with text deltas and sources.

### Test 2: RAG Verification

```bash
python3 backend/verify_rag.py
```

Expected output:
```
✅ Agent response contains course code: COMP 237
✅ Agent response contains course title
✅ RAG is working correctly!
```

### Test 3: Coder Agent

```bash
python3 backend/scripts/verify_coder.py
```

Expected: Should generate Python code for the requested function.

## Performance Testing

### Response Time Benchmarks

- **Simple query** (e.g., "What is COMP 237?"): < 3 seconds
- **Complex query** (e.g., "Explain backpropagation"): < 10 seconds
- **Code generation**: < 15 seconds

### Streaming Latency

- **Time to first token**: < 1 second
- **Tokens per second**: > 20 tokens/sec

## Error Handling Testing

### Test 1: Invalid Email Domain

- **Action**: Try to login with `test@gmail.com`
- **Expected**: Error message: "Institutional Email Required"

### Test 2: Backend Offline

- **Action**: Stop backend (`docker compose stop api_brain`)
- **Expected**: Frontend shows connection error

### Test 3: ChromaDB Empty

- **Action**: Delete ChromaDB collection
- **Expected**: Agent responds but cites no sources

### Test 4: Rate Limiting (Future)

- **Action**: Send 100 requests in 1 minute
- **Expected**: Rate limit error after threshold

## Langfuse Analytics Testing

### Dashboards to Check

1. **Traces Dashboard**:
   - Total traces count
   - Average latency
   - Error rate
   - Top users

2. **Models Dashboard**:
   - Token usage by model
   - Cost per model
   - Model selection distribution

3. **Users Dashboard**:
   - Active users
   - Queries per user
   - Average session length

### Custom Filters

Test filtering traces by:
- **User**: Filter by student email
- **Intent**: Filter by "coder", "reasoning", "fast"
- **Model**: Filter by "gemini-flash", "groq-llama-70b"
- **Date**: Filter by today, last 7 days, etc.
- **Error**: Filter only failed traces

## Troubleshooting

### Extension Not Loading

1. Check build output: `cat terminals/24.txt`
2. Rebuild: `cd extension && npm run build`
3. Reload extension in Chrome

### Backend Not Responding

1. Check logs: `docker compose logs api_brain --tail 50`
2. Restart: `docker compose restart api_brain`
3. Check health: `curl http://localhost:8000/health`

### Langfuse Not Tracking

1. Check API keys in `backend/.env`
2. Restart backend: `docker compose restart api_brain`
3. Run verification: `python3 backend/scripts/verify_langfuse.py`

### ChromaDB Empty

1. Check collection: `python3 backend/scripts/check_chroma_status.py`
2. Re-ingest: `python3 backend/scripts/ingest_course_data.py`
3. Verify: Query should now return sources

## Success Criteria

### ✅ Backend

- [x] All Docker services running
- [x] ChromaDB populated with course data
- [x] RAG retrieval working
- [x] Governor enforcing policies
- [x] Supervisor routing intents correctly
- [x] Langfuse tracing all operations

### ✅ Frontend

- [x] Extension loads in Chrome
- [x] Student login works (@my.centennialcollege.ca)
- [x] Admin login works (@centennialcollege.ca)
- [x] Chat interface streams responses
- [x] Sources are displayed
- [x] Admin dashboard shows metrics
- [x] File upload works

### ✅ Integration

- [x] Frontend → Backend communication
- [x] Backend → ChromaDB retrieval
- [x] Backend → Langfuse tracing
- [x] Admin → ETL pipeline
- [x] End-to-end query flow

## Next Steps

After testing is complete:

1. **Document Issues**: Create GitHub issues for any bugs found
2. **Performance Tuning**: Optimize slow queries
3. **Feature Enhancements**: Add requested features
4. **Deployment**: Prepare for production deployment
5. **User Acceptance Testing**: Get feedback from real students

## Support

For issues or questions:
- Check logs: `docker compose logs [service_name]`
- Review documentation: `docs/`
- Check Langfuse traces: http://localhost:3000
- Verify backend health: http://localhost:8000/health










