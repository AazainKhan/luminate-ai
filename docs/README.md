# Documentation Index

Welcome to the Luminate AI documentation. This directory contains all project documentation organized by category.

## 📖 Getting Started

- [Quick Start Guide](QUICK_START.md) - Get the backend running
- [Chrome Extension Setup](QUICK_START_EXTENSION.md) - Install and use the extension

## 🔧 Implementation Guides

All implementation details and technical documentation can be found in the [implementation](implementation/) folder:

### Major Features
- [Navigate Mode Complete](implementation/NAVIGATE_MODE_COMPLETE.md) - Navigate mode implementation
- [Chrome Extension Complete](implementation/CHROME_EXTENSION_COMPLETE.md) - Extension development
- [External Resources Implementation](implementation/EXTERNAL_RESOURCES_IMPLEMENTATION.md) - External resources integration
- [External Resources Enhancement](implementation/EXTERNAL_RESOURCES_ENHANCEMENT.md) - Query enhancement and scope detection

### Recent Updates
- [External Sources Update](implementation/EXTERNAL_SOURCES_UPDATE.md) - Latest changes to external sources (Oct 5, 2025)
- [All Fixes Complete](implementation/ALL_FIXES_COMPLETE.md) - Comprehensive fix summary
- [Ready to Test](implementation/READY_TO_TEST.md) - Testing checklist

### Backend Improvements
- [Backend Improvements](implementation/BACKEND_IMPROVEMENTS.md) - Backend architecture enhancements
- [Apply Improvements](implementation/APPLY_IMPROVEMENTS.md) - Implementation steps
- [ES Module Fix](implementation/ES_MODULE_FIX.md) - Module resolution fixes
- [Fix Root Module](implementation/FIX_ROOT_MODULE.md) - Root module issues

### Project Status
- [Phase 4 Readiness Summary](implementation/PHASE4_READINESS_SUMMARY.md) - Project readiness report

## 🏗️ Architecture

### Backend Structure
```
development/backend/
├── fastapi_service/     # API endpoints
│   └── main.py
├── langgraph/          # Multi-agent workflow
│   ├── agents/         # Individual agents
│   │   ├── understanding.py
│   │   ├── retrieval.py
│   │   ├── external_resources.py
│   │   ├── context.py
│   │   └── formatting.py
│   └── navigate_graph.py
└── logs/               # Application logs
```

### Frontend Structure
```
chrome-extension/
├── src/
│   ├── components/     # React components
│   ├── services/       # API services
│   └── lib/           # Utilities
├── dist/              # Built extension
└── manifest.json      # Extension manifest
```

## 🧪 Testing

Test files are located in `tests/old_tests/`:
- `test_all_queries.py` - Comprehensive query testing
- `test_external_resources.py` - External resources validation
- `test_scope_detection.py` - Scope detection testing
- `test_query_enhancement.py` - Query enhancement testing
- And more...

## 📊 Data

Data files are archived in `data/archive/`:
- `extracted/` - Original course materials
- `comp_237_content/` - Processed content
- `blackboard-api.json` - API configuration
- `ingest_summary.json` - Ingestion results

## 🛠️ Utility Scripts

Scripts are located in `scripts/`:
- `ingest_clean_luminate.py` - Ingest course materials
- `chromadb_helper.py` - ChromaDB management
- `debug_wiki.py` - Wikipedia API debugging
- `demo_capabilities.py` - Feature demonstrations
- `quick_start.py` - Quick setup script

## 📝 Documentation Standards

When adding new documentation:
1. Place implementation details in `implementation/`
2. Keep getting-started guides in the root `docs/` folder
3. Use descriptive filenames with dates for updates
4. Include a brief summary at the top of each document
5. Link related documents for easy navigation

---

**Last Updated**: October 5, 2025
