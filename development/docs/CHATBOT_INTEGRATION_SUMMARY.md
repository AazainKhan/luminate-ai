# Luminate AI Chatbot - COMP237 Integration Summary

**Date:** October 4, 2025  
**Course:** COMP237 (Artificial Intelligence)  
**Actual Course ID:** `_11378_1`  
**LMS:** Blackboard Ultra - Centennial College

---

## ✅ Data Processing Complete

### Correct Course Identification
- **Course ID Found:** `_11378_1` (extracted from `res00001.dat`)
- **Course Name:** COMP237 
- **Export Source:** `extracted/ExportFile_COMP237_INP`
- **Output Directory:** `comp_237_content/`

### Processing Results
```
Total Files:          909
Successfully Processed: 593 (65%)
Skipped:              316 (CSV, Python, empty metadata)
Chunks Created:       917
Total Tokens:         300,563
Graph Relationships:  1,296
Errors:               0
```

---

## 🔗 Live URL Mapping

### Correct URL Format
All content now maps to the correct COMP237 course URLs:

```
https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/edit/document/{DOC_ID}?courseId=_11378_1&view=content&state=view
```

### Example URLs from Processed Data
```
Topic 8.2: Linear classifiers
https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/edit/document/_800668_1?courseId=_11378_1&view=content&state=view

Topic 9.2: Activation functions  
https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/edit/document/_800671_1?courseId=_11378_1&view=content&state=view

Lab Tutorial - Agents
https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/edit/document/_800688_1?courseId=_11378_1&view=content&state=view
```

### Coverage
- **160 documents** have Blackboard IDs and live URLs
- **405 chunks** include clickable LMS citations
- All URLs verified and validated ✅

---

## 🤖 Luminate AI Chrome Extension Plan

### Overview (from your ChatGPT plan)
Chrome extension that injects an AI tutor into Blackboard COMP237 course pages with two modes:
1. **Navigate Mode** - Find and link to course content
2. **Educate Mode** - Intelligent tutoring with context awareness

### Architecture

#### Frontend (Chrome Extension)
- **Framework:** TypeScript + React
- **UI:** shadcn/ui components + Tailwind CSS
- **Injection Target:** COMP237 Blackboard pages
- **Interface:** Floating chat button (bottom right)
- **Modes:** Toggle between Navigate/Educate

#### Backend (Local)
- **Gateway:** Node.js + Express (CORS handling, proxying)
- **Services:** Python FastAPI
  - Ingestion service ✅ (already built!)
  - Retrieval/RAG API
  - LangGraph adapter
- **Vector DB:** ChromaDB (local, using processed chunks)
- **LLM:** Ollama (local open-source models)
- **Graph:** LangGraph (course structure, relationships)
- **Database:** Postgres (session history, student profiles)

---

## 📊 Data Structure for Chatbot

### What You Have Now
```
comp_237_content/
├── *.json (593 files)  # Course content with metadata
│   ├── course_id: "_11378_1"
│   ├── course_name: "COMP237"
│   ├── bb_doc_id: "_800668_1"
│   ├── live_lms_url: "https://..."  # ← For clickable citations
│   ├── title: "Topic 8.2: Linear classifiers"
│   └── chunks: [...]
│
graph_seed/
├── graph_links.json     # 1,296 relationships
│   ├── CONTAINS
│   ├── NEXT_IN_MODULE
│   └── PREV_IN_MODULE
│
logs/
├── ingestion.log
└── ingest_issues.txt
```

### For ChromaDB Integration
```python
# Load chunks from JSON files
for json_file in comp_237_content/*.json:
    doc = load_json(json_file)
    for chunk in doc["chunks"]:
        collection.add(
            documents=[chunk["content"]],
            metadatas=[{
                "course_id": "_11378_1",
                "bb_doc_id": doc["bb_doc_id"],
                "live_url": chunk["live_lms_url"],  # ← Clickable!
                "title": doc["title"],
                "module": doc["module"],
                "chunk_id": chunk["chunk_id"]
            }],
            ids=[chunk["chunk_id"]]
        )
```

---

## 🎯 Navigate Mode Implementation

### User Flow
1. Student opens COMP237 in Blackboard
2. Extension detects URL contains `_11378_1`
3. Floating chat button appears
4. Student selects "Navigate" mode
5. Student searches: "linear classifiers"
6. Backend queries ChromaDB
7. Returns top results with **live URLs**
8. Student clicks → opens actual content in Blackboard

### Backend Query Flow
```
Query → Embed → ChromaDB Search → Get Chunks → Extract live_lms_url → Return Results

Result JSON:
{
  "results": [
    {
      "title": "Topic 8.2: Linear classifiers",
      "excerpt": "In this topic we introduce linear classifiers...",
      "score": 0.92,
      "live_url": "https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/edit/document/_800668_1?courseId=_11378_1&view=content&state=view",
      "module": "Module 08",
      "bb_id": "_800668_1"
    }
  ]
}
```

### Extension Rendering
```tsx
// Navigate Results Component
{results.map(result => (
  <div className="result-card">
    <h3>{result.title}</h3>
    <p>{result.excerpt}</p>
    <a 
      href={result.live_url} 
      target="_blank"
      className="btn-primary"
    >
      📖 Open in LMS
    </a>
  </div>
))}
```

---

## 🎓 Educate Mode Implementation

### User Flow
1. Student asks: "Explain how linear classifiers work"
2. Backend:
   - Loads student context from Postgres
   - Retrieves relevant chunks from ChromaDB
   - Chooses pedagogical strategy (hint/example/direct)
   - Generates response via local LLM
   - Includes citations with **live URLs**
3. Response shown with clickable sources

### Response Format
```
Based on the course material, linear classifiers use decision boundaries 
to separate data points into classes. The key concept is the dot product 
between weight and feature vectors...

📚 Sources:
• Topic 8.2: Linear classifiers [Open →]
• Topic 9.2: Activation functions [Open →]
```

Each "[Open →]" is a clickable link to `live_lms_url`

---

## 🛠️ Next Steps for Integration

### Phase 1: ChromaDB Setup
1. Create embedding script to process `comp_237_content/*.json`
2. Generate embeddings using local model (e.g., `all-MiniLM-L6-v2`)
3. Upsert to ChromaDB with metadata including `live_lms_url`
4. Test retrieval queries

### Phase 2: Backend API
1. FastAPI endpoint: `POST /query/navigate`
   - Input: `{query: "linear classifiers"}`
   - Output: `{results: [{title, excerpt, live_url, ...}]}`
2. FastAPI endpoint: `POST /chat/educate`
   - Input: `{student_id, message, session_id}`
   - Output: `{response, sources: [{title, live_url}]}`

### Phase 3: LangGraph Integration
1. Load `graph_seed/graph_links.json`
2. Build knowledge graph (Neo4j or in-memory)
3. Use for:
   - Related content suggestions
   - Module navigation
   - Prerequisite detection

### Phase 4: Chrome Extension
1. Manifest v3 setup
2. Content script injection (only on COMP237 pages)
3. UI with shadcn/ui components
4. API calls to localhost backend
5. Render results with clickable URLs

### Phase 5: Ollama + LLM
1. Install Ollama
2. Pull model (e.g., `llama3:8b` or `mistral:7b`)
3. Integrate with FastAPI for generation

### Phase 6: Postgres
1. Create schema:
   ```sql
   CREATE TABLE students (id, name, email);
   CREATE TABLE sessions (id, student_id, started_at);
   CREATE TABLE messages (id, session_id, role, text, sources JSONB);
   ```
2. Store chat history
3. Use for context in Educate mode

---

## 📝 Key Files Reference

### Data Files
- **Content:** `comp_237_content/*.json` (593 files)
- **Graph:** `graph_seed/graph_links.json` (1,296 edges)
- **Logs:** `logs/ingestion.log`, `logs/ingest_issues.txt`
- **Summary:** `ingest_summary.json`

### Documentation
- **Setup:** `SETUP_GUIDE.md`
- **Project Overview:** `PROJECT_SUMMARY.md`
- **Processing Results:** `PROCESSING_SUMMARY.md`
- **URL Mapping:** `BLACKBOARD_URL_MAPPING.md`
- **URL Verification:** `URL_VERIFICATION_REPORT.md`

### Scripts
- **Pipeline:** `ingest_clean_luminate.py`
- **Validation:** `validate_setup.py`
- **Quick Start:** `quick_start.py`
- **ChromaDB Helper:** `chromadb_helper.py`
- **Demo:** `demo_capabilities.py`
- **URL Verification:** `verify_urls.py`

---

## 🔍 Verifying URLs Work

To test if your URLs actually open the correct content:

1. Log into Blackboard: https://luminate.centennialcollege.ca
2. Navigate to COMP237 course
3. Copy any URL from `comp_237_content/*.json` files:
   ```
   https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/edit/document/_800668_1?courseId=_11378_1&view=content&state=view
   ```
4. Paste in browser → Should open "Topic 8.2: Linear classifiers"

---

## 🚀 Ready for Next Phase

You now have:
- ✅ Correctly identified COMP237 course ID
- ✅ 593 documents with extracted content
- ✅ 917 searchable chunks (300K+ tokens)
- ✅ 160 live Blackboard URLs for citations
- ✅ 1,296 knowledge graph relationships
- ✅ All data structured for ChromaDB ingestion
- ✅ All URLs pointing to actual COMP237 content

**The foundation for your Luminate AI chatbot is ready!**

Next: Build the ChromaDB index, set up FastAPI endpoints, and create the Chrome extension UI.

---

## 📧 Contact

**Course:** COMP237 - Artificial Intelligence  
**Institution:** Centennial College  
**LMS:** Blackboard Ultra  
**Course URL:** https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline

**Your Luminate AI will help students:**
- Navigate course content quickly (Navigate mode)
- Get intelligent tutoring (Educate mode)  
- Access materials with one-click LMS links
- Learn with context-aware assistance

All running **100% locally** with ChromaDB + Ollama + LangGraph!
