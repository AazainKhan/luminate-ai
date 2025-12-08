# OER Sources Setup Guide

## Overview

This guide explains how to download and ingest Open Educational Resources (OER) to supplement COMP237 course materials. These resources provide foundational math and programming context.

## Required OER Sources

### 1. Introduction to Data Science Using Python
**Topics**: Python basics, data structures, file I/O, packages, basic ML
**Source**: https://paadopt.org/bookshelf/introduction-to-data-science-using-python/
**Download Location**: `backend/data/raw/oer-sources/data-science-python/`

### 2. MIT 18.657 - Mathematics of Machine Learning
**Topics**: Linear algebra, probability, gradient descent, regularization
**Source**: https://ocw.mit.edu/courses/18-657-mathematics-of-machine-learning-fall-2015/
**Download Location**: `backend/data/raw/oer-sources/mit-18-657-math-ml/`

### 3. MIT 6.867 - Machine Learning
**Topics**: Perceptron, regression, SVMs, kernel methods, boosting
**Source**: https://ocw.mit.edu/courses/6-867-machine-learning-fall-2006/
**Download Location**: `backend/data/raw/oer-sources/mit-6-867-ml/`

---

## Download Instructions

### Option 1: Manual Download (Recommended)

```bash
# Create OER sources directory
mkdir -p backend/data/raw/oer-sources

# 1. Download Introduction to Data Science Using Python
# Visit: https://paadopt.org/bookshelf/introduction-to-data-science-using-python/
# Download PDF or web scrape chapters
# Save to: backend/data/raw/oer-sources/data-science-python/

# 2. Download MIT 18.657 (Mathematics)
# Visit: https://ocw.mit.edu/courses/18-657-mathematics-of-machine-learning-fall-2015/pages/calendar/
# Download lecture notes and readings
# Save to: backend/data/raw/oer-sources/mit-18-657-math-ml/

# 3. Download MIT 6.867 (Machine Learning)
# Visit: https://ocw.mit.edu/courses/6-867-machine-learning-fall-2006/
# Download lecture notes and readings
# Save to: backend/data/raw/oer-sources/mit-6-867-ml/
```

### Option 2: Automated Scraper (TODO)

```bash
# TODO: Create automated scraper script
python backend/app/etl/download_oer.py --all
```

---

## Extract and Convert to JSONL

After downloading, convert PDFs/HTML to JSONL format using the ETL pipeline:

```bash
# Run in Docker container
docker exec -it api_brain bash

# Convert OER sources to JSONL
python -m app.etl.process_oer \
  --input /app/data/raw/oer-sources/ \
  --output /app/data/raw/oer-sources/chroma_input.jsonl

# Exit container
exit
```

Expected JSONL format:
```json
{
  "id": "unique-id",
  "text": "Content text...",
  "topic": "Math for ML",
  "subtopic": "Linear Algebra",
  "section_heading": "Vectors and Matrices",
  "source_title": "MIT 18.657",
  "source_url": "https://...",
  "difficulty_level": "Intermediate",
  "content_type": "Theory"
}
```

---

## Ingest into ChromaDB

Once you have `chroma_input.jsonl`, ingest it:

```bash
# Run in Docker container
docker exec -it api_brain bash

# Ingest OER resources
python -m app.etl.ingest_oer \
  --jsonl /app/data/raw/oer-sources/chroma_input.jsonl \
  --collection oer_resources

# Verify ingestion
python -c "
import chromadb
c = chromadb.HttpClient(host='memory_store', port=8000)
col = c.get_collection('oer_resources')
print(f'OER collection has {col.count()} chunks')
"

# Exit container
exit
```

---

## Verify RAG Hybrid Search

Test that both course and OER sources are being retrieved:

```bash
docker exec api_brain python -c "
from app.agent.tools.rag import get_rag_retriever

# Test with math query
r = get_rag_retriever()
docs, meta = r.retrieve('gradient descent calculus derivative', k=5)

print(f'Retrieved {len(docs)} docs:')
for i, d in enumerate(docs, 1):
    source_type = d.get('source_type', 'unknown')
    title = d.get('title', 'Unknown')
    score = d.get('score', 0)
    print(f'{i}. [{source_type.upper()}] {title} (score: {score:.2f})')
"
```

Expected output:
```
Retrieved 5 docs:
1. [COURSE] Topic 8.1: Introduction to ANN (score: 0.42)
2. [OER] MIT 18.657: Gradient Descent (score: 0.38)
3. [COURSE] Topic 9.1: More on ANN (score: 0.36)
4. [OER] MIT 6.867: Linear Regression (score: 0.34)
5. [OER] Introduction to Data Science: Optimization (score: 0.32)
```

---

## Quick Start with Adarsh's Existing Data

If you already have Adarsh's processed `chroma_input.jsonl`:

```bash
# Copy from docs/friends-work/luminate-ai-adarsh/data/
cp docs/friends-work/luminate-ai-adarsh/data/chroma_input.jsonl \
   backend/data/raw/oer-sources/

# Ingest directly
docker exec -it api_brain python -m app.etl.ingest_oer \
  --jsonl /app/data/raw/oer-sources/chroma_input.jsonl \
  --collection oer_resources
```

---

## Troubleshooting

### OER collection not found

```bash
# List all collections
docker exec api_brain python -c "
import chromadb
c = chromadb.HttpClient(host='memory_store', port=8000)
print([col.name for col in c.list_collections()])
"

# Should show: ['comp237_course_materials', 'oer_resources']
```

### No OER results in RAG

Check that OER search is enabled:
```python
# In backend/app/agent/tools/rag.py
docs, meta = retriever.retrieve(query, k=5, use_oer=True)  # ← make sure use_oer=True
```

### Poor OER relevance

Adjust threshold in `rag.py`:
```python
# Line ~150: Lower threshold for OER
if score >= threshold * 0.8:  # Try 0.7 for more OER results
```

---

## Files Created/Modified

- `backend/app/etl/ingest_oer.py` - OER ingestion script
- `backend/app/agent/tools/rag.py` - Hybrid course + OER retriever
- `backend/data/raw/oer-sources/` - OER source files (you create this)
- `backend/data/raw/oer-sources/chroma_input.jsonl` - Processed OER data

---

## Next Steps

1. Download OER sources from URLs above
2. Convert to JSONL (manual or automated)
3. Run `ingest_oer.py` to populate ChromaDB
4. Test hybrid search with math/programming queries
5. Verify frontend shows mix of course + OER sources
