# Luminate AI Development Folder

This folder contains all active development work for the Luminate AI Chrome extension chatbot.

## Structure

```
development/
├── docs/                  # Project documentation
│   ├── README.md                          # Main project guide
│   ├── SETUP_GUIDE.md                     # Quick start instructions
│   ├── PROJECT_SUMMARY.md                 # Deliverables overview
│   ├── PROCESSING_SUMMARY.md              # Data pipeline results
│   ├── BLACKBOARD_URL_MAPPING.md          # URL structure reference
│   ├── URL_VERIFICATION_REPORT.md         # URL validation results
│   ├── CHATBOT_INTEGRATION_SUMMARY.md     # Chatbot integration guide
│   └── plan.md                            # 7-phase development roadmap
│
├── tests/                 # Integration and unit tests
│   ├── README.md                          # Testing documentation
│   ├── test_integration.py                # Phase 2 validation suite
│   └── logs/                              # Test execution logs
│
└── backend/               # Backend services (Phase 3+)
    └── (coming soon: ChromaDB, FastAPI, LangGraph)
```

## Current Status

### ✅ Phase 2 Complete: Data Ingestion
- **593 JSON files** with structured course content
- **1,296 graph relationships** (CONTAINS, NEXT_IN_MODULE, PREV_IN_MODULE)
- **160 live Blackboard URLs** with correct COMP237 course ID
- **917 chunks** with 300K tokens
- **Integration tests**: All 9 tests passing

### 🔄 Phase 3 In Progress: Backend APIs
- Setting up ChromaDB for vector storage
- Building FastAPI `/query/navigate` endpoint
- Implementing semantic search

### ⏳ Upcoming Phases
- **Phase 4**: LangGraph Agent Orchestration
- **Phase 5**: Chrome Extension UI
- **Phase 6**: Integration & Testing
- **Phase 7**: Deployment

## Quick Commands

### Run Integration Tests
```bash
source .venv/bin/activate
python development/tests/test_integration.py
```

### View Documentation
```bash
# Main guide
cat development/docs/README.md

# Development plan
cat development/docs/plan.md

# Processing results
cat development/docs/PROCESSING_SUMMARY.md
```

## Key Files

- **Data**: `../comp_237_content/` - 593 processed JSON files
- **Graph**: `../graph_seed/graph_links.json` - Relationship data
- **Logs**: `../logs/` - Pipeline execution logs
- **Summary**: `../ingest_summary.json` - Processing statistics

## Tech Stack

### Data Processing (Complete)
- Python 3.12.8
- BeautifulSoup4, pypdf, python-docx, python-pptx

### Backend (In Development)
- **Vector DB**: ChromaDB (embeddings + semantic search)
- **API**: FastAPI (Python)
- **Agent Framework**: LangGraph (LangChain)
- **LLM**: Ollama (local - Llama 3 8B or Mistral 7B)
- **Database**: Postgres (session history)

### Frontend (Planned)
- TypeScript + React
- shadcn/ui + Tailwind CSS
- Chrome Extension API

## Development Principles

1. **Integration tests first** - Catch regressions before new features
2. **One feature at a time** - Focus on Navigate mode MVP
3. **Local-first** - No external APIs, everything runs locally
4. **COMP237 specific** - Course ID `_11378_1` hardcoded
5. **Live URLs** - All search results link to actual Blackboard content

## Next Steps

1. ✅ Create integration tests (DONE)
2. 🔄 Set up ChromaDB and load embeddings
3. Build FastAPI `/query/navigate` endpoint
4. Test semantic search with sample queries
5. Document API endpoints

---

**Course**: COMP237 (Artificial Intelligence)  
**Institution**: Centennial College  
**LMS**: Blackboard Ultra  
**Base URL**: https://luminate.centennialcollege.ca/ultra/courses/_11378_1
