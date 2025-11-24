# Docker Architecture - Luminate AI Course Marshal

## Container Overview

### 1. **api_brain** (Backend API)
- **Image**: `luminate-ai-api_brain` (custom built)
- **Port**: 8000
- **Role**: Main FastAPI application server
- **Responsibilities**:
  - Handles HTTP requests from the Chrome extension
  - Orchestrates the AI agent (Governor-Supervisor-Worker)
  - Manages RAG retrieval from ChromaDB
  - Streams responses via Server-Sent Events (SSE)
  - Enforces academic integrity policies
  - Routes queries to appropriate LLM models
- **Dependencies**: memory_store, cache_layer, observer
- **Health Check**: `http://localhost:8000/health`

### 2. **memory_store** (ChromaDB)
- **Image**: `chromadb/chroma:latest`
- **Port**: 8001 (mapped from internal 8000)
- **Role**: Vector database for course materials
- **Responsibilities**:
  - Stores document embeddings (768-dimensional Gemini embeddings)
  - Enables semantic search over course content
  - Maintains 219 document chunks from COMP 237 materials
  - Provides similarity search for RAG retrieval
- **Data**: Persistent storage in `chromadb_data` volume
- **Collection**: `comp237_course_materials`

### 3. **cache_layer** (Redis)
- **Image**: `redis:alpine`
- **Port**: 6379
- **Role**: In-memory caching and session storage
- **Responsibilities**:
  - Caches frequently accessed data
  - Stores temporary session information
  - Reduces database load
  - Speeds up repeated queries
- **Data**: Persistent storage with AOF (Append-Only File)
- **Volume**: `redis_data`

### 4. **observer** (Langfuse UI)
- **Image**: `langfuse/langfuse:latest`
- **Port**: 3000
- **Role**: Observability and tracing web interface
- **Responsibilities**:
  - Displays AI agent execution traces
  - Tracks LLM calls, token usage, and costs
  - Provides debugging interface for agent behavior
  - Stores trace data in PostgreSQL
  - Handles background worker jobs internally
- **Access**: `http://localhost:3000`
- **Version**: 3.133.0

### 5. **langfuse_postgres** (Langfuse Database)
- **Image**: `postgres:15-alpine`
- **Port**: 5432 (internal only)
- **Role**: Dedicated database for Langfuse observability
- **Responsibilities**:
  - Stores trace metadata
  - Stores Langfuse user accounts and API keys (for Langfuse UI only)
  - Stores project configurations (Langfuse projects)
  - Stores scores and evaluations
- **Data**: Persistent storage in `postgres_data` volume
- **Credentials**: langfuse/langfuse (dev only)
- **Note**: This is separate from Supabase (used for student/admin auth)

### 6. **clickhouse** (Analytics Database)
- **Image**: `clickhouse/clickhouse-server:latest`
- **Ports**: 8123 (HTTP), 9000 (Native)
- **Role**: High-performance analytics database for Langfuse
- **Responsibilities**:
  - Stores large-scale trace data
  - Enables fast analytical queries
  - Powers Langfuse dashboards
  - Handles time-series data
- **Data**: Persistent storage in `clickhouse_data` volume
- **Mode**: Standalone (non-clustered)

### 7. **minio** (S3-Compatible Storage)
- **Image**: `minio/minio:latest`
- **Ports**: 9001 (Console), 9002 (API)
- **Role**: Object storage for large trace payloads
- **Responsibilities**:
  - Stores large trace data (>1MB)
  - Stores media files (audio, images)
  - Provides S3-compatible API
  - Backs up event data
- **Data**: Persistent storage in `minio_data` volume
- **Console**: `http://localhost:9001`
- **Credentials**: minioadmin/minioadmin

## Data Flow

### Student Query Flow
```
1. Chrome Extension (Frontend)
   ↓ HTTP POST /api/chat/stream
2. api_brain (Backend)
   ↓ Authenticate with Supabase JWT
3. Governor (Policy Check)
   ↓ Query ChromaDB for scope validation
4. memory_store (ChromaDB)
   ↓ Return similarity scores
5. Supervisor (Intent Routing)
   ↓ Select model (Gemini/Groq)
6. RAG Node (Context Retrieval)
   ↓ Query ChromaDB for relevant docs
7. memory_store (ChromaDB)
   ↓ Return top-k documents
8. LLM Call (Gemini/Groq)
   ↓ Generate response
9. Response Stream (SSE)
   ↓ Stream to frontend
10. Chrome Extension
    ↓ Display to student
```

### Observability Flow
```
1. api_brain (Backend)
   ↓ Create trace via Langfuse SDK
2. observer (Langfuse)
   ↓ Store trace metadata
3. langfuse_postgres (PostgreSQL)
   ↓ Store in Langfuse database
4. clickhouse (Analytics)
   ↓ Store for analytics
5. minio (S3 Storage)
   ↓ Store large payloads
```

### Database Architecture Clarification

**Two Separate Database Systems:**

1. **Supabase** (External Cloud Service)
   - **Purpose**: User authentication and application data
   - **Users**: Students and Admins
   - **Authentication**: Email OTP (magic links)
   - **Data Stored**:
     - User profiles
     - Session tokens
     - Application-specific data (future: chat history, preferences)
   - **Access**: Via Supabase client SDK
   - **Not in Docker**: Hosted by Supabase

2. **langfuse_postgres** (Local Docker Container)
   - **Purpose**: Langfuse observability data only
   - **Users**: Langfuse UI users (developers/admins monitoring traces)
   - **Data Stored**:
     - AI agent execution traces
     - LLM call metadata
     - Token usage and costs
     - Langfuse project configurations
   - **Access**: Via Langfuse SDK
   - **In Docker**: Part of local observability stack

**Why Two Databases?**
- **Separation of Concerns**: User auth (Supabase) vs. observability (Langfuse)
- **Scalability**: Each can scale independently
- **Security**: User data isolated from debug/trace data
- **Flexibility**: Can swap Supabase for another auth provider without affecting observability

## Network Architecture

All containers are connected via the `luminate_network` bridge network:

```
luminate_network (bridge)
├── api_brain (can access all services by name)
├── memory_store (accessible as "memory_store:8000")
├── cache_layer (accessible as "cache_layer:6379")
├── observer (accessible as "observer:3000")
├── langfuse_postgres (accessible as "postgres:5432")
├── clickhouse (accessible as "clickhouse:8123")
└── minio (accessible as "minio:9000")
```

## Volume Persistence

Data is persisted across container restarts:

- **backend_data**: Backend application data
- **chromadb_data**: Vector embeddings and documents
- **redis_data**: Cache and session data
- **postgres_data**: Langfuse trace metadata
- **clickhouse_data**: Analytics data
- **minio_data**: Large file storage

## Resource Usage

Current CPU usage (from screenshot):
- **luminate-ai** (compose project): 36.68%
- **clickhouse**: 23.49% (analytics queries)
- **langfuse_postgres**: 12.65% (database operations)
- **cache_layer**: 0.19% (minimal, as expected)
- **api_brain**: 0.35% (idle, waiting for requests)
- **memory_store**: 0% (idle)
- **minio**: 0% (idle)
- **observer**: 0% (idle)

## Service Dependencies

### Startup Order
1. **postgres** (must be healthy before observer)
2. **clickhouse** (must be healthy before observer)
3. **cache_layer** (must start before observer)
4. **minio** (must start before observer)
5. **memory_store** (must start before api_brain)
6. **observer** (must start before api_brain)
7. **api_brain** (depends on all above)

### Critical Path
For the system to function:
- ✅ **api_brain** must be running (core API)
- ✅ **memory_store** must be running (RAG retrieval)
- ⚠️ **observer** is optional (observability only)
- ⚠️ **cache_layer** is optional (performance optimization)

## Troubleshooting

### Container Not Starting
```bash
# Check logs
docker compose logs [container_name] --tail 50

# Check health
docker compose ps

# Restart specific service
docker compose restart [container_name]
```

### Port Conflicts
If ports are already in use:
- 8000: Backend API (change in docker-compose.yml)
- 8001: ChromaDB (change in docker-compose.yml)
- 3000: Langfuse UI (change in docker-compose.yml)
- 6379: Redis (change in docker-compose.yml)

### Data Reset
To reset all data:
```bash
# Stop all containers
docker compose down

# Remove volumes
docker volume rm luminate-ai_chromadb_data
docker volume rm luminate-ai_postgres_data
docker volume rm luminate-ai_clickhouse_data

# Restart
docker compose up -d
```

## Production Considerations

### Security
- Change default credentials (postgres, minio)
- Use secrets management (not .env files)
- Enable TLS/SSL for all services
- Restrict network access
- Use read-only file systems where possible

### Scaling
- **api_brain**: Can be horizontally scaled (multiple replicas)
- **memory_store**: Can be scaled with Chroma distributed mode
- **cache_layer**: Can use Redis Cluster
- **observer**: Can be scaled with load balancer
- **postgres**: Consider managed PostgreSQL (RDS, Cloud SQL)
- **clickhouse**: Can be clustered for high availability

### Monitoring
- Add Prometheus exporters for metrics
- Use Grafana for visualization
- Set up alerts for container health
- Monitor disk usage for volumes
- Track API response times

## Summary

The system uses **8 Docker containers** working together:

1. **api_brain**: The brain 🧠 - orchestrates everything
2. **memory_store**: The memory 💾 - stores course knowledge
3. **cache_layer**: The speed boost ⚡ - caches frequently used data
4. **observer**: The eyes 👀 - monitors what's happening
5. **langfuse_postgres**: The notebook 📓 - records trace history
6. **clickhouse**: The analyzer 📊 - analyzes patterns
7. **minio**: The vault 🗄️ - stores large files

Together, they create a robust, observable, and scalable AI tutoring system.

