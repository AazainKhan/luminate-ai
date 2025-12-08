# Luminate AI Course Marshal - Development Instructions

If shadcn is mentioned use shadcn mcp
What this actually gets you:
Prompt	Without MCP	With MCP
"How do I customize the color picker component?"	Generic HTML5 color input or random React examples	Exact color picker from shadcn.io registry with proper form integration
"Show me button variants"	Maybe mentions primary/secondary if you're lucky	All 6 actual variants with real examples
"I need a data table with sorting"	Basic table implementations from training data	The actual Data Table component with working sort/filter patterns


## Project Vision & Philosophy

This is an **agentic AI tutoring platform** for COMP 237 (Introduction to AI) at Centennial College. The critical distinction: **this is NOT ChatGPT in a box**. The agent must exhibit true pedagogical intelligence:

- **Scaffolding not Answers**: Guide students to discover answers, don't answer for them
- **Adaptive Escalation**: 4-level scaffolding (diagnostic → hints → examples → full explanation)
- **LearnLM-Aligned**: Based on Google's learning science research
- **Course-Grounded**: All responses use COMP237 materials from ChromaDB

## Research Foundation

The agent is built on these research sources:
- **LearnLM Principles** (`docs/learnlm.md`): Active learning, cognitive load, adaptivity, curiosity, metacognition
- **Adarsh's Scaffolding Guide** (`docs/friends-work/luminate-ai-adarsh/SCAFFOLDING_GUIDE.md`): 4-phase pedagogy
- **Gemini 2.5 Flash**: Only model used, optimized for educational responses

---

## Architecture Overview

### 4-Node LangGraph Pipeline (Simplified)

```
┌─────────────────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│        Planner          │───▶│   Router    │───▶│ Agent Nodes  │───▶│  Evaluator  │
│ (3 Laws + Classify)     │    │ (route_from │    │ ┌──────────┐ │    │ (Log+Track) │
│                         │    │    _plan)   │    │ │  Tutor   │ │    └─────────────┘
│ Law 1:Scope (RAG+regex) │    │             │    │ ├──────────┤ │
│ Law 2:Integrity (regex) │    │             │    │ │  Math    │ │
│ Law 3:Mastery (defer)   │    │             │    │ ├──────────┤ │
│                         │    │             │    │ │  Reject  │ │
│ Task: explain/solve/    │    │             │    │ └──────────┘ │
│       quick/code/reject │    │             │    │              │
└─────────────────────────┘    └─────────────┘    └──────────────┘

Policy Enforcement (in Planner):
  - Law 1 (Scope): Only COMP 237 topics - RAG distance < 0.25 + 60+ regex patterns
  - Law 2 (Integrity): No complete assignment solutions - 20+ regex patterns
  - Law 3 (Mastery): Verify understanding - deferred to Evaluator
```

### File Structure

```
backend/app/
├── agent/                    # LangGraph agent (core)
│   ├── graph.py             # StateGraph definition + run_agent()
│   ├── state.py             # AgentState TypedDict (~25 fields)
│   ├── schemas.py           # Pydantic schemas (TaskType, Source, etc.)
│   ├── nodes/
│   │   ├── planner.py       # Policy enforcement + Query classification
│   │   ├── tutor.py         # Scaffolded teaching (4 levels)
│   │   ├── math.py          # Step-by-step math solutions
│   │   ├── reject.py        # Off-topic/policy violation handling
│   │   └── evaluator.py     # Interaction logging + mastery tracking
│   ├── prompts/
│   │   └── tutor.py         # LearnLM-aligned prompts
│   └── tools/
│       └── rag.py           # Direct ChromaDB retriever
├── api/routes/
│   ├── chat.py              # SSE streaming endpoint
│   ├── history.py           # Chat persistence (Supabase)
│   ├── mastery.py           # Mastery CRUD + quiz evaluation
│   └── admin.py             # ETL triggers
├── etl/                     # Document ingestion
│   ├── pipeline.py          # ETL orchestration
│   ├── blackboard_parser.py # Blackboard export parser
│   └── document_processor.py # Text extraction
├── rag/                     # Vector store utilities
│   ├── chromadb_client.py   # ChromaDB connection
│   └── embeddings.py        # Gemini embeddings
├── observability/
│   └── langfuse_client.py   # Langfuse v3 tracing
├── config.py                # Settings from .env
└── redis_client.py          # Redis connection pool
```

---

## Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| `api_brain` | 8000 | FastAPI backend |
| `memory_store` | 8001 | ChromaDB vector store |
| `neo4j_graph` | 7474/7687 | Knowledge graph (future) |
| `redis` | 6379 | Caching & session |
| `langfuse-web` | 3000 | Observability UI |
| `langfuse_postgres` | 5433 | Langfuse database |
| `clickhouse` | 8123 | Langfuse analytics |
| `minio` | 9000 | Object storage |

### Key Docker Commands

```bash
# Start all services
docker compose up -d

# Rebuild backend after code changes
docker compose build api_brain --no-cache && docker compose up -d api_brain

# View logs
docker logs -f api_brain

# Test ChromaDB connection
docker exec api_brain python -c "from app.agent.tools.rag import get_rag_retriever; r = get_rag_retriever(); print('Connected')"
```

---

## Structured Output & Frontend Integration

### Model & Streaming Strategy

**Single Model Architecture**: Gemini 2.5 Flash for all tasks
- No model selector in frontend (simplifies UX)
- Temperature varies by task (0.7 for tutoring, 0.3 for quick answers)
- Streaming via SSE with AI SDK v5-compatible events

### Backend Schemas (Pydantic → Zod Compatible)

All schemas in `backend/app/agent/schemas.py` use Pydantic with discriminated unions that map directly to Zod validators:

```python
# TaskType enum for routing
class TaskType(str, Enum):
    EXPLAIN = "explain"
    SOLVE = "solve"
    QUICK = "quick"
    CODE = "code"
    REJECT = "reject"

# Discriminated union payloads
class ExplainPayload(BaseModel):
    type: Literal["explain"] = "explain"
    topic: str
    escalation_level: int = Field(1, ge=1, le=4)

class SolvePayload(BaseModel):
    type: Literal["solve"] = "solve"
    problem: str

# Union type maps to Zod discriminatedUnion()
PayloadType = Annotated[
    Union[ExplainPayload, SolvePayload, QuickPayload, CodePayload, RejectPayload],
    Field(discriminator="type")
]

# Source citation for RAG
class Source(BaseModel):
    title: str
    source_file: str
    collection: str = "COMP237"
    score: float = Field(0.0, ge=0.0, le=1.0)
    content: Optional[str] = None
    page: Optional[int] = None
```

### Frontend Types (extension/src/types/index.ts)

The frontend TypeScript types mirror backend schemas:

```typescript
// Unified Chain of Thought for thinking display
interface ThoughtStep {
  id: string
  type: "queue" | "tool" | "reasoning" | "search" | "result"
  name: string
  status: "pending" | "processing" | "completed" | "error"
  details?: string
  input?: Record<string, any>
  output?: any
  sources?: Array<{ title: string; url?: string }>
  timestamp?: number
}

// Message with streaming metadata
interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  reasoning?: string
  sources?: Array<{ 
    title: string
    source_file?: string
    content?: string
    page?: number | string
  }>
  chainOfThought?: ThoughtStep[]  // Unified COT display
  codeBlocks?: Array<{ language: string; code: string }>
  suggestions?: string[]
  metadata?: {
    traceId?: string
    intent?: string
    scaffoldingLevel?: string
    evaluation?: {
      confidence: number
      detected_concept?: string
      scaffolding_level?: string
    }
  }
  status?: "streaming" | "complete" | "error"
  streamComplete?: boolean
}
```

### Streaming Event Protocol

SSE events use structured `thinking` events (not legacy queue-init/queue-update):

```typescript
// Trace ID for observability (emitted first)
{ type: "trace-id", traceId: "abc123" }

// Structured thinking steps (shows ThinkingTrace accordion)
{ type: "thinking", step: "scope_check", status: "processing", message: "Checking if question is within COMP237 scope..." }
{ type: "thinking", step: "scope_check", status: "completed", result: { in_scope: true }, message: "✓ Question is within COMP237 scope" }
{ type: "thinking", step: "escalation", status: "completed", result: { level: 1 }, message: "Scaffolding level 1" }
{ type: "thinking", step: "classification", status: "completed", result: { task: "explain" }, message: "Task type: explain" }
{ type: "thinking", step: "rag_retrieval", status: "processing", message: "Searching course materials..." }
{ type: "thinking", step: "rag_retrieval", status: "completed", result: { docs_found: 5 }, message: "Found 5 relevant course materials" }
{ type: "thinking", step: "strategy", status: "completed", message: "Response generated with scaffolding" }

// RAG sources (for inline citations)
{ type: "sources", sources: [{ title: "Topic 8.1: Introduction to ANN", source_file: "Module 8 - Topic 8.1", week: 8, module: "Module 8", content: "..." }] }

// Response text (streaming)
{ type: "text-delta", textDelta: "Great question! When you think about..." }

// Routing info
{ type: "routing", intent: "explain", method: "llm", escalation_level: 1 }

// Evaluation result
{ type: "evaluation", evaluation: { concept_detected: "neural_networks", scaffolding_level: "hint", outcome: "correct" } }

// Completion signal
{ type: "finish", chatId: "uuid", traceId: "abc123" }
```

### ThinkingStep Types

```typescript
type ThinkingStepType = 
  | "scope_check"      // COMP237 scope verification
  | "integrity_check"  // Academic integrity check
  | "mastery_lookup"   // Student mastery retrieval
  | "escalation"       // Scaffolding level decision
  | "classification"   // Task type routing
  | "rag_retrieval"    // Course material search
  | "strategy"         // Teaching approach selection
  | "concept_detection" // Evaluator concept identification
```

### Frontend Component Guidelines

**shadcn/ui Components**:
- Thinking accordion: `Accordion` with streaming status
- Chat bubbles: Custom with `Card` base
- Code blocks: `Highlight` with copy button
- Source citations: `Badge` + `Popover`

**Smart Scrolling Behavior**:
- Auto-scroll during streaming (unless user has scrolled up)
- Pause on user scroll, resume on bottom
- Smooth scroll-to-bottom button when content overflows

**No Model Selector**:
- Model is fixed to `gemini-2.5-flash` 
- Remove any model dropdown from chat UI
- Temperature controlled by backend based on task type

---

## Streaming Reliability Patterns

### The "Disappearing Content" Problem

SSE streaming in React can cause content to disappear due to state race conditions. This is a common issue when:
1. Multiple rapid `setMessages` calls overwrite each other
2. Closures capture stale state during async operations
3. The `finish` event handler doesn't preserve accumulated content

### Solution: Stream Buffer Pattern

We use a `useRef` buffer to accumulate content during streaming, independent of React state:

```typescript
// Buffer for accumulated content during streaming (prevents race conditions)
const streamBufferRef = useRef<{
  rawContent: string
  content: string
  reasoning?: string
  sources?: any[]
  citations?: any[]
  thinkingTrace?: ThinkingStep[]
  metadata?: Record<string, any>
  evaluation?: any
}>({
  rawContent: "",
  content: ""
})
```

### Key Implementation Rules

1. **Always Reset Buffer on New Message**:
```typescript
// Reset before starting new stream
streamBufferRef.current = {
  rawContent: "",
  content: "",
  reasoning: undefined,
  sources: undefined,
  // ... reset all fields
}
```

2. **Accumulate in Buffer, Then Sync to State**:
```typescript
if (parsed.type === "text-delta") {
  // Accumulate in buffer (source of truth)
  buffer.rawContent += parsed.textDelta
  buffer.content = processContent(buffer.rawContent)
  
  // Sync to React state
  updatedMsg.rawContent = buffer.rawContent
  updatedMsg.content = buffer.content
}
```

3. **Preserve Buffer Content on Finish**:
```typescript
if (parsed.type === "finish") {
  // CRITICAL: Copy buffer to message before clearing
  if (buffer.content) {
    updatedMsg.content = buffer.content
    updatedMsg.rawContent = buffer.rawContent
  }
  // ... preserve all buffer fields
  updatedMsg.streamComplete = true
}
```

### Backend SSE Best Practices

1. **Always Send Finish Event**:
```python
try:
    async for event in process_events():
        yield event
finally:
    yield {"type": "finish", "chatId": chat_id, "traceId": trace_id}
```

2. **Chunk Large Responses**:
```python
# Don't send entire response at once
chunk_size = 50
for i in range(0, len(response), chunk_size):
    yield {"type": "text-delta", "textDelta": response[i:i + chunk_size]}
```

3. **Use Proper SSE Headers**:
```python
return StreamingResponse(
    generate_stream(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # Disable nginx buffering
    }
)
```

### Testing Streaming

```bash
# Test SSE directly with curl
curl -N -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What is AI?"}],"stream":true}' \
  http://localhost:8000/api/chat/stream
```

---

### Gemini API Integration

Based on `docs/gemini-api-docs.md` and `docs/gemini-function-calling.md`:

```python
# Backend: Direct Gemini calls via LangChain wrapper
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    google_api_key=settings.google_api_key,
)
```

**Gemini Structured Output** (for future tool calling):
```python
from google import genai
from pydantic import BaseModel

class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_answer: int

# Gemini returns validated Pydantic model
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Generate a quiz about neural networks",
    config={"response_mime_type": "application/json", "response_schema": QuizQuestion}
)
```

---

## Escalation System (Core Pedagogy)

The agent uses 4 escalation levels based on LearnLM research and Adarsh's scaffolding guide:

| Level | Name | Behavior | Trigger |
|-------|------|----------|---------|
| **1** | Diagnostic | Ask questions only, no examples | First question on topic |
| **2** | Directed Hints | Analogy + guiding question | Student responded to diagnostic |
| **3** | Concrete Example | Walk through example step-by-step | Still confused after hints |
| **4** | Full Explanation | Direct answer + metacognition prompt | Stuck after multiple attempts |

### Stuck Detection (`planner.py`)

```python
STUCK_PATTERNS = [
    r"\bi\s+don'?t\s+know\b",
    r"\bidk\b",
    r"\bstill\s+confused\b",
    r"\bdidn'?t\s+(?:make\s+)?sense\b",
    r"\bexplain\s+again\b",
    r"\bjust\s+tell\s+me\b",
]
```

Escalation increases automatically based on:
- Current query matches stuck patterns
- History contains previous stuck signals
- Student explicitly requests "just tell me"

### Escalation Calculation

```python
def _calculate_escalation_level(is_stuck: bool, stuck_count: int) -> int:
    if not is_stuck:
        return 1  # Default: diagnostic questions
    if stuck_count >= 2:
        return 4  # Full explanation
    elif stuck_count == 1:
        return 3  # Concrete examples
    else:
        return 2  # Directed hints
```

---

## Routing Logic

---

## Policy Enforcement (in Planner Node)

The Planner runs policy checks FIRST before classification to enforce the 3 Laws:

### Law 1: Scope (COMP 237 Only)

Uses two-tier detection:
1. **Pattern matching**: 60+ off-topic regex patterns (weather, sports, entertainment, etc.)
2. **RAG check**: If no pattern match, queries ChromaDB with threshold < 0.25

```python
# Off-topic patterns (sample from planner.py)
OFF_TOPIC_PATTERNS = [
    r'\bpizza\b', r'\bweather\b', r'\bfootball\b',
    r'\bnetflix\b', r'\btaylor swift\b', ...
]
```

### Law 2: Integrity (No Cheating)

Regex patterns to detect assignment/exam cheating requests:

```python
INTEGRITY_VIOLATION_PATTERNS = [
    r"\bdo\s+my\s+(?:assignment|homework|project|lab)\b",
    r"\bgive\s+me\s+(?:the|all)\s+(?:answers?|solutions?)\b",
    r"\bjust\s+give\s+me\s+the\s+(?:answer|solution|code)\b",
    r"\bexam\s+(?:answers?|solutions?|help)\b",
    ...
]
```

### Law 3: Mastery (Understanding Verification)

Deferred to Evaluator node - triggers quiz suggestions when mastery score is low.

### Policy Check in Planner

```python
def planner_node(state: AgentState) -> Dict[str, Any]:
    # Step 1: Policy Checks (fast regex-based)
    approved, rejection_reason, rejection_type = _check_policy(query)
    if not approved:
        return {..., "approved": False, "rejection_reason": rejection_reason}
    
    # Step 1b: RAG-based scope check for edge cases
    is_in_scope, rag_score, scope_reason = _check_scope_with_rag(query)
    if not is_in_scope:
        return {..., "approved": False, "rejection_reason": scope_reason}
    
    # Step 2: Classification and routing
    ...
```

---

### Task Classification Priority (`planner.py`)

1. **Confusion signals** → `explain` (always)
2. **Math keywords** (derive, calculate, solve) → `solve`
3. **Code keywords** (Python, implement, debug) → `code`
4. **Brief requests** (quickly, briefly) → `quick`
5. **Course logistics** (syllabus, deadline) → `quick`
6. **Off-topic** (cooking, sports) → `reject`
7. **Default** → `explain`

### Routing from Plan (`graph.py`)

```python
def route_from_plan(state: AgentState) -> str:
    plan = state.get("plan") or {}
    subtasks = plan.get("subtasks", [])
    task = subtasks[0].get("task", "explain") if subtasks else "explain"
    if task == "solve": return "math"
    if task == "reject": return "reject"
    return "tutor"  # explain, quick, code all go to tutor
```

---

## RAG System

### ChromaDB Collection

- **Collection name**: `comp237_course_materials`
- **Documents**: 403 ingested from Blackboard export
- **Embeddings**: Gemini `embedding-001` (768-dim)
- **Host**: Docker service `memory_store:8000`

### Retrieval (`tools/rag.py`)

```python
class RAGRetriever:
    def retrieve(self, query: str, k: int = 5, threshold: float = 0.25):
        # Generate query embedding with Gemini
        query_embedding = self._embeddings.embed_query(query)
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert distance to similarity score
        score = 1.0 / (1.0 + float(dist))
        
        return docs, RAGMetadata(has_comp237=any_relevant, ...)
```

---

## Observability (Langfuse v3)

### Trace Hierarchy

```
agent_execution (root trace)
├── planner_node
│   ├── policy_check (integrity, scope)
│   └── classification
├── rag_retrieval
├── tutor_generation OR math_generation
└── evaluator_node
    ├── concept_detection
    ├── mastery_update
    └── langfuse_scores
```

### Creating Traces (`observability/langfuse_client.py`)

```python
from app.observability import create_trace, flush_langfuse, get_langfuse_client

# Create root trace for agent execution
trace = create_trace(
    name="agent_execution",
    user_id=user_id,
    session_id=session_id,
    metadata={"query": query[:100], "chat_id": chat_id},
    tags=["tutor-agent", "comp237"]
)
state["trace_id"] = trace.id

# ... agent execution ...

# Always flush after execution
flush_langfuse()
```

### Langfuse Scores (Evaluator Node)

The evaluator sends scores to Langfuse for each interaction:

```python
# From nodes/evaluator.py
client.create_score(
    trace_id=trace_id,
    name="scaffolding_level",
    value=float(escalation_level),
    comment=f"Escalation: {scaffolding_level}"
)

client.create_score(
    trace_id=trace_id,
    name="concept_coverage",
    value=1.0,
    comment=f"Concept: {detected_concept}"
)
```

### Langfuse Best Practices

1. **Use descriptive span names**: `planner_classification`, `rag_retrieval`, `tutor_generation`
2. **Propagate user_id/session_id**: Use `propagate_attributes()` context manager
3. **Always flush**: Call `flush_langfuse()` in API endpoints and after agent runs
4. **Score interactions**: Use `create_score()` for pedagogical quality metrics
5. **Tag traces**: Add tags like `["tutor-agent", "comp237", "escalation-3"]`

---

## Prompts (LearnLM-Aligned)

### Main Tutor Prompt Structure (`prompts/tutor.py`)

The prompts are aligned with:
1. **LearnLM Principles** from Google's research
2. **Adarsh's Scaffolding Guide** (4-phase: Activation, Socratic, Hints, Challenge)
3. **COMP237 course context** from ChromaDB

Key prompt features:
- Level-specific instructions (don't mix levels)
- Explicit "DO NOT" rules to prevent answer-giving at Level 1
- Example responses for each level
- Metacognition prompts at Level 4
- Source citation requirements: `[From: Week X]`

### Prompt Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `{escalation_level}` | Planner detection | 1-4 scaffolding level |
| `{context}` | RAG retrieval | Course materials |
| `{history}` | Chat state | Conversation context |
| `{question}` | User input | Current query |

---

## State Schema (`state.py`)

```python
class AgentState(TypedDict):
    # Input
    messages: List[BaseMessage]
    query: str
    
    # User Context
    user_id: Optional[str]
    conversation_history: Optional[List[dict]]
    
    # Routing
    plan: Optional[dict]              # PlannerPlan
    routing_info: Optional[dict]      # Debug info
    
    # RAG
    retrieved_docs: List[dict]
    rag_metadata: Optional[dict]
    context_str: Optional[str]
    
    # Scaffolding
    escalation_level: int             # 1-4
    stuck_count: int
    is_stuck: bool
    
    # Output
    response: Optional[str]
    sources: List[dict]
    
    # Evaluation (from Evaluator Node)
    evaluation: Optional[dict]        # {concept_detected, misconceptions, outcome, etc.}
    
    # Observability
    trace_id: Optional[str]
    session_id: Optional[str]
```

---

## Evaluator Node (`nodes/evaluator.py`)

The evaluator runs after each agent response to:
1. **Detect Concepts**: Identify AI/ML topics from query using regex patterns
2. **Detect Misconceptions**: Identify common student misconceptions
3. **Log Interactions**: Insert into Supabase `interactions` table
4. **Update Mastery**: Update `student_mastery` scores based on performance
5. **Score in Langfuse**: Send scaffolding_level, concept_coverage scores

### Concept Detection

```python
CONCEPT_PATTERNS = {
    "backpropagation": r"\b(backprop\w*|back.?propagat\w*|chain.?rule)",
    "gradient_descent": r"\b(gradient.?descent|learning.?rate|optimi[sz]\w+)",
    "neural_networks": r"\b(neural.?network\w*|perceptron|hidden.?layer)",
    # ... 11 total concepts
}
```

### Mastery Scoring

Uses exponential moving average with decay for forgetting curve:
```python
def calculate_mastery_score(old_score, evaluation_confidence, decay_factor=0.95):
    decayed_old = 0.5 + (old_score - 0.5) * decay_factor
    new_score = 0.7 * decayed_old + 0.3 * evaluation_confidence
    return max(0.1, min(0.95, new_score))
```

Confidence levels:
- Confusion detected → 0.3 (decreases mastery)
- Heavy scaffolding (level 3-4) → 0.4
- Moderate scaffolding (level 2) → 0.6
- Light scaffolding (level 1) → 0.7 (increases mastery)

---

## Database Schema (Supabase)

```sql
-- Chat sessions
CREATE TABLE chats (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users,
    title TEXT,
    created_at TIMESTAMPTZ
);

-- Chat messages
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    chat_id UUID REFERENCES chats,
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ
);

-- Student mastery tracking
CREATE TABLE student_mastery (
    user_id UUID,
    concept_tag TEXT,
    mastery_score FLOAT,        -- 0.1 to 0.95
    decay_factor FLOAT,         -- Default 0.95
    last_assessed_at TIMESTAMPTZ
);

-- Interaction logging for analytics
CREATE TABLE interactions (
    id UUID PRIMARY KEY,
    student_id UUID,
    type TEXT,                  -- 'question_asked', 'quiz_attempt'
    concept_focus TEXT,         -- Detected concept tag
    outcome TEXT,               -- 'correct', 'incorrect', 'confusion_detected'
    scaffolding_level TEXT,     -- 'hint', 'guided', 'explained', 'demonstrated'
    metadata JSONB,
    created_at TIMESTAMPTZ
);
```

---

## Testing

### Quick Agent Test

```bash
docker exec api_brain python -c "
from app.agent.graph import run_agent
result = run_agent(query='What is backpropagation?')
print(f'Intent: {result[\"intent\"]}')
print(f'Escalation: {result[\"escalation_level\"]}')
print(f'Response: {result[\"response\"][:200]}...')
"
```

### Test Escalation Levels

```bash
docker exec api_brain python -c "
from app.agent.graph import run_agent

# Level 1: First question (should ask diagnostic question)
result = run_agent(query='What is a neural network?', conversation_history=[])
print(f'Level 1: Escalation={result[\"escalation_level\"]}')
print(f'Response: {result[\"response\"][:150]}...')

# Level 4: Very stuck student
history = [
    {'role': 'user', 'content': 'I don\\'t know'},
    {'role': 'user', 'content': 'Still confused'},
    {'role': 'user', 'content': 'Just tell me'}
]
result = run_agent(query='explain again', conversation_history=history)
print(f'Level 4: Escalation={result[\"escalation_level\"]}')
print(f'Response: {result[\"response\"][:150]}...')
"
```

### Verify RAG

```bash
docker exec api_brain python -c "
from app.agent.tools.rag import get_rag_retriever
r = get_rag_retriever()
docs, meta = r.retrieve('gradient descent', k=3)
print(f'Found {len(docs)} docs, has_comp237={meta.has_comp237}')
for d in docs[:2]:
    print(f'  - {d[\"source\"]}: {d[\"content\"][:80]}...')
"
```

---

## Common Development Tasks

### 1. Modify Escalation Logic

Edit `backend/app/agent/nodes/planner.py`:
- `STUCK_PATTERNS`: Regex patterns for stuck detection
- `_detect_stuck()`: Logic for counting stuck signals
- `_calculate_escalation_level()`: Thresholds for level selection

### 2. Update Prompts

Edit `backend/app/agent/prompts/tutor.py`:
- `TUTOR_SYSTEM_PROMPT`: Main scaffolding prompt
- `MATH_PROMPT`: Math-specific scaffolding
- `QUICK_ANSWER_PROMPT`: Brief factual responses

### 3. Add New Task Type

1. Add to `TaskType` enum in `schemas.py`
2. Add detection patterns in `planner.py`
3. Create new node in `nodes/`
4. Add routing in `graph.py`

### 4. Ingest New Documents

```bash
w# Use admin API endpoint
curl -X POST http://localhost:8000/api/admin/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@blackboard_export.zip"

# Or run directly in container
docker exec -it api_brain python -m app.etl.pipeline --source /path/to/export.zip
```

---

## Environment Variables

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# ChromaDB (Docker)
CHROMADB_HOST=memory_store
CHROMADB_PORT=8000

# Langfuse
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_HOST=http://langfuse-web:3000

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=myredissecret
```

---

## Inline Citations (Perplexity-style)

The agent uses inline citations `[1]`, `[2]` in responses at escalation levels 2-4. Citations link to course materials with hover previews.

### Citation Flow

```
Backend (graph.py) → sources event → Frontend (useChat.ts) → citations array → Message.tsx → InlineCitation components
```

### Source Structure

```typescript
interface Source {
  title: string           // "Topic 8.1: Introduction to ANN"
  source_file: string     // "Module 8 - Topic 8.1"
  module?: string         // "Module 8"
  week?: number           // 8
  content?: string        // Content snippet for hover preview
  description?: string    // Short description
  score: number           // Relevance score (0-1)
}
```

### Citation Components

- `InlineCitationCardTrigger`: Badge showing `[1]` with hover
- `InlineCitationCardBody`: Hover card with source details
- `InlineCitationSource`: Module/week badge + title + description
- `InlineCitationQuote`: Blockquote for content preview

### Usage in Message.tsx

```tsx
const renderContentWithCitations = (content: string) => {
  const parts = content.split(/(\[\d+\])/)
  return (
    <InlineCitation>
      {parts.map((part, index) => {
        const match = part.match(/\[(\d+)\]/)
        if (match) {
          const citation = message.citations?.find(c => c.number === match[1])
          return (
            <InlineCitationCard key={index}>
              <InlineCitationCardTrigger number={citation.number} />
              <InlineCitationCardBody>
                <InlineCitationSource 
                  title={citation.title}
                  module={citation.module}
                  week={citation.week}
                />
              </InlineCitationCardBody>
            </InlineCitationCard>
          )
        }
        return <InlineCitationText key={index}>{part}</InlineCitationText>
      })}
    </InlineCitation>
  )
}
```

---

## Verified Test Results (December 2024)

All core systems verified working:

### Intent Detection ✅

| Query Type | Expected Intent | Result |
|------------|-----------------|--------|
| "What is a neural network?" | explain | ✓ |
| "Calculate the gradient of L = (y - y_hat)^2" | solve | ✓ |
| "Show me Python code for a perceptron" | code | ✓ |
| "What is the weather?" | off_topic (reject) | ✓ |
| "Do my homework for me" | integrity (reject) | ✓ |

### Escalation Levels ✅

| Scenario | Expected Level | Result |
|----------|----------------|--------|
| Fresh question | 1 | ✓ |
| Slightly confused | 2 | ✓ |
| Still confused | 3 | ✓ |
| "Just tell me" | 4 | ✓ |

### Data Flow ✅

- ChromaDB: 403 documents, connected
- Supabase: student_mastery, interactions tables accessible
- Langfuse: Connected, scores being sent
- Redis: Connected for caching

---

## Key Design Decisions

### Why Gemini 2.5 Flash Only?

- Optimized for educational responses
- Fast inference for real-time tutoring
- LearnLM research is Gemini-native
- Simplifies model management

### Why Direct ChromaDB (No LangChain Wrappers)?

- Simpler, fewer dependencies
- Direct control over embeddings
- Matches Adarsh's `DirectRAGRetriever` pattern
- Easier debugging

### Why 4 Escalation Levels?

- Research-backed (Zone of Proximal Development)
- Prevents "answer machine" behavior
- Encourages active learning
- Matches LearnLM "scaffolding" principle

### Why Planner + Router Pattern?

- Fast-path heuristics (95% of queries)
- LLM fallback for ambiguous cases
- Clean separation of concerns
- Easy to add new task types

### Why `thinking` events instead of `queue-init`/`queue-update`?

- Cleaner, more structured UI
- Shows actual agent decisions (scope, escalation, classification)
- Single source of truth for frontend ThinkingTrace component
- Easier to debug and extend

---

## Troubleshooting

### ChromaDB Connection Error

```bash
# Check if memory_store is running
docker ps | grep memory_store

# Test connection
docker exec api_brain python -c "
import chromadb
c = chromadb.HttpClient(host='memory_store', port=8000)
print(c.heartbeat())
"
```

### RAG Returns No Documents

```bash
# List collections
docker exec api_brain python -c "
import chromadb
c = chromadb.HttpClient(host='memory_store', port=8000)
print([col.name for col in c.list_collections()])
"

# Check document count
docker exec api_brain python -c "
import chromadb
c = chromadb.HttpClient(host='memory_store', port=8000)
col = c.get_collection('comp237_course_materials')
print(f'Documents: {col.count()}')
"
```

### Langfuse Traces Not Appearing

1. Check Langfuse is running: `docker ps | grep langfuse`
2. Verify credentials in `.env`
3. Ensure `flush_langfuse()` is called after agent execution
4. Check Langfuse UI at http://localhost:3000

### Agent Returns Generic Response

1. Check escalation level is being set correctly
2. Verify RAG is returning course context
3. Check prompt includes `{context}` variable
4. Review Langfuse trace for debugging

---

## Future Roadmap

- [x] **Mastery Tracking**: Update `student_mastery` table based on evaluator scores
- [ ] **Knowledge Graph**: Use Neo4j for concept relationships (requires concept graph generation)
- [ ] **Visual Diagrams**: ASCII/Mermaid diagrams for concepts
- [ ] **Auto-Graded Quizzes**: End responses with testable questions
- [ ] **Misconception Memory**: Track and address common misconceptions
- [ ] **E2B Code Execution**: Run student code in sandbox

### Neo4j Integration Status

Neo4j is running and connected, but requires concept graph data:
- **GraphRAG Service** exists at `backend/app/rag/graph_rag.py`
- **Features available**: Learning paths, prerequisite detection, related concepts
- **Requires**: Concept extraction pipeline to populate graph from course materials
- **Benefits**: ~35% improvement in RAG accuracy with hybrid vector+graph retrieval

To enable:
1. Create concept extraction from ChromaDB documents
2. Generate `concept_graph.json` with nodes and edges
3. Load into Neo4j via `Neo4jGraphService.load_concept_graph()`
4. Integrate `GraphRAGService.hybrid_retrieve()` into RAG pipeline
