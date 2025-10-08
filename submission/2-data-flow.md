# Luminate AI - Data Flow Documentation

## Overview

This document traces how data moves through the Luminate AI system, from raw Blackboard course exports to rendered responses in the Chrome extension.

---

## Data Ingestion Pipeline

### Phase 1: Blackboard Export → Cleaned JSON

**Input**: Blackboard LMS course export package  
**Output**: 593 structured JSON files in `cleaned/`

#### Step-by-Step Process

**Script**: `scripts/ingest_clean_luminate.py`

1. **Extract Blackboard Package**
   - Source: `ExportFile_COMP237/` (909 files)
   - Formats: .xml, .html, .pdf, .docx, .dat, .txt
   - Course metadata in `imsmanifest.xml`

2. **Parse Manifest File**
   - Extract course structure
   - Map Blackboard IDs to content items
   - Build module hierarchy (Root, csfiles, etc.)

3. **Process Each File**
   ```
   For each file in export:
     ├─ Detect file type (.html, .pdf, .docx, etc.)
     ├─ Extract text content
     │  ├─ HTML → BeautifulSoup parsing
     │  ├─ PDF → pypdf extraction
     │  ├─ DOCX → python-docx extraction
     │  └─ XML → ElementTree parsing
     ├─ Clean boilerplate
     │  └─ Remove: navigation, breadcrumbs, "Print Page"
     ├─ Chunk text (500-800 tokens per chunk)
     ├─ Generate metadata
     │  ├─ course_id: _29430_1
     │  ├─ bb_doc_id: _800713_1
     │  ├─ live_lms_url: https://luminate.centennialcollege.ca/...
     │  ├─ title: "Lab Tutorial Logistic regression"
     │  ├─ module: "Root"
     │  └─ created_date: "2024-10-04"
     └─ Output JSON file to cleaned/
   ```

4. **Statistics**
   - Total files: 909
   - Processed: 593
   - Skipped: 316 (empty, duplicates, unsupported)
   - Total chunks: 917
   - Total tokens: 300,563
   - Avg tokens/file: 507

**Output Format** (`cleaned/res00207.json`):
```json
{
  "course_id": "_29430_1",
  "course_name": "Luminate",
  "module": "Root",
  "file_name": "res00207.dat",
  "content_type": ".dat",
  "bb_doc_id": "_800713_1",
  "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800713_1?courseId=_29430_1&view=content&state=view",
  "title": "Lab Tutorial Logistic regression",
  "created_date": "2024-10-04 18:31:46 EDT",
  "updated_date": "2024-11-13 23:45:18 EST",
  "raw_text_length": 2078,
  "total_tokens": 638,
  "num_chunks": 2,
  "chunks": [
    {
      "chunk_id": "_800713_1_chunk_000",
      "content": "Lab Tutorial Logistic regression... [full text]",
      "tags": ["Root", "Lab Tutorial"],
      "live_lms_url": "https://...",
      "token_count": 519,
      "chunk_index": 0,
      "total_chunks": 2
    }
  ]
}
```

---

### Phase 2: JSON → ChromaDB Embeddings

**Input**: 593 JSON files from `cleaned/`  
**Output**: ChromaDB collection with 917 vector embeddings

**Script**: `development/backend/setup_chromadb.py`

#### Embedding Process

1. **Initialize ChromaDB**
   ```python
   client = chromadb.PersistentClient(path="chromadb_data/")
   collection = client.get_or_create_collection(
       name="comp237_content",
       embedding_function=SentenceTransformer("all-MiniLM-L6-v2")
   )
   ```

2. **Load All JSON Files**
   ```
   For each JSON in cleaned/:
     ├─ Load document
     ├─ Extract all chunks
     └─ Prepare for embedding
   ```

3. **Generate Embeddings**
   ```
   For each chunk:
     ├─ Text: "Lab Tutorial Logistic regression overview..."
     ├─ Model: sentence-transformers/all-MiniLM-L6-v2
     ├─ Output: 384-dimensional vector
     │    [0.023, -0.15, 0.087, ..., 0.12]
     └─ Store in ChromaDB with metadata
   ```

4. **ChromaDB Storage**
   - **IDs**: `["_800713_1_chunk_000", "_800713_1_chunk_001", ...]`
   - **Embeddings**: 917 x 384 numpy arrays
   - **Metadata**: course_id, title, live_lms_url, module, etc.
   - **Documents**: Full chunk text

**ChromaDB Structure**:
```
chromadb_data/
├── chroma.sqlite3          # SQLite index
└── b215f4bc-.../           # Vector storage
    ├── data_level0.bin     # Embeddings
    └── index.bin           # HNSW index
```

---

## Runtime Query Flow

### Navigate Mode Query Flow

**Example**: Student asks "find resources about neural networks"

#### Request Path

1. **Chrome Extension (Frontend)**
   ```typescript
   // User types in PromptInput component
   const query = "find resources about neural networks";
   
   // API call
   const response = await fetch('http://localhost:8000/api/query', {
     method: 'POST',
     body: JSON.stringify({ query })
   });
   ```

2. **FastAPI Receives Request**
   ```python
   # main.py - Unified endpoint
   @app.post("/api/query")
   async def unified_query(request: QueryRequest):
       # Step 1: Orchestrator classification
       classification = classify_query_mode(request.query)
       # Result: {'mode': 'navigate', 'confidence': 0.75}
   ```

3. **Navigate LangGraph Workflow**
   ```python
   # navigate_graph.py
   state = {
       'query': 'find resources about neural networks',
       'chroma_db': chroma_instance
   }
   
   # Agent 1: Query Understanding
   state = query_understanding_agent(state)
   # Updates: parsed_query = {
   #   'key_terms': ['neural networks'],
   #   'intent': 'search',
   #   'is_in_scope': True
   # }
   
   # Agent 2: Retrieval
   state = retrieval_agent(state)
   # ChromaDB semantic search:
   #   1. Embed "neural networks" → 384-dim vector
   #   2. Cosine similarity search
   #   3. Return top 10 results
   # Updates: retrieved_chunks = [
   #   {'title': 'Neural Networks Overview', 'score': 0.23, ...},
   #   {'title': 'Backpropagation', 'score': 0.31, ...}
   # ]
   
   # Agent 3: Context
   state = context_agent(state)
   # Updates: enriched_results (adds related topics, prerequisites)
   
   # Agent 4: External Resources
   state = external_resources_agent(state)
   # Updates: external_resources = [
   #   {'type': 'youtube', 'url': '...', 'title': '3Blue1Brown Neural Networks'}
   # ]
   
   # Agent 5: Formatting
   state = formatting_agent(state)
   # Updates: formatted_response = {
   #   'answer_markdown': '# Neural Networks\n\n...',
   #   'top_results': [...],
   #   'external_resources': [...]
   # }
   ```

4. **Response Serialization**
   ```python
   return {
       'mode': 'navigate',
       'confidence': 0.75,
       'reasoning': 'Information retrieval pattern detected',
       'response': state['formatted_response'],
       'timestamp': '2025-10-07T...'
   }
   ```

5. **Chrome Extension Renders**
   ```typescript
   // NavigateMode.tsx
   <div className="results">
     {response.top_results.map(result => (
       <ResourceCard
         title={result.title}
         excerpt={result.excerpt}
         url={result.live_url}
       />
     ))}
   </div>
   ```

#### Data Transformations

| Stage | Data Format | Example |
|-------|-------------|---------|
| User Input | String | `"find resources about neural networks"` |
| Orchestrator | Dict | `{'mode': 'navigate', 'confidence': 0.75}` |
| Query Understanding | Dict | `{'key_terms': ['neural networks'], 'intent': 'search'}` |
| ChromaDB Query | Vector | `[0.023, -0.15, 0.087, ..., 0.12]` (384-dim) |
| ChromaDB Results | List[Dict] | `[{'id': '...', 'distance': 0.23, 'metadata': {...}}]` |
| Formatted Response | Dict | `{'answer_markdown': '...', 'top_results': [...]}` |
| UI Render | React JSX | `<ResourceCard title="..." />` |

---

### Educate Mode Query Flow

**Example**: Student asks "explain gradient descent"

#### Request Path

1. **Chrome Extension** (same as Navigate)

2. **FastAPI Receives Request**
   ```python
   # Orchestrator detects "explain" keyword + "gradient descent" topic
   classification = classify_query_mode("explain gradient descent")
   # Result: {'mode': 'educate', 'confidence': 0.95}
   ```

3. **Educate LangGraph Workflow**
   ```python
   # educate_graph.py
   state = {
       'query': 'explain gradient descent',
       'chroma_db': chroma_instance
   }
   
   # Agent 1: Math Translation
   math_markdown = explain_formula("gradient descent")
   # Returns 4-level explanation:
   #   Level 1: Intuition (blindfolded hill analogy)
   #   Level 2: Math (θ = θ - α∇J(θ) with LaTeX)
   #   Level 3: Code (25-line Python implementation)
   #   Level 4: Misconceptions (3 common mistakes)
   
   state['formatted_response'] = {
       'mode': 'educate',
       'answer_markdown': math_markdown,
       'is_in_scope': True
   }
   ```

4. **Response with LaTeX**
   ```json
   {
     "mode": "educate",
     "response": {
       "formatted_response": "## Gradient Descent\n\n### Intuition\n...\n\n### Math\n$$\\theta_{new} = \\theta_{old} - \\alpha \\nabla J(\\theta)$$\n\n### Code\n```python\ndef gradient_descent(...):\n    ...\n```\n\n### Misconceptions\n..."
     }
   }
   ```

5. **Chrome Extension Renders LaTeX**
   ```typescript
   // EducateMode.tsx
   import ReactMarkdown from 'react-markdown';
   import remarkMath from 'remark-math';
   import rehypeKatex from 'rehype-katex';
   
   <ReactMarkdown
     remarkPlugins={[remarkMath]}
     rehypePlugins={[rehypeKatex]}
   >
     {response.formatted_response}
   </ReactMarkdown>
   
   // KaTeX renders: θ_new = θ_old - α∇J(θ)
   ```

---

## Student Analytics Data Flow

### Interaction Tracking

**Flow**: User action → Supabase PostgreSQL

1. **Student Queries Extension**
   ```typescript
   // DualModeChat.tsx
   const studentId = getStudentId(); // Browser fingerprint
   const sessionId = `session-${Date.now()}`;
   ```

2. **Backend Logs Interaction**
   ```python
   # After LangGraph workflow completes
   supabase.table('session_history').insert({
       'student_id': student_id,
       'mode': 'navigate',
       'query': 'find neural networks',
       'response': {...},
       'timestamp': datetime.now(),
       'week_number': 5  # Detected from query context
   })
   ```

3. **Update Topic Mastery**
   ```python
   # If student completes quiz or reads explanation
   supabase.table('topic_mastery').upsert({
       'student_id': student_id,
       'topic_name': 'neural_networks',
       'mastery_level': 65,  # 0-100 scale
       'practice_count': 3,
       'last_practiced': datetime.now()
   })
   ```

4. **Dashboard Retrieval**
   ```typescript
   // Dashboard.tsx
   const stats = await fetch('/api/student/analytics', {
       method: 'POST',
       body: JSON.stringify({ student_id: studentId })
   });
   
   // Response:
   {
       'total_queries': 47,
       'navigate_usage': 28,
       'educate_usage': 19,
       'topics_mastered': ['agents', 'search_algorithms'],
       'weak_topics': ['computer_vision'],
       'study_streak_days': 5
   }
   ```

---

## External API Integration

### YouTube API Flow

**Triggered**: External Resources Agent in Navigate Mode

1. **Agent Receives Query**
   ```python
   # external_resources.py
   query_terms = state['parsed_query']['key_terms']
   # ['neural', 'networks']
   ```

2. **YouTube Search**
   ```python
   youtube = build('youtube', 'v3', developerKey=API_KEY)
   results = youtube.search().list(
       q=' '.join(query_terms) + ' tutorial',
       part='snippet',
       maxResults=3,
       type='video',
       videoDuration='medium'
   ).execute()
   ```

3. **Filter & Format**
   ```python
   videos = []
   for item in results['items']:
       videos.append({
           'type': 'youtube',
           'title': item['snippet']['title'],
           'url': f"https://youtube.com/watch?v={item['id']['videoId']}",
           'channel': item['snippet']['channelTitle'],
           'description': item['snippet']['description'][:200]
       })
   
   state['external_resources'] = videos
   ```

4. **UI Display**
   ```typescript
   // NavigateMode.tsx
   <ExternalResources>
     {resources.map(res => (
       <VideoCard
         title={res.title}
         thumbnail={res.thumbnail}
         url={res.url}
       />
     ))}
   </ExternalResources>
   ```

---

## Error Handling Data Flow

### Scenario: ChromaDB Connection Failure

1. **Startup Check**
   ```python
   # main.py - lifespan()
   try:
       chroma_db = LuminateChromaDB()
       doc_count = chroma_db.collection.count()
       if doc_count == 0:
           logger.warning("ChromaDB empty! Run setup_chromadb.py")
   except Exception as e:
       logger.error(f"ChromaDB init failed: {e}")
       raise  # Prevents API from starting
   ```

2. **Runtime Fallback**
   ```python
   # retrieval_agent.py
   try:
       results = chroma_db.query(query_text, n_results=10)
   except Exception as e:
       logger.error(f"ChromaDB query failed: {e}")
       state['retrieval_error'] = str(e)
       state['retrieved_chunks'] = []  # Empty results
       return state  # Continue workflow with empty results
   ```

3. **Frontend Handling**
   ```typescript
   // api.ts
   catch (error) {
     if (error.message.includes('fetch')) {
       throw new Error(
         'Backend not running. Start with: python scripts/start_backend.py'
       );
     }
   }
   
   // DualModeChat.tsx
   {error && (
     <ErrorMessage>
       {error}
       <Button onClick={retry}>Retry</Button>
     </ErrorMessage>
   )}
   ```

---

## Performance Optimization Data Flow

### Caching Strategy

**Problem**: Repeated queries cause redundant ChromaDB searches

**Solution**: In-memory LRU cache

```python
# retrieval_agent.py
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_chromadb_query(query_text: str, n_results: int):
    return chroma_db.query(query_text, n_results)

# First query: hits ChromaDB (200ms)
results1 = cached_chromadb_query("neural networks", 10)

# Repeat query: hits cache (0.5ms)
results2 = cached_chromadb_query("neural networks", 10)
```

### Streaming Responses

**Use Case**: Educate Mode explanations can be long

```python
# routers/auto.py
@router.post("/api/query/stream")
async def stream_query():
    async def generate():
        # Chunk 1: Orchestrator decision
        yield f"data: {json.dumps({'type': 'decision', ...})}\n\n"
        
        # Chunk 2: Partial response
        yield f"data: {json.dumps({'type': 'partial', ...})}\n\n"
        
        # Chunk 3: Complete response
        yield f"data: {json.dumps({'type': 'complete', ...})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

```typescript
// api.ts
const response = await fetch('/api/query/stream', { method: 'POST' });
const reader = response.body.getReader();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    // Update UI incrementally
    setResponse(prev => prev + chunk);
}
```

---

## Data Security & Privacy

### Student Anonymization

```python
# utils/studentId.ts (Frontend)
function getStudentId() {
    let id = localStorage.getItem('student_id');
    if (!id) {
        // Browser fingerprint (no PII)
        const fingerprint = `${navigator.userAgent}-${screen.width}-${screen.height}`;
        id = hashCode(fingerprint).toString();
        localStorage.setItem('student_id', id);
    }
    return id;
}
```

### Data Encryption

```python
# Supabase RLS (Row-Level Security)
CREATE POLICY student_data_isolation ON session_history
    FOR SELECT USING (student_id = current_user_id());

# Students can only see their own data
```

---

## Summary: Complete Data Journey

```
Blackboard Export
     ↓ (ingest_clean_luminate.py)
Cleaned JSON (593 files)
     ↓ (setup_chromadb.py)
ChromaDB Embeddings (917 vectors × 384 dim)
     ↓ (Runtime query)
FastAPI Orchestrator
     ├─ Navigate Mode
     │    ├─ Query Understanding
     │    ├─ ChromaDB Retrieval
     │    ├─ Context Enrichment
     │    ├─ External Resources (YouTube API)
     │    └─ Formatting
     └─ Educate Mode
          ├─ Math Translation
          ├─ Pedagogical Planning
          ├─ Quiz Generation
          └─ Interactive Formatting
     ↓
JSON Response
     ↓ (HTTP)
Chrome Extension
     ├─ Parse JSON
     ├─ Render Markdown
     ├─ Display LaTeX (KaTeX)
     └─ Show Resources
     ↓ (User interaction)
Supabase Analytics
     ├─ Session History
     ├─ Topic Mastery
     └─ Quiz Responses
```

**Total Data Flow Time**: 2-4 seconds (Navigate), 1-2 seconds (Educate with math)

---

**Last Updated**: October 7, 2025
