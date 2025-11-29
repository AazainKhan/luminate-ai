# Luminate AI - Comprehensive Test Architecture

## Test Categories & Status

### 1. Infrastructure Tests (Docker/Services)
- [ ] Docker services health checks
- [ ] ChromaDB connectivity & operations
- [ ] Redis connectivity
- [ ] Langfuse/ClickHouse observability
- [ ] PostgreSQL (Langfuse) health
- [ ] MinIO storage health

### 2. Backend API Tests
- [ ] Health endpoint
- [ ] Authentication flow (dev bypass + production JWT)
- [ ] Chat stream endpoint
- [ ] Admin endpoints
- [ ] Code execution endpoint

### 3. Database Tests (Supabase)
- [ ] User authentication flow
- [ ] Session/mastery table operations
- [ ] Chat history storage
- [ ] User preferences storage

### 4. RAG Pipeline Tests (ChromaDB)
- [ ] Document embedding
- [ ] Semantic search
- [ ] Context retrieval quality
- [ ] Course-scoped queries

### 5. LangGraph Agent Pipeline Tests
- [ ] Governor node (3 laws enforcement)
- [ ] Supervisor model routing
- [ ] RAG agent integration
- [ ] Syllabus agent
- [ ] Response generator
- [ ] Evaluator/mastery tracking
- [ ] State flow correctness

### 6. Educational Methodology Tests
- [ ] Socratic questioning patterns
- [ ] No direct answer for assignments (Law 2)
- [ ] Mastery verification (Law 3)
- [ ] Scope enforcement (Law 1 - COMP 237 only)
- [ ] Adaptive difficulty

### 7. Observability Tests (Langfuse)
- [ ] Trace creation
- [ ] Span hierarchy
- [ ] Metrics collection
- [ ] Session tracking

### 8. E2E UI Tests (Playwright)
- [ ] Side panel rendering
- [ ] Nav rail interactions
- [ ] Chat functionality
- [ ] Theme switching
- [ ] User profile menu
- [ ] Folder/chat management

### 9. Generative UI Tests
- [ ] ThinkingAccordion rendering
- [ ] QuizCard interaction
- [ ] CodeBlock with execution
- [ ] Streaming message display

## Test Execution Strategy

### Parallel Execution
- Backend tests: pytest with xdist (parallel)
- E2E tests: Playwright with sharding (can't use workers due to extension)
- Integration tests: Sequential for state dependencies

### Logging & Reporting
- Structured JSON logs for programmatic analysis
- Screenshot capture on failure
- HTML reports for visual review
- Trace collection for debugging

## Running Tests

```bash
# All backend tests
cd backend && pytest tests/ -v --tb=short

# All E2E tests with sharding
cd extension && npx playwright test --shard=1/3

# Specific category
npx playwright test --grep "@backend"
npx playwright test --grep "@rag"
npx playwright test --grep "@agent"
```
