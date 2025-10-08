# Luminate AI - Architecture Diagram

## System Architecture (After Improvements)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Chrome Extension                            │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      ChatInterface.tsx                          │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │ │
│  │  │  Copy    │  │  Clear   │  │  Retry   │  │  Session │      │ │
│  │  │  Button  │  │  History │  │  Button  │  │  Restore │      │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │ │
│  │                                                                  │ │
│  │  ┌───────────────────────────────────────────────────────────┐ │ │
│  │  │              Error Boundary (catches crashes)             │ │ │
│  │  └───────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                 ↓                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                       Services Layer                            │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐        │ │
│  │  │   api.ts     │  │  session.ts  │  │  clipboard.ts │        │ │
│  │  │              │  │              │  │               │        │ │
│  │  │  • Retry 3x  │  │  • Auto-save │  │  • Copy w/    │        │ │
│  │  │  • Backoff   │  │  • Dual-layer│  │    formatting │        │ │
│  │  │  • Timeout   │  │  • Restore   │  │  • Cross-     │        │ │
│  │  │              │  │              │  │    browser    │        │ │
│  │  └──────────────┘  └──────────────┘  └───────────────┘        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                 ↓                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      Local Storage                              │ │
│  │          (Session backup, instant access)                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    │ HTTP Request (with retry)
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                              │
│                      (localhost:8000)                                │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        Middleware Layer                         │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │ Rate Limiter │→ │  Validator   │→ │    Cache     │         │ │
│  │  │              │  │              │  │              │         │ │
│  │  │  60 req/min  │  │  • Sanitize  │  │  5-min TTL   │         │ │
│  │  │  per IP      │  │  • Clamp     │  │  In-memory   │         │ │
│  │  │              │  │  • Normalize │  │              │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  │                                            ↓                     │ │
│  │                                       Cache Hit?                 │ │
│  │                                        /      \                  │ │
│  │                                      Yes      No                 │ │
│  │                                       ↓        ↓                 │ │
│  │                                   Return   Continue              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        API Endpoints                            │ │
│  │                                                                  │ │
│  │  GET  /health                   - Health check                  │ │
│  │  GET  /stats                    - Metrics + cache stats         │ │
│  │  POST /query/navigate           - Basic search (cached)         │ │
│  │  POST /langgraph/navigate       - Advanced search (cached)      │ │
│  │  POST /external-resources       - External links               │ │
│  │  POST /conversation/save        - Save history                  │ │
│  │  GET  /conversation/load/:id    - Load history                  │ │
│  │  DELETE /conversation/:id       - Delete history                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                 ↓                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      Metrics Collector                          │ │
│  │                                                                  │ │
│  │  • Total requests              • Response times                 │ │
│  │  • Success/error rates         • Endpoint usage                 │ │
│  │  • Error types                 • Requests per second            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                 ↓                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      LangGraph Workflow                         │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │    Query     │→ │  Retrieval   │→ │   Context    │→        │ │
│  │  │ Understanding│  │    Agent     │  │    Agent     │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │  Formatting  │← │  External    │← │     LLM      │         │ │
│  │  │    Agent     │  │  Resources   │  │   (Ollama)   │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                           Data Layer                                 │
│                                                                       │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────┐ │
│  │     ChromaDB       │  │  Conversation      │  │   Logs        │ │
│  │                    │  │  Store             │  │               │ │
│  │  917 documents     │  │  (in-memory)       │  │  app.log      │ │
│  │  Vector embeddings │  │  Session history   │  │  errors.log   │ │
│  └────────────────────┘  └────────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow with Caching

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Frontend: Retry Logic (3 attempts)     │
│  • Attempt 1: Immediate                 │
│  • Attempt 2: Wait 1s                   │
│  • Attempt 3: Wait 2s                   │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Backend: Rate Limiter                  │
│  • Check IP against 60/min limit        │
│  • Allow or reject (429)                │
└──────────────┬──────────────────────────┘
               │ Allowed
               ↓
┌─────────────────────────────────────────┐
│  Validator: Sanitize Input              │
│  • Trim/normalize query                 │
│  • Clamp n_results (1-50)               │
│  • Clamp min_score (0-1)                │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Cache: Check for cached response       │
│  • Hash query + params                  │
│  • Check TTL (5 min)                    │
└──────────────┬──────────────────────────┘
               │
          Cache Hit?
           /      \
         Yes      No
          │        │
          │        ↓
          │   ┌─────────────────────────┐
          │   │  Process Query:         │
          │   │  1. ChromaDB search     │
          │   │  2. LangGraph workflow  │
          │   │  3. Format response     │
          │   └──────┬──────────────────┘
          │          │
          │          ↓
          │   ┌─────────────────────────┐
          │   │  Cache result           │
          │   │  • Store with TTL       │
          │   │  • Update metrics       │
          │   └──────┬──────────────────┘
          │          │
          └──────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Metrics: Record request                │
│  • Response time                        │
│  • Success/failure                      │
│  • Endpoint                             │
│  • Error type (if any)                  │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Return Response                        │
│  • Formatted answer                     │
│  • Sources with URLs                    │
│  • Related topics                       │
│  • External resources                   │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Frontend: Display & Save               │
│  • Show response with skeleton→content  │
│  • Save to localStorage (instant)       │
│  • Queue backend save (30s)             │
└─────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────┐
│  API Error  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Error Type Detection                   │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴──────┐
       │              │
       ↓              ↓
┌─────────────┐  ┌─────────────┐
│  Network    │  │  Rate Limit │
│  Error      │  │  (429)      │
└──────┬──────┘  └──────┬──────┘
       │                │
       ↓                ↓
   Retry 3x         Wait & Retry
   (backoff)        (auto)
       │                │
       └────────┬───────┘
                │
                ↓ All retries failed
┌─────────────────────────────────────────┐
│  Error Boundary / Component             │
│  • Catch React errors                   │
│  • Show friendly message                │
│  • Offer retry button                   │
│  • Log to console                       │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  User sees:                             │
│  • Specific error message               │
│  • Retry button (keeps context)         │
│  • No app crash                         │
└─────────────────────────────────────────┘
```

## Session Persistence Flow

```
┌──────────────────────────────────────────┐
│  User sends message                      │
└─────────────┬────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────┐
│  Add to messages state                   │
└─────────────┬────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────┐
│  Save to localStorage (immediate)        │
│  • sessionId: "session_12345_abc"        │
│  • messages: [...]                       │
└─────────────┬────────────────────────────┘
              │
              ↓
      Wait 30 seconds (auto-save timer)
              │
              ↓
┌──────────────────────────────────────────┐
│  POST /conversation/save                 │
│  • Backend stores in memory              │
│  • Can be upgraded to Redis/DB           │
└─────────────┬────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────┐
│  User closes extension                   │
└─────────────┬────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────┐
│  User reopens extension                  │
└─────────────┬────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────┐
│  initializeSession()                     │
│  1. Try GET /conversation/load/:id       │
│     (backend)                            │
│  2. Fallback to localStorage             │
│     (if backend fails)                   │
└─────────────┬────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────┐
│  Restore all messages                    │
│  • User continues where they left off   │
│  • No data loss                          │
└──────────────────────────────────────────┘
```

## Metrics Collection

```
┌─────────────────────────────────────────┐
│  Every API Request                      │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  MetricsCollector.record_request()      │
│  • endpoint: "/langgraph/navigate"      │
│  • response_time: 245.67 ms             │
│  • success: true                        │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Update Metrics:                        │
│  • total_requests++                     │
│  • endpoint_calls[endpoint]++           │
│  • response_times.append(time)          │
│  • total_errors++ (if error)            │
│  • error_types[type]++ (if error)       │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Calculate Stats:                       │
│  • success_rate = (total - errors) / total │
│  • avg_response_time = mean(times)      │
│  • requests_per_second = total / uptime │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Available at GET /stats                │
│  {                                      │
│    "total_requests": 1523,              │
│    "success_rate": 0.992,               │
│    "avg_response_time_ms": 245.67,      │
│    "cache_size": 45,                    │
│    ...                                  │
│  }                                      │
└─────────────────────────────────────────┘
```

## Component Hierarchy

```
App
└── ErrorBoundary
    └── SidePanel
        └── ChatInterface
            ├── ConversationHeader
            │   ├── Logo & Title
            │   ├── Clear History Button
            │   └── Close Button
            │
            ├── ConversationContent
            │   └── Messages[]
            │       ├── Message (user)
            │       │   └── MessageContent
            │       │       └── "User question"
            │       │
            │       └── Message (assistant)
            │           └── MessageContent
            │               ├── Response text
            │               ├── Copy Button
            │               ├── Sources (if available)
            │               ├── ExternalResources (if available)
            │               ├── RelatedTopics (if available)
            │               └── Retry Button (if error)
            │
            ├── Loading State
            │   └── FullResponseSkeleton
            │       ├── MessageSkeleton
            │       ├── SourcesSkeleton
            │       └── RelatedTopicsSkeleton
            │
            └── ConversationFooter
                └── PromptInput
                    ├── Textarea
                    └── Send Button
```

## Technology Stack

```
Frontend:
├── React 18.2.0
├── TypeScript 5.2.2
├── Tailwind CSS 3.4.1
├── Vite 5.2.0
├── Vitest 3.2.4 (testing)
└── Chrome Extension APIs

Backend:
├── Python 3.11+
├── FastAPI (latest)
├── ChromaDB (vector database)
├── LangGraph (AI workflow)
├── Ollama (local LLM)
└── pytest (testing)

Infrastructure:
├── Local development
├── In-memory caching
├── File-based logging
└── localStorage + optional backend persistence
```

---

**Last Updated:** 2024-01-01  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
