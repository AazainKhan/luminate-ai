# Blackboard URL Setup - Quick Reference

## 🚀 Quick Start (5 minutes)

### 1. Find Course ID (2 min)
```bash
# Go to COMP237 in Blackboard
# Click any content item
# Copy "_XXXXX_1" from URL like:
# https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/...
```

### 2. Configure Course ID (1 min)
```bash
# Run setup script
docker exec api_brain python -m app.etl.setup_blackboard_course_id _29430_1
```

### 3. Enrich ChromaDB (2 min)
```bash
# Add Blackboard URLs to all course materials
docker exec api_brain python -m app.etl.enrich_blackboard_urls \
  --content-ids-path /app/data/processed/blackboard_content_ids.json \
  --course-id "_29430_1"

# Expected: ✅ Enriched 403 documents with Blackboard URLs
```

### 4. Rebuild & Test (1 min)
```bash
# Rebuild backend
docker compose build api_brain --no-cache
docker compose up -d api_brain

# Test
docker exec api_brain python -c "
from app.agent.graph import run_agent
result = run_agent(query='What is AI?')
print('URL:', result['sources'][0].get('url'))
print('Type:', result['sources'][0].get('link_type'))
"

# Expected: URL starts with https://luminate.centennialcollege.ca/ultra/courses/_29430_1/...
# Expected: Type: blackboard
```

---

## 📋 File Locations

| File | Path | Purpose |
|------|------|---------|
| **Content IDs** | `backend/data/processed/blackboard_content_ids.json` | Resource → Content ID mappings |
| **Enrichment Script** | `backend/app/etl/enrich_blackboard_urls.py` | Adds Blackboard URLs to ChromaDB |
| **Setup Script** | `backend/app/etl/setup_blackboard_course_id.py` | Easy course ID configuration |
| **RAG Retriever** | `backend/app/agent/tools/rag.py` | Extracts URLs from ChromaDB |
| **Frontend Types** | `extension/src/types/index.ts` | TypeScript types with blackboard |
| **Source Component** | `extension/src/components/ai-elements/sources.tsx` | Purple styling for Blackboard |

---

## 🎨 Visual Indicators

| Link Type | Icon | Color | Badge | Border |
|-----------|------|-------|-------|--------|
| **Blackboard** | 🎓 | Purple | COURSE (purple) | Purple 4px |
| Mediasite | 🎥 | Blue | VIDEO (blue) | Blue 4px |
| External | 🌐 | Gray | EMBEDDED | None |

---

## 🔍 Verification Commands

```bash
# Check ChromaDB has Blackboard URLs
docker exec api_brain python -c "
from app.rag.chromadb_client import get_chroma_client
client = get_chroma_client()
col = client.get_collection('comp237_course_materials')
doc = col.get(limit=1, include=['metadatas'])
print('Blackboard URL:', doc['metadatas'][0].get('blackboard_url', 'NOT FOUND'))
print('Primary Type:', doc['metadatas'][0].get('primary_url_type', 'NOT SET'))
"

# Expected: Blackboard URL: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/...
# Expected: Primary Type: blackboard

# Check statistics
docker exec api_brain python -m app.etl.enrich_blackboard_urls \
  --stats-only --course-id "_29430_1"

# Expected: Documents with Blackboard URLs: 403 (100%)

# Test full agent flow
docker exec api_brain python -c "
from app.agent.graph import run_agent
result = run_agent(query='What is the Turing test?')
for i, source in enumerate(result.get('sources', [])[:3], 1):
    print(f'{i}. [{source.get(\"link_type\", \"unknown\")}] {source.get(\"title\", \"Unknown\")}')
    print(f'   {source.get(\"url\", \"No URL\")[:80]}...')
"

# Expected: [blackboard] links for course materials
```

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| **404 errors on Blackboard URLs** | Wrong course ID. Re-check Blackboard URL and update. |
| **"NOT FOUND" in verification** | Enrichment not run. Execute step 3 above. |
| **Purple styling not showing** | Frontend not rebuilt. Restart extension dev server. |
| **Links open in same tab** | Check `target="_blank"` in `sources.tsx`. |

---

## 📊 Expected Results

### After Enrichment

```
📊 Statistics:
  Total documents: 403
  Documents with Blackboard URLs: 403 (100%)
  Documents with Blackboard as primary: 403 (100%)
  
URL Breakdown:
  - Blackboard course links: 403
  - Mediasite videos: 318
  - External articles: 46
  - Wikipedia: 5
  - Internal resources: 21
```

### In Frontend

```
🎓 Topic 1.2: The Turing test  [COURSE] [COURSE] 🔗
│  Module 1 - Topic 1.2
└─ https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800667_1?courseId=_29430_1&view=content

🎥 Topic 1.2: The Turing test  [COURSE] [VIDEO] 🔗
│  Module 1 - Topic 1.2
└─ https://mediasite.centennialcollege.ca/Mediasite/Play/51657db5...
```

---

## 📚 Documentation

- **Full Guide:** `docs/BLACKBOARD_URL_INTEGRATION.md`
- **Complete Summary:** `docs/COMPLETE_URL_INTEGRATION.md`
- **Clickable Sources:** `docs/CLICKABLE_SOURCES_COMPLETE.md`

---

## ✅ Success Checklist

- [ ] Course ID found from Blackboard URL
- [ ] `setup_blackboard_course_id.py` executed
- [ ] Enrichment script completed (403/403 documents)
- [ ] Backend rebuilt and restarted
- [ ] Verification shows `primary_url_type: blackboard`
- [ ] Test query returns Blackboard URLs
- [ ] Frontend shows purple 🎓 styling
- [ ] Links open in new tab to Blackboard

---

*Setup Time: ~5 minutes*  
*Required: Blackboard course ID (format: _XXXXX_1)*  
*Status: Ready for deployment after configuration*
