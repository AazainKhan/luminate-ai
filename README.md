# Luminate AI - COMP-237 Intelligent Course Assistant

AI-powered educational assistant for COMP-237 at Centennial College. LangGraph multi-agent tutoring with semantic search.

## Quick Start

**Backend:**
```bash
source .venv/bin/activate
python scripts/start_backend.py
```

**Chrome Extension:**
```bash
cd chrome-extension && npm install && npm run build
# Load dist/ in chrome://extensions/
```

## Features

- Navigate Mode: Quick Q&A
- Educate Mode: Study plans + quizzes  
- 13 LangGraph Agents
- Supabase student tracking
- ChromaDB semantic search

## Structure

```
development/backend/fastapi_service/  # API
development/backend/langgraph/        # Agents
chrome-extension/                     # React UI
chromadb_data/                        # Vector DB
```

## Status

✅ Extension builds | ✅ API running | ✅ All agents active
