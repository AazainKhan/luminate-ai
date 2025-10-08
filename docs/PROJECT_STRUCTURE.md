# Luminate AI - Project Structure

## Core Components

### Chrome Extension (`chrome-extension/`)
- **Main Entry Points:**
  - `src/popup/` - Extension popup interface
  - `src/sidepanel/` - Side panel interface
  - `src/background/` - Background service worker
  - `src/content/` - Content script for Luminate pages

- **Key Components:**
  - `src/components/DualModeChat.tsx` - Main chat interface
  - `src/components/NavigateMode.tsx` - Quick Q&A mode
  - `src/components/EducateMode.tsx` - Learning mode with study plans
  - `src/components/AutoMode.tsx` - Intelligent routing

- **Build:** `npm run build` → `dist/`

### Backend (`development/backend/`)
- **Main API:**
  - `fastapi_service/main.py` - FastAPI server with LangGraph integration
  - `fastapi_service/routers/` - API endpoints (query, health, external resources)

- **LangGraph Agents:**
  - `langgraph/orchestrator.py` - Main routing logic
  - `langgraph/educate_graph.py` - Learning mode workflow
  - `langgraph/navigate_graph.py` - Navigate mode workflow
  - `langgraph/agents/` - Individual agent implementations

- **Configuration:**
  - `langgraph/llm_config.py` - LLM settings (Ollama/LLaMA)
  - `setup_chromadb.py` - Vector DB setup
  - `setup_supabase.py` - Student data storage

### Data (`chromadb_data/`)
- Vector embeddings for course content
- Managed by ChromaDB

### Tests (`tests/`)
- Consolidated test files from all locations
- `old_tests/` - Legacy test suite

## Key Features Preserved

1. **Dual Mode System:**
   - Navigate: Quick semantic search
   - Educate: Study plans, quizzes, learning paths

2. **LangGraph Integration:**
   - Intelligent routing via orchestrator
   - Agent-based architecture
   - Streaming responses

3. **Supabase Storage:**
   - Student profiles
   - Study progress
   - Quiz results

4. **ChromaDB:**
   - Course content embeddings
   - Semantic search

## Cleanup Summary

### Removed (Safe):
- Raw data folders: `extracted/`, `comp_237_content/`, `graph_seed/`
- Old ChromaDB backups
- Duplicate test directories
- 30+ session/fix/summary MD files → `docs/archive/`
- Python cache files: `__pycache__/`, `.pytest_cache/`
- Duplicate schema execution scripts (8 files)
- Test components and build reports

### Kept:
- All functional code
- LangGraph agents (main requirement)
- Supabase setup (student storage)
- Enhanced components (actively used)
- Core documentation

## Directory Size
- Total: 1.4GB
- Chrome Extension: 237MB
- Development: 1.0MB
- Tests: 232KB
- Docs Archive: 304KB

## Quick Start

1. **Backend:**
   ```bash
   cd development/backend
   pip install -r ../../requirements.txt
   python fastapi_service/main.py
   ```

2. **Extension:**
   ```bash
   cd chrome-extension
   npm install
   npm run build
   # Load dist/ in Chrome
   ```

3. **Database Setup:**
   ```bash
   python development/backend/setup_chromadb.py
   python development/backend/setup_supabase.py
   ```
