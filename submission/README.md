# Luminate AI - Submission Documentation

Welcome to the comprehensive documentation package for **Luminate AI**, an intelligent educational assistant built for COMP-237 (Artificial Intelligence) at Centennial College.

## 📁 Documentation Contents

This folder contains five detailed documents that provide complete insight into the system architecture, data flow, technology stack, and visual diagrams.

### 1. **Architecture Overview** (`1-architecture.md`)

A comprehensive guide to the system architecture covering:

- **System Components**: Frontend (Chrome Extension), Backend (FastAPI), LangGraph Agents, Databases
- **Navigate Mode Agents**: 5 specialized agents for information retrieval
- **Educate Mode Agents**: 8 agents for adaptive tutoring and math explanations
- **Deployment Architecture**: Production-ready cloud deployment strategy
- **Technology Decisions**: Rationale for React, FastAPI, LangGraph, ChromaDB choices
- **Security & Privacy**: Student anonymization, CORS protection, data encryption
- **Future Enhancements**: Algorithm visualization, interactive REPL, voice input

**Key Stats**:
- 13 total LangGraph agents
- 917 ChromaDB documents
- 30+ math formulas with 4-level explanations
- 2-4 second average response time

---

### 2. **Data Flow** (`2-data-flow.md`)

Complete tracing of how data moves through the system:

- **Ingestion Pipeline**: Blackboard export → Cleaned JSON → ChromaDB embeddings
- **Navigate Mode Query Flow**: Student input → Orchestrator → 5 agents → UI rendering
- **Educate Mode Query Flow**: Math formula detection → 4-level explanation → LaTeX rendering
- **Student Analytics**: Interaction tracking, topic mastery updates, quiz responses
- **External API Integration**: YouTube API, OER Commons resource fetching
- **Error Handling**: Connection failures, graceful degradation, user feedback
- **Performance Optimization**: Caching strategies, streaming responses

**Data Journey**:
```
Blackboard Export (909 files)
    ↓ Processing (593 processed)
ChromaDB (917 vectors × 384 dimensions)
    ↓ Runtime Query
LangGraph Workflows (Navigate/Educate)
    ↓ JSON Response
Chrome Extension UI (React + KaTeX)
    ↓ User Interaction
Supabase Analytics (PostgreSQL)
```

---

### 3. **Data Structures** (`3-data-structures.md`)

Detailed schemas and formats for all data types:

- **Cleaned JSON Schema**: Course content with Blackboard metadata
- **ChromaDB Document Structure**: 384-dim embeddings + metadata
- **API Request/Response Schemas**: TypeScript interfaces for all endpoints
- **LangGraph State Types**: NavigateState, EducateState typed dictionaries
- **Supabase Database Tables**: students, session_history, topic_mastery, quiz_responses
- **Math Translation Format**: 4-level explanation dataclass
- **External Resources**: YouTube API response transformation
- **Chrome Extension Storage**: LocalStorage schema for chat history, notes, settings

**Example Schemas**:
- Cleaned JSON: Course metadata + chunked text + live URLs
- ChromaDB: Vector embeddings + cosine similarity scores
- API Response: Mode classification + formatted markdown + resources
- Supabase: Student fingerprints + interaction logs + mastery tracking

---

### 4. **Technology Stack** (`4-tech-stack.md`)

In-depth analysis of all technologies and their integration:

#### Frontend Stack
- **React 18.2.0**: Component-based UI with hooks
- **TypeScript 5.2.2**: Type-safe development
- **Vite 5.2.0**: 10-100x faster bundling than Webpack
- **shadcn/ui**: Accessible, customizable components
- **TailwindCSS 3.4.1**: Utility-first styling
- **KaTeX 0.16.23**: Fast math rendering (10x faster than MathJax)
- **Prism.js**: Syntax highlighting for code blocks
- **framer-motion**: Declarative animations
- **lucide-react**: 1000+ optimized SVG icons

#### Backend Stack
- **FastAPI 0.115.0**: Async Python web framework
- **LangGraph 0.2.5**: Multi-agent orchestration
- **ChromaDB 0.5.0**: Embedded vector database
- **Sentence Transformers 3.0.0**: Text embeddings (384-dim)
- **Supabase**: Managed PostgreSQL + Auth
- **Google Gemini**: 2.0 Flash (Navigate) + 2.5 Flash (Educate)
- **BeautifulSoup4**: HTML parsing from Blackboard exports
- **pypdf**: PDF text extraction

#### Integration
- **HTTP REST API**: JSON over HTTP/1.1
- **CORS Configuration**: Chrome extension ↔ localhost:8000
- **Browser Fingerprinting**: Student identification without PII
- **WebSocket Support**: Streaming responses for long explanations

**Why These Technologies?**
- React: Largest ecosystem, best hiring pool
- FastAPI: 3x faster than Flask, automatic docs
- ChromaDB: Free, embedded, fast enough for 1000 docs
- LangGraph: Explicit agent control vs. black-box chains

---

### 5. **Interactive Architecture Diagram** (`5-architecture-diagram.html`)

A beautiful, interactive HTML/CSS visualization of the entire system.

**Features**:
- ✅ **Color-coded layers**: Frontend (blue), API (green), Orchestrator (orange), Agents (purple), Data (red), AI (cyan)
- ✅ **Interactive components**: Click any component for detailed description
- ✅ **Complete data flow**: Step-by-step query journey with examples
- ✅ **Responsive design**: Works on desktop, tablet, mobile
- ✅ **Smooth animations**: Fade-in effects as you scroll
- ✅ **Real statistics**: 917 documents, 30+ formulas, 2-4s response time

**How to View**:
1. Open `5-architecture-diagram.html` in any modern browser (Chrome, Firefox, Safari, Edge)
2. Scroll to explore all layers
3. Click components to see tooltips
4. View Navigate vs. Educate data flow examples

**Layers Visualized**:
1. **Frontend Layer**: DualModeChat, Navigate Mode, Educate Mode, Auto Mode
2. **API Layer**: Unified Endpoint, CORS & Auth, Health & Stats
3. **Orchestrator**: classify_query_mode() with confidence scoring
4. **Agent Layer**: 5 Navigate agents + 8 Educate agents
5. **Data Layer**: ChromaDB (917 docs), Supabase (6 tables), Course JSON (593 files)
6. **AI Models**: Gemini 2.0 Flash, Gemini 2.5 Flash, Sentence Transformers

---

## 🎯 Quick Navigation

| Document | Focus | Best For |
|----------|-------|----------|
| `1-architecture.md` | **System overview** | Understanding component relationships |
| `2-data-flow.md` | **Query journey** | Tracing how data moves end-to-end |
| `3-data-structures.md` | **Schemas & formats** | API integration, data modeling |
| `4-tech-stack.md` | **Technologies & integration** | Technology decisions, frontend-backend communication |
| `5-architecture-diagram.html` | **Visual architecture** | Quick system understanding, presentations |

---

## 📊 System Highlights

### Performance
- **Response Time**: 2-4 seconds (Navigate), 1-2 seconds (Educate with math)
- **ChromaDB Query**: <500ms for semantic search
- **Concurrent Users**: Supports 100+ simultaneous queries
- **Extension Bundle**: 1.89 MB (optimized for Chrome)

### Data Scale
- **Course Documents**: 593 processed from 909 Blackboard files
- **Vector Embeddings**: 917 chunks × 384 dimensions
- **Total Tokens**: 300,563 tokens indexed
- **Math Formulas**: 30+ with 4-level explanations

### Agent Capabilities
- **Navigate Mode**: Query understanding → ChromaDB retrieval → Context enrichment → External resources → Formatting
- **Educate Mode**: Math translation → Pedagogical planning → Student modeling → Quiz generation → Study planning

---

## 🚀 Getting Started with the Code

### Prerequisites
```bash
# Backend
Python 3.12+
ChromaDB setup (917 documents)
Google Gemini API key
Supabase account (optional for analytics)

# Frontend
Node.js 18+
Chrome browser (for extension testing)
```

### Run Backend
```bash
cd development/backend
source .venv/bin/activate
pip install -r requirements.txt
python scripts/start_backend.py  # Starts on localhost:8000
```

### Build Extension
```bash
cd chrome-extension
npm install
npm run build  # Outputs to dist/
```

### Load Extension
1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `chrome-extension/dist/`

---

## 🔍 How to Use These Documents

### For Technical Review
1. Start with `5-architecture-diagram.html` for visual overview
2. Read `1-architecture.md` for component details
3. Check `4-tech-stack.md` for technology rationale

### For API Integration
1. Study `3-data-structures.md` for request/response schemas
2. Review `2-data-flow.md` for query processing steps
3. Reference `4-tech-stack.md` for CORS and authentication

### For Understanding Data Pipeline
1. Read `2-data-flow.md` section "Data Ingestion Pipeline"
2. Check `3-data-structures.md` for ChromaDB schema
3. View `5-architecture-diagram.html` data layer

### For Scaling & Deployment
1. Review `1-architecture.md` "Scalability Considerations"
2. Check `4-tech-stack.md` "Performance Optimizations"
3. Study `2-data-flow.md` "Caching Strategy"

---

## 📝 Document Statistics

| Document | Lines | Words | Topics Covered |
|----------|-------|-------|----------------|
| 1-architecture.md | 450+ | 4,500+ | Architecture, Components, Deployment |
| 2-data-flow.md | 650+ | 6,000+ | Pipelines, Queries, Analytics |
| 3-data-structures.md | 850+ | 7,500+ | Schemas, Formats, Examples |
| 4-tech-stack.md | 750+ | 6,500+ | Technologies, Integration, Rationale |
| 5-architecture-diagram.html | 900+ | N/A | Interactive Visualization |

**Total**: 3,600+ lines of documentation covering every aspect of Luminate AI

---

## 🎓 Educational Context

**Course**: COMP-237 Artificial Intelligence  
**Institution**: Centennial College  
**Purpose**: Intelligent tutoring system for AI course content  
**Target Users**: 100+ students per semester

**Learning Modes**:
- **Navigate Mode**: Quick Q&A, resource discovery, semantic search
- **Educate Mode**: Deep explanations, math formulas, quizzes, study plans
- **Auto Mode**: Intelligent routing based on query intent

---

## 🤝 Contributing

These documents are living artifacts. To update:

1. **Architecture changes**: Update `1-architecture.md` + `5-architecture-diagram.html`
2. **New data flows**: Add to `2-data-flow.md` with examples
3. **Schema changes**: Update `3-data-structures.md` with new formats
4. **Tech stack updates**: Document in `4-tech-stack.md` with rationale

---

## 📧 Contact & Support

For questions about the architecture or implementation:

1. Review these documents thoroughly
2. Check inline code comments in `development/backend/` and `chrome-extension/src/`
3. Run tests: `npm test` (frontend) or `python -m pytest` (backend)

---

## ✨ Final Notes

This documentation package represents **extreme detail** exploration of the Luminate AI codebase. Every component, data flow, schema, and technology decision has been carefully documented to provide a complete understanding of the system.

**Key Strengths**:
- ✅ Comprehensive coverage of all system layers
- ✅ Visual + textual documentation for different learning styles
- ✅ Real-world examples with actual code snippets
- ✅ Performance metrics and scalability considerations
- ✅ Technology rationale for informed decision-making

**Use Cases**:
- 📚 Onboarding new developers
- 🎯 Technical presentations to stakeholders
- 🔧 API integration for third-party tools
- 📊 System audits and security reviews
- 🚀 Deployment planning and scaling

---

**Documentation Version**: 1.0  
**Last Updated**: October 7, 2025  
**Status**: ✅ Complete and Production-Ready
