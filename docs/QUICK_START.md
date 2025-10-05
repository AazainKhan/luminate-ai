# Luminate AI - Quick Start Guide

## What Is This?

Luminate AI is a Chrome extension chatbot for COMP237 (Artificial Intelligence) that helps students **navigate** course content and provides **intelligent tutoring**. Everything runs locally for privacy.

## Current Status: Phase 3 Complete ✅

### ✅ What's Working Now

1. **Data Processing (Phase 2)**
   - 593 COMP237 course files processed
   - 917 searchable chunks with 300K tokens
   - 160 live Blackboard URLs
   - 1,296 knowledge graph relationships

2. **ChromaDB Vector Search (Phase 3)**
   - Semantic search over all course content
   - Fast queries (40-150ms)
   - Uses `all-MiniLM-L6-v2` embeddings

3. **Navigate API (Phase 3)**
   - RESTful endpoint: `/query/navigate`
   - Returns relevant content with Blackboard links
   - CORS enabled for Chrome extension

### ⏳ What's Next

- **Phase 4**: LangGraph agents for intelligent routing
- **Phase 5**: Chrome extension UI
- **Phase 6**: Integration testing
- **Phase 7**: Deployment

---

## Quick Start: Using the Navigate API

### 1. Activate Virtual Environment

```bash
cd /Users/aazain/Documents/GitHub/luminate-ai
source .venv/bin/activate
```

### 2. Start ChromaDB + FastAPI Server

```bash
cd development/backend/fastapi_service
python main.py
```

Wait for:
```
✓ ChromaDB loaded with 917 documents
INFO:     Application startup complete.
```

Server is now running at: http://127.0.0.1:8000

### 3. Test the API

#### Health Check
```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "chromadb_documents": 917,
  "timestamp": "2025-10-04T..."
}
```

#### Search Query
```bash
curl -X POST http://127.0.0.1:8000/query/navigate \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning algorithms", "n_results": 3}'
```

Expected response:
```json
{
  "query": "machine learning algorithms",
  "results": [
    {
      "title": "Topic 5.1 Machine learning overview",
      "excerpt": "M5_Classification_regegression.png...",
      "score": 0.5262,
      "live_url": "https://luminate.centennialcollege.ca/ultra/courses/_11378_1/...",
      "module": "Root",
      "bb_doc_id": "_800646_1",
      ...
    }
  ],
  "total_results": 3,
  "execution_time_ms": 133.2
}
```

### 4. Interactive API Documentation

Open in browser:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

Try queries directly from the Swagger UI!

---

## Common Tasks

### Run Integration Tests

Validates all Phase 2 data processing:

```bash
source .venv/bin/activate
python development/tests/test_integration.py
```

Expected: **All 9 tests passing** ✅

### Re-Initialize ChromaDB

If you need to reload course data:

```bash
source .venv/bin/activate
python development/backend/setup_chromadb.py
```

Choose "yes" when prompted to reload.

### View Logs

API request logs:
```bash
tail -f development/backend/logs/fastapi_service.log
```

Integration test logs:
```bash
ls development/tests/logs/
```

---

## Sample Search Queries

Try these in the API:

### Academic Topics
- "machine learning supervised learning"
- "neural networks backpropagation"
- "breadth first search algorithm"
- "TCP handshake protocol"

### Lab Work
- "lab tutorial neural networks"
- "python exercises machine learning"

### Course Administration
- "syllabus assignment deadlines"
- "course outline topics"
- "professor office hours"

---

## Project Structure

```
luminate-ai/
├── .venv/                          # Python virtual environment
├── comp_237_content/               # 593 processed JSON files
├── chromadb_data/                  # Vector embeddings (917 chunks)
├── graph_seed/                     # 1,296 knowledge relationships
├── logs/                           # Processing logs
│
├── development/
│   ├── backend/
│   │   ├── fastapi_service/
│   │   │   └── main.py            # Navigate API server
│   │   ├── setup_chromadb.py      # ChromaDB initialization
│   │   ├── test_navigate_api.py   # API test client
│   │   ├── API_DOCUMENTATION.md   # Complete API reference
│   │   └── PHASE3_SUMMARY.md      # Implementation summary
│   │
│   ├── tests/
│   │   ├── test_integration.py    # 9 integration tests
│   │   └── README.md              # Testing documentation
│   │
│   └── docs/
│       ├── plan.md                # 7-phase development plan
│       ├── educational_ai.md      # Research on ITS best practices
│       └── (7 other docs)
│
└── ingest_clean_luminate.py       # Original data pipeline
```

---

## Key Technologies

| Component | Technology | Version |
|-----------|-----------|---------|
| Vector DB | ChromaDB | 1.1.0 |
| Embeddings | sentence-transformers | 5.1.1 |
| API Framework | FastAPI | 0.118.0 |
| Server | Uvicorn | 0.37.0 |
| LLM Backend | Torch | 2.8.0 |
| Language | Python | 3.12.8 |

---

## Troubleshooting

### "ChromaDB collection is empty"

Run ChromaDB setup:
```bash
python development/backend/setup_chromadb.py
```

### "Port 8000 already in use"

Kill existing process:
```bash
pkill -f "python main.py"
```

Or use different port in `main.py`:
```python
uvicorn.run("main:app", port=8001)
```

### "Import errors" or "Module not found"

Ensure virtual environment is activated:
```bash
source .venv/bin/activate
pip list  # Verify packages installed
```

### API returns no results

Check:
1. ChromaDB has 917 documents: `curl http://127.0.0.1:8000/stats`
2. Query is not too specific
3. Try broader queries like "machine learning"

---

## Development Workflow

### Making Changes to the API

1. Edit `development/backend/fastapi_service/main.py`
2. Uvicorn auto-reloads (if using `reload=True`)
3. Test with: `curl http://127.0.0.1:8000/health`

### Adding New Endpoints

1. Define Pydantic models for request/response
2. Create endpoint function with `@app.post()` or `@app.get()`
3. Update `API_DOCUMENTATION.md`
4. Test with `test_navigate_api.py`

### Modifying ChromaDB

1. Edit `setup_chromadb.py`
2. Delete `chromadb_data/` directory
3. Re-run: `python setup_chromadb.py`
4. Restart API server

---

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Avg Query Time | 40-150ms |
| Collection Size | 917 chunks |
| Startup Time | ~5 seconds (model loading) |
| Memory Usage | ~500MB (embeddings in RAM) |
| Disk Usage | ~100MB (ChromaDB data) |

---

## Educational AI Alignment

Based on research in `development/docs/educational_ai.md`:

✅ **Retrieval Practice** - Students actively search → better retention  
✅ **Scaffolding Ready** - Module filtering enables progressive difficulty  
✅ **Source Transparency** - Live Blackboard URLs cite authoritative sources  
✅ **Privacy First** - 100% local processing, no external APIs  
✅ **Fast Feedback** - <200ms query time for immediate results  

---

## Next Steps for You

### If You're a Student
- Wait for Chrome extension (Phase 5)
- Use API via Swagger UI for now: http://127.0.0.1:8000/docs

### If You're Developing
1. Review `development/docs/plan.md` for full roadmap
2. Read `development/backend/API_DOCUMENTATION.md` for API details
3. Check `development/docs/educational_ai.md` for pedagogical context
4. Start Phase 4: LangGraph agent orchestration

### If You're Testing
1. Run integration tests: `python development/tests/test_integration.py`
2. Try API queries with different search terms
3. Review logs for debugging: `development/backend/logs/`

---

## Resources

### Documentation
- **API Reference**: `development/backend/API_DOCUMENTATION.md`
- **Phase 3 Summary**: `development/backend/PHASE3_SUMMARY.md`
- **Development Plan**: `development/docs/plan.md`
- **Educational AI**: `development/docs/educational_ai.md`

### Code Files
- **API Server**: `development/backend/fastapi_service/main.py`
- **ChromaDB Setup**: `development/backend/setup_chromadb.py`
- **Integration Tests**: `development/tests/test_integration.py`

### External Links
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Sentence Transformers**: https://www.sbert.net/

---

## Support

### Questions?
- Check `development/backend/logs/fastapi_service.log` for errors
- Review `development/backend/API_DOCUMENTATION.md` for API usage
- Read `development/docs/educational_ai.md` for design rationale

### Contributing
- Follow existing code structure in `development/backend/`
- Add tests to `development/tests/test_integration.py`
- Update documentation in `development/backend/API_DOCUMENTATION.md`

---

**Version**: 1.0.0 (Phase 3 Complete)  
**Course**: COMP237 - Artificial Intelligence  
**Institution**: Centennial College  
**Last Updated**: October 4, 2025

**Status**: ✅ Navigate API Ready for Chrome Extension Integration
