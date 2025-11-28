# AI Tutor Project Handover Document

**Date:** November 27, 2025  
**Project:** COMP237 AI Tutor for Centennial College Luminate LMS

---

## 1. Project Overview

An AI-powered tutoring chatbot that integrates with Centennial College's Luminate LMS as a Chrome extension. The system uses a **multi-agent architecture** with RAG (Retrieval-Augmented Generation) to provide scaffolding-based tutoring for the COMP237 (Intro to AI) course.

### Key Features
- Chrome extension that injects chatbot into Luminate pages
- Scaffolding-based pedagogy (guides students, doesn't give direct answers)
- RAG retrieval from COMP237 course materials
- Multi-agent system with specialized agents for different tasks
- Conversation history persistence via PostgreSQL
- Course scope enforcement (politely declines off-topic questions)

---

## 2. Tech Stack

### Backend
| Component | Technology | Details |
|-----------|------------|---------|
| **API Framework** | FastAPI | REST API with CORS support |
| **Server** | Uvicorn | ASGI server with hot reload |
| **LLM** | Google Gemini 2.0 Flash | via `langchain-google-genai` |
| **Agent Framework** | LangGraph | StateGraph-based multi-agent orchestration |
| **Vector Database** | ChromaDB | Persistent storage at `./chroma_db` |
| **Relational Database** | PostgreSQL 15 | localhost:5432, db: `ai_tutor`, user: `reet` |
| **Language** | Python 3.11 | Using pipenv for dependency management |

### Frontend
| Component | Technology | Details |
|-----------|------------|---------|
| **Chrome Extension** | Manifest V3 | Content script injection |
| **Target Site** | luminate.centennialcollege.ca | Centennial College LMS |

### Key Dependencies
```
langchain, langgraph, langchain-google-genai, langchain-chroma
chromadb
fastapi, uvicorn
psycopg2-binary
beautifulsoup4, lxml
pydantic, python-dotenv
```

---

## 3. Project Structure

```
AiTutor/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── Pipfile                 # Pipenv dependencies
│
├── agents/                 # Multi-agent system
│   ├── planner_agent.py    # Routes queries to appropriate agent
│   ├── planner_heuristics.py # Rule-based routing fallback
│   ├── tutor_agent.py      # Main tutoring agent with scaffolding
│   ├── math_agent.py       # Mathematical problem solver
│   └── feedback_agent.py   # Analytics and feedback processing
│
├── graph/
│   └── graph_ai.py         # LangGraph StateGraph definition
│
├── tools/
│   ├── db.py               # PostgreSQL operations
│   ├── rag_tool.py         # ChromaDB retrieval wrapper
│   ├── math_tool.py        # Symbolic math operations
│   └── run_feedback_job.py # Batch analytics job
│
├── prompts/
│   ├── planner_prompts.py  # Planner system/user prompts
│   └── math_prompts.py     # Math agent prompts
│
├── schemas/
│   ├── planner.py          # Pydantic models for planner
│   ├── math.py             # Math agent schemas
│   └── shared.py           # Shared data models
│
├── config/
│   └── chroma_config.py    # ChromaDB settings
│
├── data/
│   ├── sql/
│   │   └── feedback_schema.sql  # PostgreSQL schema
│   ├── ExportFile_COMP237_INP 2/  # Blackboard export (396 .dat files)
│   ├── 01_ingest_comp237.py      # Course content ingestion
│   ├── 02_ingest_oer.py          # OER resources ingestion
│   └── ingest_core.py            # Shared ingestion utilities
│
├── chroma_db/              # ChromaDB persistent storage
│
└── chrome-extension/
    ├── manifest.json       # Extension manifest v3
    ├── contentScript.js    # Chatbot UI injection
    └── styles.css          # Chatbot styling
```

---

## 4. Agentic Design Pattern

### Multi-Agent Architecture (LangGraph StateGraph)

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │   Planner   │  ← Classifies query into subtasks
                    │   Agent     │    (explain, solve, reject, chat)
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │   Router    │  ← Picks next subtask
                    │    Node     │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Tutor   │    │   Math   │    │  Reject  │
    │  Agent   │    │  Agent   │    │   Node   │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
                  ┌─────────────┐
                  │   Router    │  ← Check for more subtasks
                  │   (loop)    │
                  └──────┬──────┘
                         ▼
                  ┌─────────────┐
                  │  Feedback   │  ← Final processing
                  │    Node     │
                  └──────┬──────┘
                         ▼
                    ┌─────────────┐
                    │    END      │
                    └─────────────┘
```

### Agent Responsibilities

| Agent | Purpose | Key Features |
|-------|---------|--------------|
| **PlannerAgent** | Query classification & routing | LLM-first with heuristic fallback, produces subtasks |
| **TutorAgent** | Conceptual explanations | Scaffolding pedagogy, RAG retrieval, stuck student detection |
| **MathAgent** | Mathematical problem solving | Symbolic computation with SymPy, step-by-step solutions |
| **FeedbackAgent** | Analytics & insights | Batch processing of conversation quality |

### Task Types (from Planner)
```python
class TaskType(str, Enum):
    EXPLAIN = "explain"    # → TutorAgent
    SOLVE = "solve"        # → MathAgent  
    REJECT = "reject"      # → Reject node (off-topic)
    CHAT = "chat"          # → General conversation
```

---

## 5. Data Sources

### ChromaDB Collections

| Collection | Content | Documents | Source |
|------------|---------|-----------|--------|
| `course_comp237` | COMP237 course materials | ~339 chunks | Blackboard export (396 .dat files) |
| `oer_resources` | Open Educational Resources | 0 (not populated) | External AI/ML resources |

**Ingestion Process:**
1. `.dat` files from Blackboard export are parsed
2. HTML content cleaned with BeautifulSoup
3. Text chunked (400 words, 80-word overlap)
4. Embedded and stored in ChromaDB

**Ingestion Script:** `ingest_comp237_content.py`

### PostgreSQL Tables

```sql
-- Chat logs (conversation history)
CREATE TABLE chat_logs (
    conversation_id TEXT NOT NULL,
    turn_index      INT  NOT NULL,
    role            TEXT NOT NULL,   -- 'student' or 'assistant'
    agent           TEXT,            -- 'PlannerAgent' | 'TutorAgent' | 'MathAgent'
    content         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Conversation ratings
CREATE TABLE conversation_ratings (
    conversation_id TEXT PRIMARY KEY,
    rating          INT NOT NULL,    -- 1–5 stars
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Analytics insights
CREATE TABLE analytics_insights (
    id                     SERIAL PRIMARY KEY,
    conversation_id        TEXT,
    topic                  TEXT,
    primary_agent          TEXT,
    severity               TEXT,
    requires_human_review  BOOLEAN DEFAULT TRUE,
    summary                TEXT,
    raw_json               JSONB,
    generated_at           TIMESTAMP DEFAULT NOW()
);
```

---

## 6. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Main tutoring endpoint - accepts question, returns AI response |
| `/rate` | POST | Save conversation rating (1-5 stars) |
| `/feedback/run` | POST | Trigger batch feedback analysis |

### `/ask` Request/Response

**Request:**
```json
{
    "question": "What is A* search?",
    "conversation_id": "conv_123...",  // optional, auto-generated if not provided
    "turn_index": 0                     // optional
}
```

**Response:**
```json
{
    "conversation_id": "conv_123...",
    "output": "A* search is...",
    "student_input": "What is A* search?",
    "plan": {...},
    "outputs": [...],
    "rag_metadata": {
        "docs_retrieved": 3,
        "sources_used": ["course_comp237"],
        "has_comp237": true
    },
    "routing_info": {...},
    "status": "success"
}
```

---

## 7. Key Implementation Details

### Conversation History Flow
1. **Storage:** Each message logged to PostgreSQL `chat_logs` table
2. **Retrieval:** `get_conversation_history()` fetches last 10 messages
3. **Passed to Graph:** `conversation_history` in state dict
4. **Used by TutorAgent:** Extracts previous topic when student says "I don't understand"

### Topic Extraction Logic (tutor_agent.py)
When student sends follow-up like "I didn't understand":
1. System looks backwards through conversation history
2. Skips "stuck phrases" (i don't know, no, etc.)
3. Finds last substantive question (e.g., "what is A* search")
4. Uses that topic for RAG retrieval instead of generic "clarification needed"

### RAG Retrieval (DirectRAGRetriever)
1. Query both `course_comp237` and `oer_resources` collections
2. Apply similarity threshold (0.35) for comp237 documents
3. If comp237 docs found → in-scope mode (full explanation)
4. If no comp237 docs → out-of-scope mode (one-line answer)

### Scaffolding Pedagogy
- Starts with Socratic questions to guide thinking
- Detects when student is "stuck" (repeated "I don't know")
- Switches to concrete examples after 2+ stuck responses
- Avoids giving direct answers unless student is truly stuck

---

## 8. Current Status & Known Issues

### ✅ Working
- ChromaDB with 339 COMP237 documents
- PostgreSQL conversation logging
- Multi-agent routing (Planner → Tutor/Math/Reject)
- Chrome extension injection on Luminate pages
- Scaffolding-based tutoring prompts
- RAG retrieval from course materials

### ⚠️ Partially Working
- Topic extraction for follow-ups (sometimes misses topic)
- Stuck student detection (occasionally still asks questions when should explain)

### ❌ Known Issues
1. **Topic Loss on Follow-ups:** When student says "I didn't understand", tutor sometimes explains wrong topic (heuristics instead of A* search)
2. **Generic Planner Topics:** Planner returns "clarification needed on previous topic" which doesn't help RAG retrieval
3. **OER Collection Empty:** `oer_resources` collection not populated

### 🔧 Recent Fixes Applied
- Added `conversation_history` to tutor_state in graph_ai.py
- Added topic extraction logic to detect previous substantive question
- Expanded generic topic phrase detection list

---

## 9. How to Run

### Prerequisites
- Python 3.11+
- PostgreSQL 15
- Google API Key (Gemini)

### Setup
```bash
# 1. Install dependencies
cd "/Users/adarshsprabhan/Desktop/AiTutor "
pipenv install

# 2. Start PostgreSQL
brew services start postgresql@15

# 3. Initialize database (if not done)
psql -U reet -d ai_tutor -f data/sql/feedback_schema.sql

# 4. Set environment variables
export GOOGLE_API_KEY="your-api-key"

# 5. Start server
pipenv run uvicorn main:app --reload
```

### Chrome Extension
1. Open Chrome → `chrome://extensions`
2. Enable Developer Mode
3. Load Unpacked → Select `chrome-extension/` folder
4. Navigate to luminate.centennialcollege.ca

---

## 10. Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | Set in main.py (hardcoded) |

### PostgreSQL Config (tools/db.py)
```python
PG_OPTS = {
    "host": "localhost",
    "port": 5432,
    "user": "reet",
    "password": "",
    "dbname": "ai_tutor"
}
```

---

## 11. Next Steps / Recommendations

1. **Fix Topic Persistence:** Consider passing the actual topic in planner output instead of generic phrases
2. **Populate OER Collection:** Add open educational resources for broader coverage
3. **Add User Authentication:** Currently no auth - each conversation is anonymous
4. **Implement Feedback Analytics:** FeedbackAgent exists but not fully utilized
5. **Improve Stuck Detection:** Use turn count or sentiment analysis
6. **Add Unit Tests:** No test coverage currently
7. **Move Secrets to .env:** API key is hardcoded in main.py

---

## 12. Contact / Handover Notes

**Original Developer:** Adarsh  
**Handover Date:** November 27, 2025

The codebase follows a modular agent design pattern using LangGraph. Each agent has its own file in `agents/` with clear responsibilities. The main orchestration happens in `graph/graph_ai.py` which builds the StateGraph.

Key files to understand first:
1. `main.py` - Entry point, API endpoints
2. `graph/graph_ai.py` - LangGraph state machine
3. `agents/tutor_agent.py` - Main tutoring logic (largest file)
4. `tools/db.py` - Database operations

Good luck! 🚀
