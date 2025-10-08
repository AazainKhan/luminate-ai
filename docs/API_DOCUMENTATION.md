# Luminate AI Navigate API Documentation

## Overview

The Navigate API provides semantic search capabilities for COMP237 course content using ChromaDB vector embeddings. Students can search for topics, concepts, and materials, receiving relevant results with direct links to Blackboard course pages.

## Base URL

```
http://127.0.0.1:8000
```

## Authentication

None required (local service for student use)

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API service is running and ChromaDB is accessible.

**Response:**
```json
{
  "status": "healthy",
  "chromadb_documents": 917,
  "timestamp": "2025-10-04T18:23:48.014521"
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - ChromaDB not initialized

---

### 2. Collection Statistics

**GET** `/stats`

Get ChromaDB collection statistics and configuration.

**Response:**
```json
{
  "stats": {
    "total_documents": 917,
    "collection_name": "comp237_content",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "persist_directory": "/path/to/chromadb_data",
    "sample_metadata_keys": ["course_id", "title", "bb_doc_id", "live_lms_url", ...]
  },
  "timestamp": "2025-10-04T18:23:48.014521"
}
```

---

### 3. Navigate Search (Main Endpoint)

**POST** `/query/navigate`

Semantic search for course content with ChromaDB.

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "n_results": 10,
  "min_score": 0.0,
  "module_filter": null,
  "content_type_filter": null,
  "include_no_url": false
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (1-500 chars) |
| `n_results` | integer | No | 10 | Number of results (1-50) |
| `min_score` | float | No | 0.0 | Minimum similarity score (0-1, lower is better) |
| `module_filter` | string | No | null | Filter by module name (e.g., "Root") |
| `content_type_filter` | string | No | null | Filter by content type (e.g., ".pdf", ".dat") |
| `include_no_url` | boolean | No | false | Include results without Blackboard URLs |

**Response:**
```json
{
  "query": "machine learning algorithms",
  "results": [
    {
      "title": "Topic 5.1 Machine learning overview",
      "excerpt": "M5_Classification_regegression.png References Artificial intelligence...",
      "score": 0.5262,
      "live_url": "https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/edit/document/_800646_1?courseId=_11378_1&view=content&state=view",
      "module": "Root",
      "bb_doc_id": "_800646_1",
      "content_type": ".dat",
      "chunk_index": 4,
      "total_chunks": 5,
      "tags": ["Root", "Topic 5.1 Machine learning overview"]
    }
  ],
  "total_results": 3,
  "execution_time_ms": 133.2,
  "timestamp": "2025-10-04T18:23:55.063483"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Original search query |
| `results` | array | List of search results |
| `results[].title` | string | Document title |
| `results[].excerpt` | string | Text excerpt (150 chars max) |
| `results[].score` | float | Similarity score (lower = more similar) |
| `results[].live_url` | string | Clickable Blackboard URL (may be null) |
| `results[].module` | string | Course module name |
| `results[].bb_doc_id` | string | Blackboard document ID |
| `results[].content_type` | string | File extension (.dat, .pdf, etc.) |
| `results[].chunk_index` | integer | Current chunk index |
| `results[].total_chunks` | integer | Total chunks in document |
| `results[].tags` | array | Associated tags |
| `total_results` | integer | Number of results returned |
| `execution_time_ms` | float | Query execution time in milliseconds |
| `timestamp` | string | ISO 8601 timestamp |

**Status Codes:**
- `200 OK` - Successful search
- `422 Unprocessable Entity` - Invalid request parameters
- `500 Internal Server Error` - Search failed
- `503 Service Unavailable` - ChromaDB not available

---

## Example Usage

### JavaScript (Fetch API)

```javascript
async function searchCourse(query) {
  const response = await fetch('http://127.0.0.1:8000/query/navigate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: query,
      n_results: 10
    })
  });
  
  const data = await response.json();
  return data.results;
}

// Usage
const results = await searchCourse('neural networks');
results.forEach(result => {
  console.log(`${result.title}: ${result.live_url}`);
});
```

### Python (requests)

```python
import requests

def search_course(query, n_results=10):
    response = requests.post(
        'http://127.0.0.1:8000/query/navigate',
        json={
            'query': query,
            'n_results': n_results
        }
    )
    response.raise_for_status()
    return response.json()['results']

# Usage
results = search_course('machine learning algorithms')
for result in results:
    print(f"{result['title']}: {result['live_url']}")
```

### cURL

```bash
# Basic search
curl -X POST http://127.0.0.1:8000/query/navigate \
  -H "Content-Type: application/json" \
  -d '{"query": "neural networks", "n_results": 5}'

# Filtered search
curl -X POST http://127.0.0.1:8000/query/navigate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search algorithms",
    "n_results": 5,
    "module_filter": "Root",
    "min_score": 0.5
  }'
```

## Sample Queries

### Topic Discovery
```json
{"query": "machine learning supervised learning"}
```

### Lab Exercises
```json
{"query": "lab tutorial neural networks python"}
```

### Course Administration
```json
{"query": "syllabus assignment deadlines"}
```

### Specific Concepts
```json
{"query": "breadth first search algorithm"}
```

### Networking Topics
```json
{"query": "TCP handshake protocol"}
```

## Error Handling

### Empty Query
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "query"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

### ChromaDB Unavailable
```json
{
  "error": "Search service not available",
  "timestamp": "2025-10-04T18:23:55.063483"
}
```

## Performance

- **Typical Query Time**: 40-150ms
- **Collection Size**: 917 chunks
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Average Results**: 10 per query

## CORS Configuration

The API is configured to accept requests from:
- Chrome extensions (`chrome-extension://*`)
- Localhost (`http://localhost:*`, `http://127.0.0.1:*`)
- Blackboard LMS (`https://luminate.centennialcollege.ca`)

## Running the Service

### Start Server
```bash
cd development/backend/fastapi_service
source ../../../.venv/bin/activate
python main.py
```

Server will start on `http://127.0.0.1:8000`

### Test Health
```bash
curl http://127.0.0.1:8000/health
```

### View API Documentation
FastAPI provides interactive API docs at:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Logging

Logs are written to:
```
development/backend/logs/fastapi_service.log
```

Log entries include:
- Request details (IP, query, n_results)
- Execution time
- Result counts
- Errors with stack traces

## Next Steps

### Integration with Chrome Extension
1. Call `/query/navigate` from Chrome extension content script
2. Display results in custom UI injected into Blackboard
3. Handle click events to navigate to `live_url`

### Future Enhancements
- Query history tracking
- Popular search analytics
- Query auto-completion
- Related topics suggestions
- Personalized result ranking based on student progress

---

**API Version**: 1.0.0  
**Course**: COMP237 (Artificial Intelligence)  
**Institution**: Centennial College  
**Last Updated**: October 4, 2025
