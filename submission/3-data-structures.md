# Luminate AI - Data Structures Documentation

## Overview

This document details all data structures, schemas, and formats used throughout the Luminate AI system.

---

## 1. Course Content Data

### Cleaned JSON Schema

**Location**: `cleaned/*.json`  
**Count**: 593 files

Each file represents one Blackboard course document with extracted text chunks.

```json
{
  "course_id": "string",           // Blackboard course ID (_29430_1)
  "course_name": "string",         // "Luminate"
  "module": "string",              // Folder name (Root, csfiles, etc.)
  "file_name": "string",           // Original filename
  "content_type": "string",        // File extension (.dat, .pdf, .xml, etc.)
  "bb_doc_id": "string",           // Blackboard document ID (_800713_1)
  "live_lms_url": "string",        // Direct link to Blackboard page
  "title": "string",               // Human-readable title
  "created_date": "string",        // ISO 8601 timestamp
  "updated_date": "string",        // ISO 8601 timestamp
  "raw_text_length": "integer",    // Character count before chunking
  "total_tokens": "integer",       // Approximate token count
  "num_chunks": "integer",         // Number of text chunks
  "chunks": [                      // Array of text chunks
    {
      "chunk_id": "string",        // Unique ID (_800713_1_chunk_000)
      "content": "string",         // Full text of chunk
      "tags": ["string"],          // Topic tags
      "live_lms_url": "string",    // Link to source page
      "token_count": "integer",    // Tokens in this chunk
      "chunk_index": "integer",    // 0-based index
      "total_chunks": "integer"    // Total chunks in document
    }
  ]
}
```

**Example**:

```json
{
  "course_id": "_29430_1",
  "course_name": "Luminate",
  "module": "Root",
  "file_name": "res00207.dat",
  "content_type": ".dat",
  "bb_doc_id": "_800713_1",
  "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800713_1?courseId=_29430_1&view=content&state=view",
  "title": "Lab Tutorial Logistic regression and data pre-processing",
  "created_date": "2024-10-04 18:31:46 EDT",
  "updated_date": "2024-11-13 23:45:18 EST",
  "raw_text_length": 2078,
  "total_tokens": 638,
  "num_chunks": 2,
  "chunks": [
    {
      "chunk_id": "_800713_1_chunk_000",
      "content": "Lab Tutorial Logistic regression and data pre-processing...",
      "tags": ["Root", "Lab Tutorial Logistic regression and data pre-processing"],
      "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800713_1?courseId=_29430_1&view=content&state=view",
      "token_count": 519,
      "chunk_index": 0,
      "total_chunks": 2
    }
  ]
}
```

**Statistics**:

- Total files: 593
- Total chunks: 917
- Total tokens: 300,563
- Avg tokens/file: 507
- Chunk size: 500-800 tokens

---

## 2. ChromaDB Vector Database

### Collection Schema

**Collection Name**: `comp237_content`  
**Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`  
**Dimension**: 384  
**Distance Metric**: Cosine similarity

### Document Structure

Each chunk from cleaned JSON becomes one ChromaDB document.

```python
{
    "id": "string",                    # Chunk ID (_800713_1_chunk_000)
    "embedding": [float],              # 384-dim vector
    "metadata": {
        "course_id": "string",
        "bb_doc_id": "string",
        "live_lms_url": "string",
        "title": "string",
        "module": "string",
        "content_type": "string",
        "created_date": "string",
        "chunk_index": int,
        "total_chunks": int,
        "token_count": int
    },
    "document": "string"               # Full chunk text
}
```

### Query Result Format

When querying ChromaDB, results are returned as:

```python
{
    "ids": [["_800713_1_chunk_000", "_800714_1_chunk_001", ...]],
    "distances": [[0.234, 0.456, ...]],  # Cosine distance (lower = more similar)
    "metadatas": [[{...}, {...}, ...]],
    "documents": [["Lab Tutorial...", "Neural Networks..."]]
}
```

**Distance Interpretation**:

- 0.0-0.3: Highly relevant
- 0.3-0.5: Moderately relevant
- 0.5-0.7: Somewhat relevant
- 0.7+: Low relevance

---

## 3. API Request/Response Schemas

### Unified Query Request

**Endpoint**: `POST /api/query`

```typescript
interface UnifiedQueryRequest {
  query: string;              // 1-500 characters
  student_id?: string;        // Browser fingerprint
  session_id?: string;        // Session identifier
  n_results?: number;         // 1-50, default 10
  min_score?: number;         // 0-1, default 0.0
  module_filter?: string;     // "Root", "csfiles", etc.
  content_type_filter?: string; // ".pdf", ".dat", etc.
}
```

### Unified Query Response

```typescript
interface UnifiedQueryResponse {
  mode: 'navigate' | 'educate';
  confidence: number;         // 0-1
  reasoning: string;          // Why mode was selected
  response: {
    formatted_response: string;  // Markdown text
    top_results?: Array<{
      title: string;
      excerpt: string;
      url: string;             // Blackboard live URL
      module: string;
      relevance_explanation?: string;
      score?: number;          // 0-1 similarity score
    }>;
    related_topics?: Array<{
      title: string;
      why_explore?: string;
    }>;
    external_resources?: Array<{
      title: string;
      url: string;
      description?: string;
      type: 'youtube' | 'oer' | 'khan_academy';
      channel?: string;        // For YouTube
    }>;
    total_results?: number;
    level?: string;            // Difficulty level
    misconceptions_detected?: Array<{
      wrong: string;
      right: string;
    }>;
    next_steps?: string[];
  };
  timestamp: string;           // ISO 8601
}
```

**Example Response (Navigate Mode)**:

```json
{
  "mode": "navigate",
  "confidence": 0.75,
  "reasoning": "Information retrieval pattern detected (2 navigate indicators)",
  "response": {
    "formatted_response": "# Neural Networks Resources\n\nFound 5 course materials...",
    "top_results": [
      {
        "title": "Topic 7.1 Neural Networks Overview",
        "excerpt": "Artificial neural networks are computing systems...",
        "url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800646_1",
        "module": "Root",
        "relevance_explanation": "Core concept explanation with diagrams",
        "score": 0.23
      }
    ],
    "external_resources": [
      {
        "title": "Neural Networks Explained - 3Blue1Brown",
        "url": "https://youtube.com/watch?v=...",
        "type": "youtube",
        "channel": "3Blue1Brown",
        "description": "Visual explanation of neural network fundamentals"
      }
    ],
    "total_results": 5
  },
  "timestamp": "2025-10-07T15:23:45.123Z"
}
```

**Example Response (Educate Mode)**:

```json
{
  "mode": "educate",
  "confidence": 0.95,
  "reasoning": "Query contains COMP-237 core topic: gradient descent",
  "response": {
    "formatted_response": "## Gradient Descent\n\n### Level 1: Intuition\n🎯 Imagine you're blindfolded...\n\n### Level 2: Math\n$$\\theta_{new} = \\theta_{old} - \\alpha \\nabla J(\\theta)$$\n\n...",
    "level": "4-level-explanation",
    "misconceptions_detected": [
      {
        "wrong": "❌ Bigger learning rate = faster = better",
        "right": "✅ Too big → overshoot & diverge"
      }
    ]
  },
  "timestamp": "2025-10-07T15:24:12.456Z"
}
```

---

## 4. LangGraph State Schemas

### Navigate State

```python
class NavigateState(TypedDict, total=False):
    # Input
    query: str
    chroma_db: Any
    
    # Agent outputs
    parsed_query: Dict[str, Any]
    retrieved_chunks: List[Dict]
    enriched_results: List[Dict]
    external_resources: List[Dict]
    formatted_response: Dict[str, Any]
    
    # Metadata
    retrieval_metadata: Dict[str, Any]
    retrieval_error: str
    context_warning: str
    is_in_scope: bool
    
    # For external resources
    original_query: str
    understood_query: str
    
    # Agent trace callback
    trace_callback: Optional[Callable]
```

**parsed_query Structure**:

```python
{
    'key_terms': ['neural', 'networks'],
    'intent': 'search',
    'scope': 'COMP-237',
    'is_in_scope': True,
    'module_hint': 'Root',
    'topic_category': 'machine_learning'
}
```

**retrieved_chunks Structure**:

```python
[
    {
        'id': '_800646_1_chunk_000',
        'distance': 0.23,
        'content': 'Neural networks are...',
        'metadata': {
            'title': 'Neural Networks Overview',
            'live_lms_url': 'https://...',
            'module': 'Root',
            'bb_doc_id': '_800646_1'
        }
    }
]
```

### Educate State

```python
class EducateState(TypedDict, total=False):
    query: str
    chroma_db: Any
    
    # Math translation
    math_markdown: str
    
    # Agent outputs
    parsed_query: Dict[str, Any]
    retrieved_chunks: List[Dict]
    enriched_results: List[Dict]
    teaching_strategy: str
    interaction_prompts: Dict[str, Any]
    student_context: Dict[str, Any]
    
    # Student modeling
    student_insights: Dict[str, Any]
    quiz_data: Dict[str, Any]
    study_plan: Dict[str, Any]
    detected_misconception: str
    
    # Output
    formatted_response: Dict[str, Any]
```

**teaching_strategy Values**:

- `"socratic"`: Question-based learning
- `"worked_example"`: Step-by-step solution
- `"scaffolding"`: Gradual complexity increase
- `"discovery"`: Guided exploration

**quiz_data Structure**:

```python
{
    'question': 'What is the purpose of the learning rate in gradient descent?',
    'options': [
        'A) Determines how big each step is',
        'B) Measures final model accuracy',
        'C) Counts training iterations',
        'D) Initializes random weights'
    ],
    'correct_answer': 'A',
    'explanation': 'Learning rate α controls step size...',
    'difficulty': 'medium'
}
```

**study_plan Structure**:

```python
{
    'topic': 'Neural Networks',
    'estimated_hours': 8,
    'week_breakdown': [
        {
            'day': 'Monday',
            'duration_minutes': 60,
            'activities': [
                'Watch 3Blue1Brown video (20 min)',
                'Read course notes (30 min)',
                'Practice exercises (10 min)'
            ],
            'resources': [
                {'title': '...', 'url': '...'}
            ]
        }
    ],
    'prerequisites': ['Calculus', 'Linear Algebra'],
    'success_criteria': [
        'Can explain forward propagation',
        'Can implement backpropagation'
    ]
}
```

---

## 5. Supabase Database Schema

### students Table

```sql
CREATE TABLE students (
    student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    browser_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Example Row**:

| student_id | browser_fingerprint | created_at | last_active |
|------------|---------------------|------------|-------------|
| 550e8400-e29b-41d4-a716-446655440000 | chrome-1920x1080-mac | 2025-10-01 10:00:00+00 | 2025-10-07 15:30:00+00 |

### session_history Table

```sql
CREATE TABLE session_history (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(student_id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('navigate', 'educate')),
    query TEXT NOT NULL,
    response JSONB,
    feedback_rating INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
    conversation_turn INTEGER DEFAULT 1,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14)
);
```

**Example Row**:

```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-07T15:23:45.123Z",
  "mode": "navigate",
  "query": "find neural networks resources",
  "response": {
    "top_results": [...],
    "external_resources": [...]
  },
  "feedback_rating": 4,
  "conversation_turn": 3,
  "week_number": 7
}
```

### topic_mastery Table

```sql
CREATE TABLE topic_mastery (
    student_id UUID REFERENCES students(student_id),
    topic_name VARCHAR(255) NOT NULL,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14),
    mastery_level INTEGER DEFAULT 0 CHECK (mastery_level BETWEEN 0 AND 100),
    last_practiced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    practice_count INTEGER DEFAULT 1,
    PRIMARY KEY (student_id, topic_name)
);
```

**Topic Names** (COMP-237 aligned):

- `agents`
- `search_algorithms`
- `machine_learning`
- `neural_networks`
- `nlp`
- `computer_vision`
- `ai_ethics`

**Example Row**:

| student_id | topic_name | week_number | mastery_level | practice_count |
|------------|------------|-------------|---------------|----------------|
| 550e8400... | neural_networks | 7 | 65 | 8 |

---

## 6. Math Translation Agent Data

### Formula Library Entry

```python
@dataclass
class MathTranslation:
    formula_name: str
    intuition: str              # Level 1: Analogy
    math_latex: str             # Level 2: LaTeX formula
    variable_explanations: Dict[str, str]
    code_example: str           # Level 3: Python code
    misconceptions: List[Dict[str, str]]  # Level 4: Common mistakes
    visual_hint: Optional[str]  # Matplotlib/Mermaid suggestion
```

**Example Entry (Gradient Descent)**:

```python
MathTranslation(
    formula_name="Gradient Descent",
    intuition="""
    🎯 Imagine you're blindfolded on a hill trying to reach the bottom:
    - You feel the slope with your feet (gradient)
    - You take a step downhill (update parameters)
    - You repeat until you can't go down anymore (convergence)
    """,
    math_latex=r"\theta_{new} = \theta_{old} - \alpha \nabla J(\theta)",
    variable_explanations={
        "θ (theta)": "Model parameters (e.g., weights)",
        "α (alpha)": "Learning rate (0.001-0.1)",
        "∇J(θ)": "Gradient - direction of steepest increase",
        "J(θ)": "Loss function - measures error"
    },
    code_example="""
import numpy as np

def gradient_descent(X, y, learning_rate=0.01, iterations=1000):
    m, n = X.shape
    theta = np.zeros(n)
    
    for i in range(iterations):
        predictions = X.dot(theta)
        gradient = (1/m) * X.T.dot(predictions - y)
        theta = theta - learning_rate * gradient
    
    return theta
    """,
    misconceptions=[
        {
            "wrong": "❌ Bigger learning rate = faster = better",
            "right": "✅ Too big → overshoot. Too small → slow."
        }
    ],
    visual_hint="3D surface plot with gradient vectors"
)
```

**Supported Formulas** (30+ total):

1. Gradient Descent
2. Backpropagation
3. Sigmoid Activation
4. ReLU Activation
5. Softmax
6. Cross-Entropy Loss
7. Mean Squared Error
8. Bayes' Theorem
9. TF-IDF
10. Cosine Similarity
11. Euclidean Distance
12. K-Means Clustering
13. Precision & Recall
14. F1 Score
15. Confusion Matrix
16. Logistic Regression
17. Linear Regression
18. Decision Tree Split
19. Random Forest
20. SVM Kernel

---

## 7. External Resources Data

### YouTube API Response

```json
{
  "kind": "youtube#searchListResponse",
  "items": [
    {
      "id": {
        "videoId": "aircAruvnKk"
      },
      "snippet": {
        "title": "But what is a neural network? | Chapter 1, Deep learning",
        "description": "Subscribe to stay notified about new videos...",
        "channelTitle": "3Blue1Brown",
        "publishedAt": "2017-10-05T15:00:01Z",
        "thumbnails": {
          "default": {
            "url": "https://i.ytimg.com/vi/aircAruvnKk/default.jpg"
          }
        }
      }
    }
  ]
}
```

**Transformed for UI**:

```typescript
interface ExternalResource {
  type: 'youtube' | 'oer' | 'khan_academy';
  title: string;
  url: string;
  description?: string;
  channel?: string;       // YouTube only
  thumbnail?: string;     // YouTube only
  duration?: string;      // "15:23"
  views?: number;         // For popularity sorting
}
```

---

## 8. Chrome Extension Storage

### LocalStorage Schema

```typescript
interface LocalStorageSchema {
  student_id: string;              // Browser fingerprint hash
  theme: 'light' | 'dark' | 'system';
  chat_history: ChatHistoryItem[];
  conversation_history: ConversationMessage[];
  notes: Note[];
  settings: {
    auto_mode_enabled: boolean;
    show_confidence_scores: boolean;
    latex_rendering: boolean;
  };
}

interface ChatHistoryItem {
  id: string;
  query: string;
  timestamp: Date;
  mode: 'navigate' | 'educate' | 'auto';
}

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  mode?: 'navigate' | 'educate';
  timestamp: string;
}

interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}
```

---

## 9. Error Response Formats

### API Error Response

```typescript
interface ErrorResponse {
  error: {
    code: string;            // "CHROMADB_UNAVAILABLE", "QUERY_TOO_LONG", etc.
    message: string;         // Human-readable error
    details?: any;           // Stack trace (dev mode only)
  };
  timestamp: string;
}
```

**Example**:

```json
{
  "error": {
    "code": "CHROMADB_UNAVAILABLE",
    "message": "ChromaDB connection failed. Please ensure the database is initialized.",
    "details": "PersistentClient error: Collection 'comp237_content' not found"
  },
  "timestamp": "2025-10-07T15:30:00.000Z"
}
```

---

## 10. Configuration Files

### Environment Variables (.env)

```bash
# Google Gemini API
GOOGLE_API_KEY=AIzaSy...

# Supabase
SUPABASE_URL=https://jedqonaiqpnqollmylkk.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# YouTube Data API
YOUTUBE_API_KEY=AIzaSy...

# Backend
BACKEND_PORT=8000
CHROMADB_PATH=../chromadb_data
```

### Vite Config (Extension Build)

```typescript
{
  base: './',
  build: {
    rollupOptions: {
      input: {
        sidepanel: 'sidepanel.html',
        background: 'src/background/index.ts'
      },
      output: {
        entryFileNames: '[name].js',
        format: 'es'
      }
    },
    outDir: 'dist'
  },
  resolve: {
    alias: {
      '@': './src'
    }
  }
}
```

---

## Data Size Summary

| Component | Count | Size | Format |
|-----------|-------|------|--------|
| Cleaned JSON Files | 593 | ~8 MB | JSON |
| ChromaDB Embeddings | 917 | ~12 MB | Binary vectors |
| Extension Bundle | 1 | 1.89 MB | JavaScript |
| Total Course Content | - | 300,563 tokens | Text |

**Token Distribution**:

- Root module: 193,575 tokens (64%)
- csfiles module: 101,142 tokens (34%)
- Other modules: 5,846 tokens (2%)

---

**Last Updated**: October 7, 2025
