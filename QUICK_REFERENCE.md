# Quick Reference Guide

**Luminate AI** - AI-powered course assistant for COMP-237

## 🚀 Fast Commands

### Start Backend
```bash
source .venv/bin/activate
cd development/backend
python fastapi_service/main.py
```

### Build Chrome Extension
```bash
cd chrome-extension
npm run build
```

### Check System Status
```bash
# ChromaDB documents
python scripts/chromadb_helper.py

# View logs
tail -f development/backend/logs/app.log
```

## 📂 Where to Find Things

| What you need | Location |
|--------------|----------|
| **Documentation** | `docs/` |
| **Quick Start** | `docs/QUICK_START.md` |
| **Scripts** | `scripts/` |
| **Tests** | `tests/old_tests/` |
| **Backend Code** | `development/backend/` |
| **Extension Code** | `chrome-extension/src/` |
| **Archived Data** | `data/archive/` |
| **Logs** | `logs/` and `development/backend/logs/` |

## 🔧 Common Tasks

### Update Documentation
1. Implementation notes → `docs/implementation/`
2. User guides → `docs/`
3. Update `docs/README.md` index

### Run Tests
```bash
python tests/old_tests/test_all_queries.py
```

### Restart Backend
```bash
# Kill existing process
pkill -f "python fastapi_service/main.py"

# Restart
cd development/backend
python fastapi_service/main.py
```

### Rebuild Extension
```bash
cd chrome-extension
npm run build
# Then reload in chrome://extensions
```

## 📖 Key Documentation

- [Main README](README.md) - Project overview
- [Quick Start](docs/QUICK_START.md) - Backend setup
- [Extension Setup](docs/QUICK_START_EXTENSION.md) - Chrome extension
- [Workspace Cleanup](docs/WORKSPACE_CLEANUP.md) - Organization details
- [Docs Index](docs/README.md) - All documentation

## 🌐 API Endpoints

```bash
# Navigate Mode
curl -X POST http://localhost:8000/api/navigate \
  -H "Content-Type: application/json" \
  -d '{"query": "What is backpropagation?"}'

# External Resources
curl http://localhost:8000/api/external-resources?query=neural+networks

# Health Check
curl http://localhost:8000/health
```

## 🎯 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| **Backend not starting** | Check `.env` file exists, activate venv |
| **Extension not working** | Rebuild and reload in Chrome |
| **ChromaDB errors** | Check `chromadb_data/` exists |
| **Module errors** | Run `pip install -r requirements.txt` |

## 📊 Project Stats

- **Documents**: 917 embedded course materials
- **Agents**: 5 (Understanding, Retrieval, External, Context, Formatting)
- **External Sources**: YouTube, Wikipedia, OER Commons
- **Response Time**: 2-5 seconds average

---

**Need help?** See full documentation in `docs/`
