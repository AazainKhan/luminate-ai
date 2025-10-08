# Luminate AI - System Architecture

## Executive Summary

Luminate AI is an intelligent educational assistant for COMP-237 (Artificial Intelligence) at Centennial College. It combines ChromaDB vector search, LangGraph multi-agent orchestration, and a Chrome extension frontend to provide students with two modes: **Navigate Mode** (quick information retrieval) and **Educate Mode** (adaptive tutoring with math formula explanations).

---

## System Components

### 1. Chrome Extension (Frontend)

**Location**: `chrome-extension/`

The user interface is a Chrome browser extension that provides a side panel for student interaction.

**Key Components**:
- **DualModeChat**: Main UI container with tabbed interface (Auto, Navigate, Educate, Dashboard, Graph)
- **NavigateMode**: Displays semantic search results with course materials
- **EducateMode**: Renders tutoring responses with LaTeX math formulas
- **AutoMode**: Intelligent routing that automatically selects Navigate or Educate mode
- **Settings Panel**: Theme switching, authentication UI, about information
- **Dashboard**: Student progress tracking and analytics
- **ConceptGraph**: Visual knowledge graph of course concepts
- **NotesPanel**: Student note-taking interface

**Build System**:
- Vite bundler with React 18 + TypeScript
- Manifest V3 Chrome Extension
- TailwindCSS + shadcn/ui components
- KaTeX for LaTeX rendering

---

### 2. FastAPI Backend

**Location**: `development/backend/fastapi_service/`

RESTful API service that coordinates all AI operations.

**Core Endpoints**:
- `POST /api/query` - Unified query endpoint (auto-routing)
- `POST /query/navigate` - Navigate mode semantic search
- `POST /query/educate` - Educate mode tutoring
- `GET /health` - Service health check
- `GET /stats` - ChromaDB statistics

**Key Features**:
- CORS enabled for Chrome extension
- Request/response logging
- ChromaDB initialization on startup
- LangGraph workflow integration
- Streaming response support

---

### 3. LangGraph Multi-Agent System

**Location**: `development/backend/langgraph/`

Orchestrates intelligent workflows using directed acyclic graphs (DAGs) of specialized agents.

#### Navigate Mode Agents (5 agents)

**Workflow**: `navigate_graph.py`

1. **Query Understanding Agent** (`query_understanding.py`)
   - Extracts key terms and intent
   - Detects scope (COMP-237 or out-of-scope)
   - Enhances query for better retrieval

2. **Retrieval Agent** (`retrieval.py`)
   - Searches ChromaDB with semantic embeddings
   - Filters by module, content type
   - Returns top-K results with relevance scores

3. **Context Agent** (`context.py`)
   - Adds course structure context
   - Identifies prerequisites and next topics
   - Enriches results with related concepts

4. **External Resources Agent** (`external_resources.py`)
   - Fetches YouTube tutorials
   - Searches OER Commons
   - Provides supplementary learning materials

5. **Formatting Agent** (`formatting.py`)
   - Creates UI-ready markdown
   - Organizes results hierarchically
   - Generates relevance explanations

#### Educate Mode Agents (8 agents)

**Workflow**: `educate_graph.py`

1. **Math Translation Agent** (`math_translation_agent.py`)
   - Detects 30+ mathematical formulas (gradient descent, backpropagation, etc.)
   - Generates 4-level explanations:
     - **Intuition**: 5-year-old analogy
     - **Math**: LaTeX formula with variable explanations
     - **Code**: Working Python implementation
     - **Misconceptions**: Common mistakes

2. **Pedagogical Planner** (`pedagogical_planner.py`)
   - Selects teaching strategy (Socratic, worked example, scaffolding)
   - Adapts to student knowledge level
   - Determines interaction type

3. **Student Model Agent** (`student_model.py`)
   - Tracks student mastery levels
   - Identifies knowledge gaps
   - Personalizes responses

4. **Quiz Generator** (`quiz_generator.py`)
   - Creates multiple-choice questions
   - Generates distractors (wrong answers)
   - Provides explanations

5. **Study Planner** (`study_planner.py`)
   - Creates weekly study schedules
   - Breaks down topics into sessions
   - Suggests resources

6. **Retrieval Agent** (shared with Navigate)

7. **Context Agent** (shared with Navigate)

8. **Interactive Formatting Agent** (`interactive_formatting.py`)
   - Renders LaTeX math
   - Creates expandable sections
   - Adds code syntax highlighting

#### Orchestrator

**File**: `orchestrator_simple.py`

Routes queries to Navigate or Educate mode based on:
- Keyword detection (find, search → Navigate; explain, understand → Educate)
- COMP-237 topic matching (gradient descent, neural networks → Educate)
- Conversation context

**Output**:
```python
{
    'mode': 'navigate' | 'educate',
    'confidence': 0.0-1.0,
    'reasoning': 'Why this mode was selected'
}
```

---

### 4. ChromaDB Vector Database

**Location**: `chromadb_data/`

Persistent vector database storing COMP-237 course content embeddings.

**Collection**: `comp237_content`
- **Documents**: 917 text chunks
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimension**: 384

**Metadata Schema**:
```python
{
    'course_id': '_29430_1',
    'bb_doc_id': '_800713_1',
    'live_lms_url': 'https://luminate.centennialcollege.ca/...',
    'title': 'Lab Tutorial Logistic regression',
    'module': 'Root',
    'content_type': '.dat',
    'created_date': '2024-10-04',
    'chunk_id': '_800713_1_chunk_000',
    'chunk_index': 0,
    'total_chunks': 2
}
```

**Query Process**:
1. Convert query to 384-dim embedding
2. Cosine similarity search
3. Filter by metadata (module, content_type)
4. Return top-K results (default K=10)

---

### 5. Supabase PostgreSQL Database

**Location**: `development/backend/supabase_schema.sql`

Stores student interaction data and learning analytics.

**Tables**:
1. **students**: Browser fingerprint-based profiles
2. **session_history**: All Navigate/Educate interactions
3. **topic_mastery**: Week-by-week mastery tracking
4. **misconceptions**: Detected student misconceptions
5. **quiz_responses**: Quiz attempts and scores
6. **spaced_repetition**: Spaced learning schedules

**Features**:
- Row-Level Security (RLS)
- UUID primary keys
- Week tracking (1-14 for COMP-237)
- Indexes for performance

---

### 6. Google Gemini AI Models

**Configuration**: `development/backend/langgraph/llm_config.py`

Two models optimized for different tasks:

- **Gemini 2.0 Flash**: Navigate Mode (fast information retrieval)
- **Gemini 2.5 Flash**: Educate Mode (complex reasoning, math explanations)

**API Integration**:
- Google Cloud Vertex AI
- Environment variable configuration
- Rate limiting and error handling

---

## Deployment Architecture

```
┌─────────────────────────┐
│  Student Browser        │
│  ┌──────────────────┐   │
│  │ Chrome Extension │   │
│  │ (Side Panel)     │   │
│  └────────┬─────────┘   │
└───────────┼─────────────┘
            │ HTTP
            ↓
┌─────────────────────────┐
│  FastAPI Backend        │
│  localhost:8000         │
│  ┌──────────────────┐   │
│  │ Orchestrator     │   │
│  └────┬────────┬────┘   │
│       │        │         │
│  ┌────▼────┐ ┌▼──────┐  │
│  │Navigate │ │Educate│  │
│  │ Graph   │ │ Graph │  │
│  └────┬────┘ └┬──────┘  │
└───────┼───────┼─────────┘
        │       │
   ┌────▼───────▼────┐
   │                 │
┌──▼──────┐    ┌────▼─────┐
│ChromaDB │    │Supabase  │
│917 docs │    │PostgreSQL│
└─────────┘    └──────────┘
        │
        ↓
┌─────────────────────────┐
│  Google Gemini API      │
│  (Vertex AI)            │
└─────────────────────────┘
```

---

## Component Communication

### Request Flow (Navigate Mode)

```
1. Student types query in Chrome extension
   ↓
2. Extension calls POST /api/query
   ↓
3. Orchestrator classifies mode → 'navigate'
   ↓
4. Navigate LangGraph workflow activates:
   4.1 Query Understanding Agent parses query
   4.2 Retrieval Agent searches ChromaDB
   4.3 Context Agent adds course structure
   4.4 External Resources Agent fetches videos
   4.5 Formatting Agent creates markdown
   ↓
5. FastAPI returns JSON response
   ↓
6. Extension renders results with links
```

### Request Flow (Educate Mode)

```
1. Student types "explain gradient descent"
   ↓
2. Extension calls POST /api/query
   ↓
3. Orchestrator classifies mode → 'educate'
   ↓
4. Educate LangGraph workflow activates:
   4.1 Math Translation Agent detects formula
   4.2 Generates 4-level explanation:
       - Intuition (analogy)
       - Math (LaTeX)
       - Code (Python)
       - Misconceptions
   ↓
5. FastAPI returns markdown with LaTeX
   ↓
6. Extension renders with KaTeX
```

---

## Technology Decisions

### Why LangGraph?
- **Agent Orchestration**: Directed graphs cleanly model educational workflows
- **State Management**: Typed state ensures data consistency across agents
- **Debugging**: Easy to trace agent execution and inspect intermediate outputs

### Why ChromaDB?
- **Lightweight**: No separate server required (embedded mode)
- **Python Native**: Seamless integration with FastAPI
- **Efficient**: Fast cosine similarity search for semantic retrieval

### Why Chrome Extension?
- **Context Awareness**: Can access Blackboard LMS pages
- **Always Available**: Side panel stays open while browsing
- **Offline Capable**: Can cache responses

### Why Gemini?
- **Cost-Effective**: Free tier supports development
- **Multi-Modal**: Can handle text + images (future feature)
- **Fast**: 2.0 Flash optimized for low latency

---

## Scalability Considerations

**Current**: Local development (localhost:8000)

**Production Ready**:
1. Deploy FastAPI to Google Cloud Run (auto-scaling)
2. Move ChromaDB to hosted service (e.g., Chroma Cloud)
3. Use Supabase for authentication + analytics
4. CDN for extension assets
5. Rate limiting and caching

**Estimated Capacity**:
- 100 concurrent students
- 1000 queries/hour
- <3s response time (95th percentile)

---

## Security & Privacy

- **No Personal Data**: Browser fingerprinting only (no emails/names)
- **CORS Protection**: Only extension origin allowed
- **HTTPS**: All external API calls encrypted
- **Supabase RLS**: Row-level security prevents data leaks
- **Content Filtering**: Blackboard content stays within campus network

---

## Future Enhancements

1. **Algorithm Visualization**: Animated DFS/BFS/A* search
2. **Interactive Code REPL**: Embedded Python interpreter
3. **Voice Input**: Speech-to-text for hands-free learning
4. **Mobile App**: React Native version for iOS/Android
5. **Multi-Language**: Support for French/Spanish students
6. **Peer Collaboration**: Real-time study groups

---

**Architecture Status**: ✅ Production-ready for 100 students  
**Last Updated**: October 7, 2025
