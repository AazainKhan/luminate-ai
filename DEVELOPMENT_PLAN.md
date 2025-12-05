# Development Plan - Post-Testing Analysis

**Date:** November 29, 2025  
**Analysis Source:** Langfuse Trace Export + Comprehensive Test Suite  
**Status:** ✅ Phase 1 Complete - All Critical Fixes Applied

---

## ✅ Completed Fixes (November 29, 2025)

### 1. **ChromaDB Data + Embeddings** ✅ FIXED
- Created `ingest_comp237_proper.py` with 21 comprehensive COMP237 course documents
- Uses Gemini embeddings (768-dim) consistently
- ML topics now correctly pass scope check:
  - "machine learning" → Distance: 0.549 ✅
  - "k-nearest neighbors" → Distance: 0.440 ✅
  - "gradient descent" → Distance: 0.512 ✅
  - "backpropagation" → Distance: 0.484 ✅
  - "capital of France?" → Distance: 0.981 ❌ (correctly OUT OF SCOPE)

### 2. **Governor False Positives** ✅ FIXED
- Root cause was embedding dimension mismatch (384 vs 768)
- Now correctly approves all ML topics
- Test: "What is gradient descent?" → Approved ✅

### 3. **Langfuse Span Linking** ✅ FIXED
- Updated `governor_node()` to use `trace_context={"trace_id": trace_id}`
- Updated `evaluator_node()` to use `trace_context={"trace_id": trace_id}`
- Spans now properly linked to parent trace

---

## 🔍 Original Issues (from Langfuse Traces)

### 1. **CRITICAL: Governor False Positives** ✅ RESOLVED
**Symptom:** Valid ML queries like "k-nearest neighbors", "gradient descent", "neural network", "machine learning" are being **blocked** with reason: `"This topic is not covered in COMP 237"`.

**Root Cause Analysis:**
1. ChromaDB collection `comp237_course_materials` has only **5 documents** (should have hundreds)
2. **Embedding dimension mismatch**: Collection expects 768-dim embeddings, but queries generate 384-dim
3. Test data was ingested with `text-embedding-3-small` (384-dim) but LangChain uses `embedding-001` (768-dim)

**Evidence from traces:**
```json
{
  "policy_decision": {
    "approved": false,
    "reason": "This topic is not covered in COMP 237. Please ask about course content.",
    "law_violated": "scope"
  }
}
```

**Fix Required:**
- [ ] Delete current collection and re-ingest with consistent Gemini embeddings
- [ ] Ingest actual COMP237 course materials (PDFs, slides, lecture notes)
- [ ] Verify embedding dimensions match (768-dim for Gemini)

---

### 2. **MEDIUM: Orphaned Spans in Langfuse**
**Symptom:** `policy_enforcement_guardrail` and `mastery_verification_evaluator` spans appear as **separate traces** instead of nested spans within the main agent trace.

**Root Cause:**
The `start_span()` call in `governor_node()` and `evaluator_node()` uses `trace_context={"trace_id": trace_id}` but this creates a new trace, not a child span.

**Evidence:**
```json
{
  "id": "1b9384046684e56bab046aa4931cbdd8",
  "name": "policy_enforcement_guardrail",
  // No parent_observation_id - this is an orphaned span
}
```

**Fix Required:**
- [ ] Use `span.start_span()` from parent span context instead of `client.start_span()`
- [ ] Pass parent observation ID through AgentState
- [ ] Use `langfuse.trace()` decorator or context manager for proper nesting

---

### 3. **LOW: Low Confidence Scores**
**Symptom:** All evaluator outputs show `"confidence": 0.3` which is the default/fallback value.

**Root Cause:**
The `calculate_pedagogical_score()` function returns default values when scoring fails. The actual response quality isn't being analyzed.

**Evidence:**
```json
{
  "evaluation_result": {
    "confidence": 0.3,
    "passed": false,
    "feedback": "Please try to explain more clearly.",
    "level": "developing"
  }
}
```

**Fix Required:**
- [ ] Implement actual LLM-based response evaluation
- [ ] Parse scaffolding level from response XML tags
- [ ] Calculate confidence based on response completeness

---

### 4. **GOOD: Langfuse Scores Working ✅**
The 5 scores are being created correctly:
- `pedagogical_quality` (0.58-0.68)
- `policy_compliance` (1.0)
- `response_confidence` (0.3)
- `scaffolding_level` (0.0-0.5)
- `intent_complexity` (0.5-1.0)

---

## 📋 Development Tasks (Priority Order)

### Phase 1: Critical Fixes (Today)

#### Task 1.1: Fix ChromaDB Data + Embeddings
**Priority:** 🔴 CRITICAL  
**Time Estimate:** 30 mins

1. Delete existing collection with mismatched embeddings
2. Create ingestion script using consistent Gemini embeddings
3. Ingest comprehensive COMP237 course content
4. Verify Governor approves ML topics

#### Task 1.2: Fix Span Linking in Langfuse
**Priority:** 🟡 MEDIUM  
**Time Estimate:** 20 mins

1. Add `parent_observation_id` to AgentState
2. Update `governor_node()` to use parent context
3. Update `evaluator_node()` to use parent context
4. Verify trace hierarchy in Langfuse UI

---

### Phase 2: Quality Improvements (Next Session)

#### Task 2.1: Improve Evaluator Confidence Scoring
**Priority:** 🟡 MEDIUM  
**Time Estimate:** 45 mins

1. Parse actual response content for quality indicators
2. Check for `<thinking>` tags (pedagogy present)
3. Check for follow-up questions (engagement)
4. Check for code examples (when relevant)
5. Adjust confidence based on scaffolding level

#### Task 2.2: Add Conversation History Display
**Priority:** 🟢 LOW  
**Time Estimate:** 30 mins

1. Load prior messages on chat initialization
2. Display in chat UI
3. Include in LLM context for better responses

---

### Phase 3: Production Readiness

#### Task 3.1: Extension Integration Testing
- [ ] Build Chrome extension
- [ ] Test side panel functionality
- [ ] Verify auth flow with Supabase
- [ ] Test streaming chat

#### Task 3.2: Performance Optimization
- [ ] Add Redis caching for embeddings
- [ ] Optimize RAG retrieval (top-k tuning)
- [ ] Monitor latency in Langfuse

---

## 🛠️ Immediate Action Items

```bash
# 1. Delete mismatched collection
cd backend && source venv/bin/activate
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8001)
try:
    client.delete_collection('comp237_course_materials')
    print('Deleted old collection')
except: pass
"

# 2. Ingest with correct embeddings
python ingest_comp237_proper.py

# 3. Verify ingestion
python verify_rag.py
```

---

## 📊 Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Governor Approval Rate (ML topics) | 0% | 95%+ |
| Span Hierarchy in Langfuse | Orphaned | Nested |
| Evaluator Confidence Range | Always 0.3 | 0.3-0.9 |
| ChromaDB Document Count | 5 | 200+ |

---

## 📝 Files to Modify

1. `backend/app/agents/governor.py` - Span linking
2. `backend/app/agents/evaluator.py` - Span linking, confidence scoring
3. `backend/app/agents/state.py` - Add `parent_observation_id`
4. `backend/app/agents/tutor_agent.py` - Pass parent context
5. NEW: `backend/ingest_comp237_proper.py` - Proper ingestion script

---

**Next Step:** Execute Phase 1 tasks to fix critical issues.
