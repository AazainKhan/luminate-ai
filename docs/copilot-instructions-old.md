# Luminate AI Course Marshal - Backend Development Instructions

## Project Vision & Philosophy

For ground info on agents, tips, and best practices, refer to /docs/agent-info.md and /docs/agentic_tutor_info.md

All frontend in docs/vercel-ai-sdk-docs.txt

This is an **agentic AI tutoring platform** for COMP 237 (Introduction to AI) at Centennial College. The critical distinction: **this is NOT ChatGPT in a box**. The agent must exhibit true pedagogical intelligence:

- **Reasoning → Strategy → Action**: Before responding, the agent must analyze student knowledge, select teaching strategy, then execute
- **Adaptive not Generic**: Every response adapts to the student's level, not a templated script
- **Progressive Mastery**: Guide students up Bloom's Taxonomy (Remember → Understand → Apply → Analyze → Evaluate → Create)
- **Memory-Aware**: Build and use student knowledge graphs, mastery scores, and misconception history

---

## Architecture Deep Dive

### The LangGraph Agent Pipeline (`backend/app/agents/`)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐    ┌───────────┐
│  Governor   │───▶│  Supervisor │───▶│  Specialized Agents     │───▶│ Evaluator │
│ (3 Laws)    │    │  (Router)   │    │  ┌─────────────────┐    │    │ (Mastery) │
│             │    │             │    │  │ Pedagogical     │    │    │           │
│ Scope       │    │ Intent      │    │  │ Tutor (Socratic)│    │    │ Scoring   │
│ Integrity   │    │ Detection   │    │  ├─────────────────┤    │    │ Langfuse  │
│ Mastery     │    │ Model       │    │  │ Math Agent      │    │    │           │
│             │    │ Selection   │    │  │ (Derivations)   │    │    │           │
│             │    │             │    │  ├─────────────────┤    │    │           │
│             │    │             │    │  │ General Agent   │    │    │           │
│             │    │             │    │  │ (Tools + RAG)   │    │    │           │
│             │    │             │    │  └─────────────────┘    │    │           │
└─────────────┘    └─────────────┘    └─────────────────────────┘    └───────────┘
```

### Node-by-Node Breakdown

#### 1. Governor (`governor.py`) - Policy Engine
Enforces 3 laws **before** any agent action proceeds:

| Law | Purpose | Implementation |
|-----|---------|----------------|
| **Law 1: Scope** | Only COMP 237 topics | ChromaDB distance < 0.80 threshold |
| **Law 2: Integrity** | No full assignment solutions | Keyword detection for "complete solution", "do my assignment" |
| **Law 3: Mastery** | Verify understanding | Deferred to Evaluator node |

**When modifying:** Never relax integrity checks. Scope threshold (0.80) was empirically tuned.

#### 2. Supervisor (`supervisor.py`) - Intelligent Router
Hybrid routing: regex patterns first, LLM fallback when confidence < 0.6

**Routing Priority Order:**
1. **coder**: Code-specific keywords (python, implement, debug)
2. **syllabus_query**: Course info/logistics (BEFORE tutor to prevent verbose responses)
3. **fast_info**: Quick factual questions
4. **tutor_override**: Strong confusion signals (always routes to tutor)
5. **explain**: Simple "explain X" requests (medium-length response)
6. **math vs tutor**: Disambiguated by specificity
7. **fast**: Default fallback

| Intent | Model | Trigger Patterns | Response Style |
|--------|-------|------------------|----------------|
| `syllabus_query` | `gemini-flash` | "what is this course", "topics covered", "COMP 237" | **Concise (2-4 sentences)** |
| `explain` | `gemini-flash` | "explain X", "what is a/the X" (without confusion) | **Medium (3-5 paragraphs)** |
| `tutor` | `gemini-tutor` (temp=0.9) | "confused", "don't understand", "struggling", "need help" | Full Socratic scaffolding |
| `math` | `gemini-flash` | "derive", "formula", "step-by-step", "proof" | Detailed derivation |
| `coder` | `groq-llama-70b` | "python", "code", "implement", "debug" | Code + explanation |
| `fast` | `gemini-flash` | "briefly", "quick answer", or default | **Concise (1-3 sentences)** |

**Critical Routing Rules:**
- `syllabus_query` patterns are checked BEFORE `tutor` to prevent verbose Socratic responses for course info questions
- **NEW: `explain` intent** handles "explain X" without full Socratic scaffolding (medium-length response)
- `tutor_override` patterns ("confused", "struggling") ALWAYS route to `tutor` even if math keywords present
- Tutor now requires explicit confusion signals, not just "explain"
- "explain gradient descent" → `explain` (NOT `tutor`) - concise explanation
- "I don't understand gradient descent" → `tutor` - full Socratic scaffolding
- "what is this course about?" → `syllabus_query` (NOT `tutor`)

#### 3. Pedagogical Tutor (`pedagogical_tutor.py`) - Socratic Agent
This is the CORE teaching agent. Implements research-backed pedagogy:

**Scaffolding Levels (Zone of Proximal Development):**
- `hint`: Minimal guidance, probing questions only
- `guided`: Partial support, "we do" together
- `explained`: Full explanation with examples
- `demonstrated`: Worked example, "I do" first

**Response Structure (MUST follow):**
```xml
<thinking>
[Assess student level]
[Plan scaffolding strategy]
[Select approach: socratic/direct/exploratory]
</thinking>

**Activation:** [Connect to prior knowledge or analogy]
**Exploration:** [Socratic questions]
**Guidance:** [Progressive hints]
**Challenge:** [Closing question to test understanding]
```

**Confusion Detection:** Regex patterns score confusion signals (0.0-1.0). Higher scores → more scaffolding.

#### 4. Math Agent (`math_agent.py`) - Step-by-Step Derivations
Specialized for AI mathematics:

**Topic Detection:**
- `gradient_descent`: learning rate, optimization, minimize
- `backpropagation`: chain rule, error propagation
- `loss_functions`: MSE, cross-entropy, cost function
- `probability`: Bayes, conditional, prior/posterior
- `linear_algebra`: matrix, vector, transpose

**Response Structure:**
```xml
<thinking>
[Identify math concept]
[Plan intuition-first approach]
[Visual analogy to use]
</thinking>

**Understanding:** [Clarify the goal]
**Connection:** [Link to known concepts]
**Guidance:** [Step-by-step with LaTeX]
**Verification:** [How to check the answer]
```

#### 5. Evaluator (`evaluator.py`) - Quality & Mastery
Creates Langfuse scores after EVERY interaction:

| Score | Type | Purpose |
|-------|------|---------|
| `pedagogical_quality` | 0-1 | How well response teaches |
| `policy_compliance` | 0/1 | Governor approved |
| `response_confidence` | 0-1 | Evaluator confidence |
| `scaffolding_level` | 0-1 | Scaffolding used |
| `intent_complexity` | 0-1 | Routing complexity |

### State Schema (`state.py`) - The Contract

**CRITICAL: Never break the AgentState contract.** All nodes read/write to this shared state.

Key fields for pedagogical behavior:

```python
class AgentState(TypedDict):
    # User context
    user_id: Optional[str]
    user_email: Optional[str]
    conversation_history: Optional[List[dict]]  # Prior messages
    
    # Routing
    intent: Optional[str]  # "tutor", "math", "coder", "syllabus_query", "fast"
    model_selected: Optional[str]
    
    # Pedagogical state (THE KEY FIELDS)
    scaffolding_level: Optional[ScaffoldingLevel]  # "hint", "guided", "explained", "demonstrated"
    student_confusion_detected: bool
    thinking_steps: Optional[List[ThinkingStep]]  # Visible reasoning
    bloom_level: Optional[BloomLevel]  # "remember" → "create"
    pedagogical_approach: Optional[PedagogicalApproach]  # "socratic", "direct", "scaffolded"
    
    # RAG
    retrieved_context: List[dict]
    context_sources: List[dict]
```

---

## What The Agent SHOULD Do (Target Behavior)

### 1. Immediate Micro-Diagnostic
Before teaching, ask 1-2 quick checks:
- "Do you want a quick answer or deeper breakdown?"
- "Have you covered supervised learning in class?"
- "What do you already know about this?"

### 2. Multi-Mode Response
Offer depth levels:
- **Mode A (Quick):** 5-second answer. Classification → category. Regression → number.
- **Mode B (Intermediate):** Short examples + decision rule
- **Mode C (Deep Dive):** Loss functions, metrics, code examples

### 3. Dynamic Scaffolding
Select based on student signals:
- High confusion → `demonstrated` (worked example)
- Medium confusion → `explained` (full walkthrough)  
- Low confusion → `guided` (partial support)
- No confusion → `hint` (Socratic questions only)

### 4. Misconception Detection
If student answers incorrectly:
```
Student: "Regression outputs categories"
Tutor: "I notice a common misconception! Regression actually outputs 
continuous numbers (like 0.73 or 42.5). Classification outputs categories.
Let me ask: if you're predicting house prices, which would you use?"
```

### 5. Course Material Retrieval
ALWAYS pull from ChromaDB COMP237 collection:
- Use student's course terminology
- Cite specific sources: `[From: module3_slides.pdf, Page 12]`
- Match examples to their curriculum

### 6. Mastery Tracking Integration
Each interaction should:
1. Check `student_mastery` table for prior scores
2. Adjust scaffolding based on mastery (high mastery → less scaffolding)
3. Update mastery after evaluation
4. Track misconceptions in `interactions` table

### 7. Progressive Bloom's Levels
After explanation:
1. **Apply:** "Try this mini-exercise..."
2. **Analyze:** "Compare these two approaches..."
3. **Evaluate:** "Which method would you choose for...?"
4. **Create:** "Design a small dataset for..."

### 8. Auto-Graded Practice
End responses with testable questions:
```xml
<quiz>
{
  "question": "Which is a classification problem?",
  "options": ["Predicting temperature", "Predicting spam/not-spam", "Predicting stock price"],
  "correct": 1,
  "explanation": "Spam detection has discrete categories (spam/not-spam)"
}
</quiz>
```

---

## Current Gaps To Address

### Gap 1: Reasoning is Static ✅ ADDRESSED
**Current:** `<thinking>` block dumps justification, doesn't drive action
**Status:** FIXED - Knowledge graph now suggests next concepts
**Implementation:**
1. ✅ Created `knowledge_graph.py` with concept relationships
2. ✅ `get_next_concepts()` suggests topics based on current mastery
3. ✅ Response now includes "📚 What to learn next:" suggestions

### Gap 2: No Personalization ✅ ADDRESSED
**Status:** FIXED in `pedagogical_tutor.py`
**Implementation:**
1. ✅ Added `get_student_mastery()` function to fetch from Supabase
2. ✅ Mastery is now passed to `select_scaffolding_level()`
3. ✅ Scaffolding adjusts based on prior mastery (>0.8=hint, <0.3=demonstrated)

### Gap 3: Missing Mastery Integration ✅ ADDRESSED
**Status:** FIXED - Full loop now works
**Implementation:**
1. ✅ `pedagogical_tutor.py` queries mastery before selecting scaffolding
2. ✅ `evaluator.py` updates mastery after each interaction
3. ✅ Concept detection maps queries to 10 COMP237 concepts

### Gap 4: No Short-Form Control ✅ ADDRESSED
**Status:** FIXED in `supervisor.py` and `tutor_agent.py`
**Implementation:**
1. ✅ `fast_info` intent patterns detect "briefly", "quick", "one sentence"
2. ✅ `syllabus_query` and `fast` intents use concise prompts
3. ✅ Template: "Quick: [answer]. Want me to explain more?"
4. ✅ **NEW: `explain` intent** - medium-length explanations (3-5 paragraphs) for "explain X" queries without full Socratic scaffolding
5. ✅ Prompts now use "MUST call `retrieve_context` tool FIRST" for reliable tool invocation

### Gap 5: Misconception Memory ✅ ADDRESSED
**Status:** FIXED in `evaluator.py`
**Implementation:**
1. ✅ Added `MISCONCEPTION_PATTERNS` with 5 common AI/ML misconceptions
2. ✅ `detect_misconceptions()` scans queries for misconception signals
3. ✅ Misconceptions stored in `interactions.metadata` for future reference

### Gap 6: Visual Support ✅ ADDRESSED
**Current:** ASCII diagrams and Mermaid.js charts embedded in responses
**Status:** FIXED in `visual_diagrams.py` and `pedagogical_tutor.py`
**Implementation:**
1. ✅ Created `backend/app/agents/visual_diagrams.py` with ASCII_DIAGRAMS (10 concepts) and MERMAID_DIAGRAMS (5 concepts)
2. ✅ `get_diagram_for_detected_concept()` maps detected concepts to diagram keys
3. ✅ `format_diagram_for_response()` formats diagrams with emoji headers
4. ✅ Pedagogical tutor integrates diagrams after explanation for `explained`/`demonstrated` scaffolding
5. ✅ Concepts with visual support: neural_network, gradient_descent, backpropagation, decision_tree, classification_vs_regression, kmeans_clustering, confusion_matrix, overfitting, activation_functions, train_test_split

### Gap 7: Diagnostic Micro-Questions ✅ ADDRESSED
**Current:** No pre-assessment before teaching
**Status:** FIXED in `pedagogical_tutor.py`
**Implementation:**
1. ✅ Added `diagnostic_asked` and `user_depth_preference` to AgentState
2. ✅ `should_ask_diagnostic()` checks if diagnostic is needed
3. ✅ Asks "quick answer or deeper breakdown?" before teaching
4. ✅ `detect_depth_preference()` parses user's choice
3. "Have you covered supervised learning in class?"

---

## Development Workflows

### Testing Agent Changes
```bash
cd backend

# Quick test
python -c "from app.agents.tutor_agent import run_agent; print(run_agent('What is backpropagation?'))"

# Verbose test with full state
python test_agent_stream.py

# Full test suite (22 tests)
pytest test_comprehensive.py -v
```

### Frontend Testing with Playwright (REQUIRED for UI Changes)

**CRITICAL: After any backend or frontend change that affects the UI, run Playwright tests to verify the user experience.**

#### Setup (Terminal 1 - Backend)
```bash
cd /Users/aazain/Documents/GitHub/luminate-ai
docker compose up -d  # Ensure all services running
```

#### Setup (Terminal 2 - Frontend Dev Server)
```bash
cd /Users/aazain/Documents/GitHub/luminate-ai/extension
pnpm dev  # Start extension dev server
```

#### Using Playwright MCP Tools for Testing

**Step 1: Initialize browser and navigate to extension**
```python
# Use mcp_playwright_init-browser to start
# Then navigate to extension sidepanel
```

**Step 2: Get page context to understand current state**
```python
# Use mcp_playwright_get-context to see DOM structure
# This helps identify elements for interaction
```

**Step 3: Execute test interactions with proper timing**
```python
# Use mcp_playwright_execute-code with PROPER WAIT TIMES
# Example: Testing a chat interaction

async function run(page) {
  // Wait for page to be fully loaded
  await page.waitForLoadState('networkidle');
  
  // Find and fill the prompt input
  const input = await page.locator('[data-testid="prompt-input"], textarea');
  await input.fill('What is gradient descent?');
  
  // Click send button
  const sendBtn = await page.locator('[data-testid="send-button"], button[type="submit"]');
  await sendBtn.click();
  
  // CRITICAL: Wait for streaming response to complete
  // AI responses take time - wait for loading indicator to disappear
  await page.waitForTimeout(3000);  // Initial thinking time
  
  // Wait for response to appear
  await page.waitForSelector('[data-testid="assistant-message"], .assistant-message', {
    timeout: 30000  // 30 seconds for full response
  });
  
  // Additional wait for streaming to finish
  await page.waitForTimeout(2000);
  
  return { status: 'completed', timestamp: Date.now() };
}
```

**Step 4: Capture screenshot for verification**
```python
# Use mcp_playwright_get-screenshot to capture current state
# Review screenshot to verify:
# - Response rendered correctly
# - No error states visible
# - UI elements properly styled
# - Loading states completed
```

#### Timing Guidelines for AI Responses

| Action | Minimum Wait Time | Reason |
|--------|------------------|--------|
| Page load | `waitForLoadState('networkidle')` | Ensure all assets loaded |
| After sending message | 3-5 seconds | Backend processing, LLM thinking |
| Streaming response | 10-30 seconds | Full response generation |
| After response complete | 2 seconds | UI updates, animations |
| Between test steps | 1 second | Prevent race conditions |

#### Example: Full E2E Test Flow

```javascript
// Complete test sequence using mcp_playwright_execute-code
async function run(page) {
  const results = [];
  
  // Step 1: Navigate and wait
  await page.goto('chrome-extension://YOUR_EXTENSION_ID/sidepanel.html');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  results.push('Page loaded');
  
  // Step 2: Check auth state
  const authButton = await page.locator('[data-testid="sign-in-button"]');
  if (await authButton.isVisible()) {
    results.push('User not authenticated - need to sign in first');
    return { results, needsAuth: true };
  }
  
  // Step 3: Send a test query
  const input = await page.locator('textarea, [data-testid="prompt-input"]');
  await input.fill('briefly, what is backpropagation?');
  await page.waitForTimeout(500);
  
  // Step 4: Submit
  await page.keyboard.press('Enter');
  results.push('Message sent');
  
  // Step 5: Wait for response with generous timeout
  await page.waitForTimeout(5000);  // Initial wait
  
  // Step 6: Check for response
  const messages = await page.locator('.message, [data-role="assistant"]').count();
  results.push(`Found ${messages} messages`);
  
  // Step 7: Wait for streaming to complete
  await page.waitForTimeout(10000);
  
  return { results, success: messages > 0 };
}
```

#### Running Playwright E2E Test Suite

```bash
cd /Users/aazain/Documents/GitHub/luminate-ai/extension

# Run all E2E tests
pnpm test:e2e

# Run specific test file
pnpm test:e2e test/e2e/chat.spec.ts

# Run with UI mode for debugging
pnpm test:e2e --ui

# Run with headed browser (visible)
pnpm test:e2e --headed
```

#### Screenshot Verification Checklist

After capturing a screenshot with `mcp_playwright_get-screenshot`, verify:

1. **Response Content**
   - [ ] AI response is visible and readable
   - [ ] Response follows expected format (Quick answer vs Socratic)
   - [ ] No error messages or red error states

2. **UI State**
   - [ ] Loading spinners are gone
   - [ ] Send button is re-enabled
   - [ ] Input field is cleared or ready for next input

3. **Styling**
   - [ ] Dark/light mode renders correctly
   - [ ] Code blocks have syntax highlighting
   - [ ] Markdown is rendered (not raw)

4. **Responsive**
   - [ ] Content fits within sidepanel width
   - [ ] No horizontal scrollbars unexpectedly
   - [ ] Text is readable size

### Modifying Agent Behavior

1. **Add new state field:**
   - Edit `state.py` → add to `AgentState` TypedDict
   - Update nodes that need to read/write it
   
2. **Change scaffolding logic:**
   - Edit `pedagogical_tutor.py` → `select_scaffolding_level()`
   - Adjust thresholds or add new signals

3. **Add new intent:**
   - Edit `supervisor.py` → add patterns to `INTENT_PATTERNS`
   - Add routing in `route_by_intent()` in `tutor_agent.py`
   - Create new agent node if needed

4. **Modify prompts:**
   - Check Langfuse prompt management first (`socratic-tutor-prompt`)
   - Fallback prompts are in agent files

### Prompt Management
Prompts are managed via Langfuse:
- `socratic-tutor-prompt`: Pedagogical tutor system prompt
- `math-agent-prompt`: Math agent system prompt

To update: Langfuse dashboard → Prompts → Edit → Deploy

---

## File Reference (Backend Focus)

| File | Purpose | When to Modify |
|------|---------|----------------|
| `tutor_agent.py` | LangGraph orchestration | Adding nodes, changing flow |
| `state.py` | Shared state schema | Adding new agent capabilities |
| `governor.py` | Policy enforcement | Adjusting scope/integrity rules |
| `supervisor.py` | Intent routing | Adding intents, changing models |
| `pedagogical_tutor.py` | Socratic teaching | Improving pedagogy |
| `math_agent.py` | Math derivations | Math-specific improvements |
| `evaluator.py` | Quality scoring | Mastery integration |
| `tools.py` | RAG + Syllabus tools | Adding new tools |
| `chat.py` | Streaming endpoint | API changes |
| `mastery.py` | Mastery CRUD | Student progress tracking |

---

## Integration Points

### External Services
- **Supabase**: Auth + PostgreSQL (mastery tables, chat history)
- **ChromaDB**: Vector store (768-dim Gemini embeddings)
- **E2B**: Code execution sandbox
- **Langfuse**: Observability + prompt management

### Database Tables
```sql
student_mastery(user_id, concept_tag, mastery_score, decay_factor, last_assessed_at)
interactions(student_id, type, concept_focus, outcome, intent, agent_used, scaffolding_level)
chats(id, user_id, title)
messages(id, chat_id, role, content, metadata)
```

---

## Common Pitfalls

1. **Breaking AgentState:** Always add fields to `state.py` first
2. **Bypassing Governor:** Never skip policy checks for "convenience"
3. **Ignoring mastery:** Check mastery table before scaffolding decisions
4. **Generic responses:** Always inject course-specific context
5. **Monolithic prompts:** Use structured sections (Activation/Exploration/Guidance/Challenge)
6. **Missing citations:** ALWAYS cite retrieved sources
7. **Infinite loops:** Check `should_continue()` conditions after adding nodes

---

## Post-Change Validation Checklist

**CRITICAL: After ANY code change, verify the full system works end-to-end.** Don't assume isolated changes are safe.

### 1. Docker Services Health Check
```bash
# Check all containers are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected: api_brain, memory_store, redis, langfuse-web, langfuse-worker, 
#           clickhouse, postgres, minio - all "Up"
```

### 2. ChromaDB Data Verification
```bash
cd backend

# Test RAG retrieval is working
python -c "
from app.rag.langchain_chroma import get_langchain_chroma_client
client = get_langchain_chroma_client()
results = client.similarity_search_with_score('What is backpropagation?', k=3)
print(f'Retrieved {len(results)} documents')
for doc, score in results:
    print(f'  Score: {score:.3f} | Source: {doc.metadata.get(\"source_file\", \"unknown\")}')
"

# Expected: 3 documents with scores < 0.8, from COMP237 materials
# If empty or scores > 0.8: re-run ingestion (python 01_ingest_comp237.py)
```

### 3. Redis Connection Pooling Verification
```bash
cd backend

# Test Redis with connection pooling (required for production)
python -c "
import redis

# Use connection pool (REQUIRED - don't create single connections)
pool = redis.ConnectionPool(
    host='localhost', 
    port=6379, 
    password='myredissecret',
    max_connections=10,
    health_check_interval=30  # Auto-heal dead connections
)
r = redis.Redis(connection_pool=pool)

# Test connection
print(f'Redis ping: {r.ping()}')

# Test set/get
r.set('test_key', 'test_value', ex=60)
print(f'Redis get: {r.get(\"test_key\")}')

# Check active connections
print(f'Pool: {pool.connection_kwargs}')
"

# Expected: True, b'test_value', pool details
# If connection refused: docker-compose up -d redis
```

### 4. Langfuse Tracing Verification
```bash
cd backend

# Test Langfuse captures traces properly
python -c "
from app.observability import get_langfuse_client, flush_langfuse

client = get_langfuse_client()
if not client:
    print('ERROR: Langfuse client not initialized')
    exit(1)

# Create test trace
trace = client.trace(
    name='test-trace-verification',
    metadata={'test': True}
)

# Create test span
span = trace.span(name='test-span')
span.end()

# Create test score
client.score(
    trace_id=trace.id,
    name='test-score',
    value=1.0
)

flush_langfuse()
print(f'✅ Trace created: {trace.id}')
print('Check Langfuse UI: http://localhost:3000')
"

# Expected: Trace ID printed, visible in Langfuse dashboard
# If errors: Check LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in .env
```

**Langfuse LangChain Integration Pattern:**
```python
# Correct way to pass Langfuse handler to LangGraph
from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler()
result = agent.invoke(state, config={"callbacks": [langfuse_handler]})

# For streaming with trace attributes:
result = chain.invoke(
    {"input": query},
    config={
        "callbacks": [langfuse_handler],
        "metadata": {
            "langfuse_user_id": user_id,
            "langfuse_session_id": session_id,
            "langfuse_tags": ["tutor", "comp237"]
        }
    }
)
```

### 5. Supabase Database Verification
```bash
# Check table row counts and identify empty tables
# Using Supabase MCP or SQL Editor:

SELECT 'chats' as table_name, COUNT(*) as rows FROM chats
UNION ALL SELECT 'concepts', COUNT(*) FROM concepts
UNION ALL SELECT 'folders', COUNT(*) FROM folders
UNION ALL SELECT 'interactions', COUNT(*) FROM interactions
UNION ALL SELECT 'messages', COUNT(*) FROM messages
UNION ALL SELECT 'student_mastery', COUNT(*) FROM student_mastery;
```

**Current Table Status & Action Plan:**

| Table | Status | Purpose | Action Required |
|-------|--------|---------|-----------------|
| `chats` | ✅ Has data | Chat sessions | None |
| `messages` | ✅ Has data | Chat messages | None |
| `folders` | ✅ Has data | Chat organization | None |
| `interactions` | ✅ WIRED | Learning analytics | Evaluator logs interactions (requires real user) |
| `student_mastery` | ✅ WIRED | Mastery scores | Evaluator updates mastery (requires real user) |
| `mastery_history` | ✅ NEW | Mastery score changes over time | Auto-populated |
| `learning_sessions` | ✅ NEW | Groups interactions by session | Auto-populated |

**Note:** The old `concepts` table was REMOVED (Dec 2025). Concept hierarchy is now managed by:
- Neo4j/In-Memory Graph (`app/rag/graph_rag.py`)
- In-memory `CONCEPT_UNLOCKS` / `CONCEPT_NAMES` (`app/agents/knowledge_graph.py`)
- `CONCEPT_PATTERNS` for detection (`app/agents/evaluator.py`)

**Database Constraints:**
- `interactions.outcome`: Must be one of `'correct', 'incorrect', 'confusion_detected', 'passive_read'`
- `interactions.scaffolding_level`: Must be one of `'hint', 'example', 'guided', 'explain', 'explained', 'demonstrated', 'activation', 'socratic', 'verification', NULL`
- `student_id` foreign key: ✅ DROPPED - Now allows test UUIDs (no FK constraint)

### 6. End-to-End Agent Test
```bash
# Run tests inside Docker container (dependencies installed there)
docker exec api_brain python -c "
import uuid
from app.agents.tutor_agent import run_agent

result = run_agent(
    query='Explain backpropagation step by step',
    user_id=str(uuid.uuid4()),  # Use valid UUID format
    user_email='test@my.centennialcollege.ca'
)

print('=== Agent Response ===')
print(f'Intent: {result.get(\"intent\")}')
print(f'Model: {result.get(\"model_used\")}')
print(f'Error: {result.get(\"error\")}')
print(f'Sources: {len(result.get(\"sources\", []))}')
print(f'Response preview: {result.get(\"response\", \"\")[:200]}...')
"

# Expected:
# - Intent: math or tutor
# - Model: gemini-flash or gemini-tutor
# - Error: None
# - Sources: >= 0 (RAG may not be called for simple queries)
# - Response: Contains pedagogical content
```

### 7. Routing Test Suite
```bash
# Validate routing and response lengths for common query types
docker exec api_brain python -c "
import uuid
from app.agents.tutor_agent import run_agent

tests = [
    ('what is this course about?', 'syllabus_query', 'short'),
    ('what topics are covered?', 'syllabus_query', 'short'),
    ('when is the final exam?', 'syllabus_query', 'short'),
    ('explain backpropagation', 'tutor', 'long'),
    ('I am confused about gradient descent', 'tutor', 'long'),
    ('derive the chain rule for backprop', 'math', 'long'),
]

print('ROUTING TEST SUITE')
for query, expected_intent, expected_length in tests:
    result = run_agent(query=query, user_id=str(uuid.uuid4()), user_email='test@test.com')
    intent = result.get('intent', 'unknown')
    response_len = len(result.get('response', ''))
    length_type = 'short' if response_len < 400 else 'long'
    intent_ok = '✅' if intent == expected_intent else '❌'
    length_ok = '✅' if length_type == expected_length else '⚠️'
    print(f'{intent_ok} {length_ok} [{intent:15}] {response_len:4} chars | {query[:40]}')
"

# Expected: All ✅ (correct intent and appropriate response length)
```

### 8. Streaming Endpoint Test
```bash
cd backend

# Test SSE streaming
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{"messages": [{"role": "user", "content": "What is a neural network?"}], "stream": true}'

# Expected: data: {"type":"text-delta","textDelta":"..."} chunks
```

---

## Known Issues & Remediation

### Issue 1: Verbose Responses for Course-Level Questions (FIXED)
**Symptom:** "what is this course about?" returns 500+ word Socratic scaffolding
**Root Cause:** Query was routing to `tutor` intent due to "what is" pattern
**Fix Applied:**
1. Updated `supervisor.py` patterns: `syllabus_query` now has priority over `tutor`
2. Added `SYSTEM_PROMPTS` dict in `tutor_agent.py` with intent-specific prompts
3. `syllabus_query` prompt: "Give a CONCISE, direct answer (2-4 sentences)"
**Result:** Course info questions now return ~200 char responses

### Issue 1b: Verbose Responses for Simple "Explain X" Queries (FIXED)
**Symptom:** "explain gradient descent" returns 4500+ char full Socratic scaffolding
**Root Cause:** "explain" keyword was triggering `tutor` intent (full scaffolding)
**Fix Applied:**
1. Created new `explain` intent in `supervisor.py` patterns
2. `explain` triggers on "explain X", "what is a/the X" patterns WITHOUT confusion signals
3. `tutor` now only triggers on explicit confusion: "don't understand", "confused", "struggling"
4. Added `explain` prompt in `SYSTEM_PROMPTS`: "3-5 paragraphs max, MEDIUM-LENGTH"
5. Updated routing priority: tutor_override → explain → tutor
**Result:** "explain X" now returns ~1000 char concise explanations; confused users get full scaffolding

### Issue 1c: Queue UI Showing Checkmarks Without Labels (FIXED)
**Symptom:** Queue component showed 4 checkmarks but no step labels (blank items)
**Root Cause:** 
1. Backend SSE sends `{label, status}` but frontend Queue expects `{name, status}`
2. Backend `waiting` status vs frontend `pending` enum mismatch
**Fix Applied:**
1. `extension/src/hooks/use-chat.ts`: Map `label→name` and `waiting→pending` in queue event parsing
2. `extension/src/types/index.ts`: Queue interface uses `name: string` consistently
**Result:** Queue now displays step labels correctly (e.g., "Reviewing policies", "Selecting strategy")

### Issue 2: Empty `interactions` and `student_mastery` Tables (FIXED)
**Root Cause:** 
1. Evaluator used invalid outcome/scaffolding values
2. Async logging via `asyncio.create_task()` didn't complete before process exit
3. Foreign key constraints blocked test users

**Fix Applied:**
1. Changed outcome values to match DB constraint: `'correct', 'incorrect', 'confusion_detected', 'passive_read'`
2. Added scaffolding level mapping: `hint→hint, guided→guided, explained→explained, demonstrated→demonstrated`
3. Added concept detection from queries for mastery tracking (15 concept patterns)
4. Created synchronous versions: `log_interaction_to_supabase_sync()` and `update_student_mastery_sync()`
5. Dropped foreign key constraints on `interactions.student_id` and `student_mastery.user_id` to allow test UUIDs
**Result:** Now logging 6+ interactions and 5+ mastery records successfully

### Issue 3: Async Logging Reliability (FIXED)
**Root Cause:** Using `asyncio.create_task()` for database logging which doesn't wait for completion
**Fix Applied:**
1. Created `log_interaction_to_supabase_sync()` - fully synchronous version
2. Created `update_student_mastery_sync()` - fully synchronous version
3. Call sync functions directly from evaluator node instead of async gymnastics
**Result:** All interactions now reliably logged to Supabase before function returns

### Issue 4: Redis Not Using Connection Pooling
**Root Cause:** Direct `redis.Redis()` calls instead of pooled connections.
**Fix:** Create singleton pool in `app/config.py`:
```python
import redis

_redis_pool = None

def get_redis_pool():
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=settings.redis_host,
            port=settings.redis_port,
            password='myredissecret',
            max_connections=20,
            health_check_interval=30
        )
    return _redis_pool

def get_redis_client():
    return redis.Redis(connection_pool=get_redis_pool())
```

### Issue 5: Langfuse Spans Not Nested Properly ✅ FIXED
**Root Cause:** Using `client.start_span(trace_context=...)` which doesn't properly link parent-child spans in Langfuse v3.
**Status:** FIXED - All agent nodes now use proper v3 pattern
**Solution:** 
1. Pass the root span object through state as `langfuse_root_span`
2. Use `parent_span.start_span()` instead of `client.start_span(trace_context=...)`
3. Added `create_child_span_from_state()` helper in `langfuse_client.py`

```python
# CORRECT (v3 pattern) - Uses parent span object
from app.observability.langfuse_client import create_child_span_from_state

observation = create_child_span_from_state(
    state=state,  # Contains langfuse_root_span
    name="my-span",
    input_data={...},
    metadata={...}
)
# Don't forget to call observation.end() when done

# INCORRECT (old pattern) - Don't use this!
# client.start_span(trace_context={"trace_id": ...})  # Broken in v3
```

**Expected Trace Hierarchy:**
```
tutor_agent_execution (root)
├── policy_enforcement_guardrail
├── intelligent_routing_agent
├── pedagogical_tutor_agent OR math_reasoning_agent
└── mastery_verification_evaluator
```

### Issue 6: ChromaDB Returns No Results
**Possible Causes:**
1. Collection empty → Run ingestion: `python 01_ingest_comp237.py`
2. Wrong collection name → Check filter: `{"course_id": "COMP237"}`
3. Embedding dimension mismatch → Ensure 768-dim Gemini embeddings

**Debug:**
```python
from chromadb import HttpClient
client = HttpClient(host="localhost", port=8001)
collection = client.get_collection("COMP237")
print(f"Document count: {collection.count()}")
```

---

## Verified Working Behavior (as of Nov 29, 2025)

### RAG Retrieval Working ✅
The `retrieve_context` tool successfully retrieves relevant COMP237 course materials:
- **Query:** "gradient descent" → Returns syllabus chunks mentioning gradient descent, perceptrons, neural networks
- **Query:** "AI" → Returns course description, learning outcomes, and topical outline
- **Relevance scores:** Typically 0.56-0.68 (within the 0.80 threshold)
- **Sources:** `COMP_237_COURSEOUTLINE.pdf`, Blackboard export files, mediasite links, other content from the chromadb ETL pipeline

### Quick Answer Mode Working ✅
When user asks a simple question, agent responds with:
- **Format:** "Quick: [1-3 sentence answer]. Want me to explain more?"
- **Example:** "Quick: Gradient descent is an algorithm to find the minimum of a function..."
- **Triggers escalation:** User says "I WANT TO LEARN ABOUT it" → Routes to `tutor` intent

### Intent Escalation Pattern
1. User asks simple question → `fast` or `syllabus_query` intent → Concise response
2. User requests deeper explanation → Agent should detect and route to `tutor`
3. This creates a natural conversation flow from quick answers to full Socratic teaching

### Diagnostic Questions Working ✅
When tutor intent is triggered for conceptual questions:
- **Tutor asks:** "Do you want a **quick answer** or a **deeper breakdown** with examples?"
- **Student responds:** "detailed" or "quick" → Scaffolding adjusts accordingly
- **Skip diagnostic if:** User already indicated preference, high confusion detected, or follow-up question

### Knowledge Graph Suggestions Working ✅
After explaining a concept, tutor suggests next topics:
- **Format:** "📚 **What to learn next:** ✅ Decision Trees - Builds on Classification"
- **Based on:** CONCEPT_UNLOCKS relationships and student mastery scores
- **Ready indicator:** ✅ = prerequisites met, ⏳ = need to review prerequisites

### Auto-Graded Quizzes Working ✅
After detailed explanations, tutor includes a quiz question:
- **Format:** `<quiz>{"question": "...", "options": [...], "correct": 1, "explanation": "..."}</quiz>`
- **Triggers:** Only for `tutor` intent with `explained` or `demonstrated` scaffolding
- **Evaluation API:** `POST /api/mastery/quiz/evaluate` updates mastery based on answer
- **Quiz bank:** 10 concepts with pre-built questions in `quiz_generator.py`
- **Concept patterns:** Fixed to match full words (e.g., "classification", "backpropagation")

### Visual Diagrams Working ✅
For concepts with visual support, tutor includes ASCII diagrams:
- **Format:** `📊 **[Concept] Visualization:** \n\`\`\`[ASCII art]\`\`\``
- **Triggers:** Only for `explained`/`demonstrated` scaffolding when concept is detected
- **ASCII concepts (10):** neural_network, gradient_descent, backpropagation, decision_tree, classification_vs_regression, kmeans_clustering, confusion_matrix, overfitting, activation_functions, train_test_split
- **Mermaid concepts (5):** neural_network, gradient_descent, decision_tree, supervised_learning, classification_pipeline
- **Mapping:** `CONCEPT_TO_DIAGRAM` converts detected concepts to diagram keys

---

## Next Implementation Priorities

1. ~~**Mastery-Driven Scaffolding:** Query mastery table, inject into `select_scaffolding_level()`~~ ✅ DONE
2. ~~**Quick Answer Mode:** Add `quick` intent with 1-sentence responses~~ ✅ DONE
3. ~~**Misconception Memory:** Store in `interactions.metadata`, reference in prompts~~ ✅ DONE
4. ~~**Knowledge Graph:** Build concept relationships for "next topic" suggestions~~ ✅ DONE
5. ~~**Diagnostic Questions:** Add micro-checks before teaching~~ ✅ DONE
6. ~~**Auto-Graded Quizzes:** Generate and evaluate mini-exercises~~ ✅ DONE
7. ~~**Wire Up Empty Tables:**~~ ✅ DONE (concepts seeded, evaluator logs interactions)
8. ~~**Redis Connection Pool:** Implement singleton pool with health checks~~ ✅ DONE
9. ~~**Langfuse Span Hierarchy:** Ensure all nodes use proper v3 pattern~~ ✅ DONE
10. ~~**Visual Support:** ASCII diagrams and Mermaid.js for AI concepts~~ ✅ DONE

🎉 **All core features complete!** Remaining work:
- Frontend quiz component to display and submit answers
- Frontend Mermaid.js renderer for flowcharts
- Production deployment and monitoring
