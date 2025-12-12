# 4. Technical Execution

## Luminate AI Course Marshal

---

## 4.1 Algorithm Choice and Justification

### Core AI Algorithms

The Luminate AI Course Marshal employs multiple AI algorithms, each selected for specific capabilities:

#### 4.1.1 Large Language Models (LLMs)

| Model | Provider | Use Case | Justification |
|-------|----------|----------|---------------|
| **Gemini 2.0 Flash** | Google | Default reasoning, tutoring | Low latency (<2s), strong reasoning, cost-effective |
| **Llama 3.3 70B** | Groq | Code generation | Excellent code quality, fastest inference via Groq |
| **Gemini Embedding** | Google | Document vectorization | Native Google ecosystem integration, 768 dimensions |

**Selection Rationale:**

1. **Gemini 2.0 Flash** was selected over GPT-4 due to:
   - Superior cost-efficiency (free tier available)
   - Native Google Cloud integration
   - Strong performance on educational content
   - Low latency critical for interactive tutoring

2. **Groq/Llama 3.3** was selected for code generation due to:
   - Exceptional code generation quality (comparable to Claude)
   - Groq's hardware acceleration provides <1s inference
   - Open-source model avoids vendor lock-in

3. **Alternative Considered: Claude 3.5 Sonnet**
   - Excellent reasoning but higher latency and cost
   - Reserved for future complex reasoning tasks

#### 4.1.2 Retrieval Algorithm (RAG)

**Algorithm**: Approximate Nearest Neighbor (ANN) search with L2 distance

```python
# ChromaDB uses HNSW (Hierarchical Navigable Small World) algorithm
# Default parameters:
{
    "hnsw:space": "l2",          # L2 (Euclidean) distance
    "hnsw:construction_ef": 100, # Construction exploration factor
    "hnsw:M": 16,                # Number of bi-directional links
    "hnsw:search_ef": 10         # Search exploration factor
}
```

**Justification:**
- HNSW provides O(log n) query time vs O(n) for brute force
- L2 distance aligns with Gemini embedding space geometry
- Configurable precision-recall tradeoff via ef parameters

#### 4.1.3 Intent Classification Algorithm

**Algorithm**: Rule-based pattern matching with weighted scoring

```python
INTENT_PATTERNS = {
    "math": [r"\bderive\b", r"\bformula\b", r"\bequation\b", ...],
    "tutor": [r"\bexplain\b", r"\bunderstand\b", r"\bconfused\b", ...],
    "coder": [r"\bpython\b", r"\bcode\b", r"\bimplement\b", ...],
}

def route_intent(query: str) -> Dict:
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, query.lower()))
        if score > 0:
            scores[intent] = score
    
    # Priority routing: coder > syllabus > math > tutor > fast
    return select_by_priority(scores)
```

**Justification:**
- Deterministic behavior critical for policy enforcement
- Zero inference latency (pure regex)
- Easily auditable and modifiable rules
- Alternative (LLM classification) would add 500ms+ latency

#### 4.1.4 Scope Enforcement Algorithm

**Algorithm**: Semantic similarity threshold with empirical calibration

```
Query → Embed → ChromaDB Search → Distance Scores → Threshold Check
```

**Threshold Selection Process:**

| Query Type | Sample | Min Distance | Decision |
|------------|--------|--------------|----------|
| Direct course topic | "What is backpropagation?" | 0.58 | ✅ In-scope |
| Related AI topic | "Explain softmax function" | 0.77 | ✅ In-scope |
| General question | "What is the weather?" | 0.94 | ❌ Out-of-scope |
| Programming generic | "How do I use Python loops?" | 0.85 | ❌ Out-of-scope |

**Final Threshold**: 0.80 (empirically tuned to maximize in-scope coverage while blocking unrelated queries)

---

## 4.2 Data Handling

### 4.2.1 Data Collection

**Primary Data Source**: Blackboard LMS Export Package

| Data Type | Format | Volume | Processing |
|-----------|--------|--------|------------|
| Lecture Slides | PDF | 120 files | PyPDF2 extraction |
| Course Outline | PDF | 1 file | PyPDF2 extraction |
| Assignments | PDF/DOCX | 10 files | Multi-format parser |
| HTML Content | .dat (HTML) | 50+ files | BeautifulSoup |
| Embedded Media | Various | Ignored | Not processed |

**imsmanifest.xml Parsing:**

```xml
<!-- Blackboard uses cryptic IDs -->
<resource identifier="res00001" type="resource/x-bb-document">
  <file href="res00001.dat"/>
</resource>

<!-- Mapping extracted via -->
<item identifier="item00001" identifierref="res00001">
  <title>Week 1: Introduction to AI</title>
</item>
```

### 4.2.2 Data Preprocessing

**Text Extraction Pipeline:**

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Raw Files   │───▶│  Extraction  │───▶│   Cleaning   │───▶│   Chunking   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
     │                    │                    │                    │
     │                    │                    │                    │
     ▼                    ▼                    ▼                    ▼
 PDF, DOCX,         PyPDF2,            - Remove headers        1000 char
 HTML, TXT        python-docx,         - Strip footers         chunks with
                 BeautifulSoup         - Normalize whitespace  200 overlap
                                       - Handle LaTeX
```

**Cleaning Operations:**

```python
def clean_text(text: str) -> str:
    # Remove page headers/footers (common in PDFs)
    text = re.sub(r'Page \d+ of \d+', '', text)
    text = re.sub(r'COMP 237.*?Centennial College', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Preserve LaTeX equations (important for math content)
    # But ensure proper escaping
    text = re.sub(r'\$\$(.*?)\$\$', r'[EQUATION: \1]', text)
    
    return text.strip()
```

### 4.2.3 Data Storage

**Vector Store (ChromaDB):**

```python
# Collection configuration
collection = chroma_client.get_or_create_collection(
    name="COMP237",
    metadata={"hnsw:space": "l2"},
    embedding_function=GoogleGenerativeAiEmbeddingFunction(
        model_name="models/embedding-001",
        api_key=settings.google_api_key
    )
)

# Document insertion
collection.add(
    documents=[chunk.page_content for chunk in chunks],
    metadatas=[{
        "source_file": chunk.metadata["source"],
        "page": chunk.metadata.get("page", 0),
        "course_id": "COMP237",
        "chunk_id": f"chunk_{i:05d}"
    } for i, chunk in enumerate(chunks)],
    ids=[str(uuid.uuid4()) for _ in chunks]
)
```

**Relational Database (Supabase/PostgreSQL):**

```sql
-- Student mastery tracking
CREATE TABLE student_mastery (
    user_id UUID REFERENCES auth.users(id),
    concept_tag TEXT NOT NULL,
    mastery_score FLOAT CHECK (mastery_score BETWEEN 0 AND 1),
    decay_factor FLOAT DEFAULT 0.95,
    last_assessed_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, concept_tag)
);

-- Interaction logging
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES auth.users(id),
    type TEXT CHECK (type IN ('question', 'quiz', 'code_execution')),
    concept_focus TEXT,
    outcome TEXT,
    intent TEXT,
    agent_used TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2.4 Data Quality Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| Document coverage | 100% of course materials | 100% ✅ |
| Chunk success rate | >95% clean chunks | 98% ✅ |
| Embedding generation | 100% of chunks | 100% ✅ |
| Metadata completeness | All chunks have source | 100% ✅ |

---

## 4.3 Model Development

### 4.3.1 Agent State Architecture

The agent uses a typed state dictionary that flows through the LangGraph pipeline:

```python
class AgentState(TypedDict):
    # User Input
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    
    # User Context
    user_id: Optional[str]
    user_email: Optional[str]
    user_role: Optional[Literal["student", "admin"]]
    
    # Routing Decisions
    intent: Optional[str]  # "tutor", "math", "coder", "syllabus", "fast"
    model_selected: Optional[str]
    
    # RAG Context
    retrieved_context: List[dict]
    context_sources: List[dict]
    
    # Policy Enforcement
    governor_approved: bool
    governor_reason: Optional[str]
    
    # Pedagogical State
    scaffolding_level: Optional[ScaffoldingLevel]  # "hint", "guided", "explained"
    student_confusion_detected: bool
    thinking_steps: Optional[List[ThinkingStep]]
    bloom_level: Optional[BloomLevel]
    
    # Response
    response: Optional[str]
    error: Optional[str]
```

### 4.3.2 LangGraph Workflow Construction

```python
def create_tutor_agent() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("governor", governor_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("pedagogical_tutor", pedagogical_tutor_node)
    workflow.add_node("math_agent", math_agent_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tutor_tools))
    workflow.add_node("evaluator", evaluator_node)
    
    # Set entry point
    workflow.set_entry_point("governor")
    
    # Conditional edges
    workflow.add_conditional_edges(
        "governor",
        should_continue,
        {"continue": "supervisor", "end": END}
    )
    
    workflow.add_conditional_edges(
        "supervisor",
        route_by_intent,
        {
            "pedagogical_tutor": "pedagogical_tutor",
            "math_agent": "math_agent",
            "agent": "agent"
        }
    )
    
    # Tool loop
    workflow.add_conditional_edges(
        "agent",
        route_agent_output,
        {"tools": "tools", "evaluator": "evaluator"}
    )
    workflow.add_edge("tools", "post_tools")
    workflow.add_edge("post_tools", "agent")
    
    # Terminal edges
    workflow.add_edge("pedagogical_tutor", "evaluator")
    workflow.add_edge("math_agent", "evaluator")
    workflow.add_edge("evaluator", END)
    
    return workflow.compile()
```

### 4.3.3 Prompt Engineering

**System Prompt (Base):**

```python
SYSTEM_PROMPT = """You are Course Marshal, an AI tutor for COMP 237: Introduction to AI at Centennial College.

CAPABILITIES:
1. Answer questions about AI/ML concepts covered in COMP 237
2. Explain mathematical foundations (linear algebra, calculus, probability)
3. Guide students through code implementation (Python, scikit-learn)
4. Provide course logistics information (schedule, deadlines)

CONSTRAINTS:
1. Only answer questions within COMP 237 scope
2. Never provide complete solutions for graded assignments
3. Use Socratic method - guide discovery, don't just give answers
4. Always cite sources from course materials

PEDAGOGICAL APPROACH:
- Assess student's current understanding before explaining
- Provide scaffolded support (hint → example → explanation)
- Ask follow-up questions to verify comprehension
- Adapt language complexity to student level
"""
```

**Pedagogical Tutor Prompt:**

```python
SOCRATIC_TUTOR_PROMPT = """You are a Socratic tutor. Your role is to guide 
students to understanding through questioning, not direct answers.

APPROACH:
1. First, ask a clarifying question to assess their current understanding
2. If confused, provide a hint or analogy
3. If partially correct, guide them to complete understanding
4. If incorrect, gently redirect without making them feel wrong

SCAFFOLDING LEVELS:
- HINT: Just a nudge in the right direction
- GUIDED: Step-by-step questions leading to answer
- EXPLAINED: Full explanation with examples (only if struggling)

Current student confusion level: {confusion_detected}
Current scaffolding level: {scaffolding_level}
"""
```

### 4.3.4 Hyperparameter Tuning

| Parameter | Initial | Tuned | Rationale |
|-----------|---------|-------|-----------|
| Gemini Temperature (Tutor) | 0.7 | 0.9 | Higher creativity for Socratic responses |
| Gemini Temperature (General) | 0.7 | 0.7 | Balanced factual/creative |
| Groq Temperature (Code) | 0.7 | 0.5 | Lower for deterministic code output |
| RAG k (results) | 3 | 5 | More context improves grounding |
| Scope Threshold | 1.0 | 0.80 | Empirically tuned for coverage |
| Chunk Size | 500 | 1000 | Better context preservation |
| Chunk Overlap | 50 | 200 | Maintain cross-chunk coherence |

---

## 4.4 Full Stack Implementation

### 4.4.1 Backend Architecture (FastAPI)

**Project Structure:**

```
backend/
├── main.py                 # FastAPI app entry point
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py     # /api/chat/stream endpoint
│   │   │   ├── admin.py    # /api/admin/* endpoints
│   │   │   ├── execute.py  # /api/execute (E2B)
│   │   │   └── mastery.py  # /api/mastery/* endpoints
│   │   └── middleware.py   # JWT authentication
│   ├── agents/
│   │   ├── tutor_agent.py  # LangGraph orchestration
│   │   ├── governor.py     # Policy enforcement
│   │   ├── supervisor.py   # Intent routing
│   │   └── state.py        # AgentState definition
│   ├── rag/
│   │   ├── chromadb_client.py
│   │   └── embeddings.py
│   └── etl/
│       ├── pipeline.py
│       └── document_processor.py
└── requirements.txt
```

**Streaming Chat Endpoint:**

```python
@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user_info: dict = Depends(require_auth)
):
    async def generate_stream():
        async for event in astream_agent(
            query=request.messages[-1].content,
            user_id=user_info["user_id"],
            user_email=user_info["email"]
        ):
            if event["type"] == "text-delta":
                yield f"0:{json.dumps(event['textDelta'])}\n"
            elif event["type"] == "tool-call":
                yield f"9:{json.dumps({'toolName': event['toolName']})}\n"
            elif event.get("sources"):
                yield f"2:{json.dumps(event['sources'])}\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )
```

### 4.4.2 Frontend Architecture (Plasmo/React)

**Extension Structure:**

```
extension/
├── src/
│   ├── sidepanel.tsx           # Student chat entry point
│   ├── admin-sidepanel.tsx     # Admin dashboard entry
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── ai-elements/
│   │   │   ├── ThinkingAccordion.tsx
│   │   │   ├── QuizCard.tsx
│   │   │   └── CodeBlock.tsx
│   │   └── auth/
│   │       └── LoginForm.tsx
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   └── use-chat.ts
│   └── lib/
│       ├── supabase.ts
│       └── api.ts
├── assets/
│   └── icon.png
└── package.json
```

**React Chat Hook:**

```typescript
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (content: string) => {
    setIsLoading(true);
    
    // Optimistic update
    setMessages(prev => [...prev, { role: 'user', content }]);
    
    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: JSON.stringify({ messages: [...messages, { role: 'user', content }] })
      });
      
      // Stream response
      const reader = response.body?.getReader();
      let assistantMessage = '';
      
      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;
        
        const chunk = new TextDecoder().decode(value);
        // Parse SSE format and update message
        assistantMessage += parseChunk(chunk);
        setMessages(prev => updateLastAssistant(prev, assistantMessage));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading };
}
```

### 4.4.3 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User enters email in Chrome Extension                                   │
│                                                                             │
│  2. Email domain validation:                                                │
│     - @my.centennialcollege.ca → Student role                              │
│     - @centennialcollege.ca → Admin role                                   │
│     - Other domains → Rejected                                              │
│                                                                             │
│  3. Supabase sends OTP code to email                                       │
│                                                                             │
│  4. User enters OTP code                                                   │
│                                                                             │
│  5. Supabase validates OTP, returns JWT                                    │
│                                                                             │
│  6. Extension stores JWT in secure storage                                 │
│                                                                             │
│  7. All API requests include JWT in Authorization header                   │
│                                                                             │
│  8. Backend middleware validates JWT on each request                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**JWT Validation Middleware:**

```python
async def require_auth(
    authorization: str = Header(None)
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify with Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        return {
            "user_id": payload["sub"],
            "email": payload.get("email"),
            "role": "admin" if "@centennialcollege.ca" in payload.get("email", "") 
                    else "student"
        }
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 4.4.4 Code Quality Practices

| Practice | Implementation |
|----------|---------------|
| **Type Safety** | TypeScript (frontend), Pydantic + TypedDict (backend) |
| **Code Formatting** | Prettier (JS/TS), Black (Python) |
| **Linting** | ESLint (JS/TS), Ruff (Python) |
| **Component Architecture** | Functional React with hooks |
| **API Design** | RESTful with SSE streaming |
| **Error Handling** | Try/catch blocks, HTTP status codes |
| **Logging** | Python logging module with structured output |
| **Environment Config** | .env files, pydantic-settings |

---

*This section details the technical execution of the Luminate AI Course Marshal. The following section explores the innovative aspects and technical challenges overcome during development.*
