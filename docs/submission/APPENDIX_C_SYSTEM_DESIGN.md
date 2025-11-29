# Appendix C: System Design

## Luminate AI Course Marshal

---

## C.1 Technology Stack

### C.1.1 Hardware Specifications

#### Development Environment

| Component | Specification |
|-----------|---------------|
| **CPU** | Apple M1/M2 or Intel i7+ equivalent |
| **RAM** | 16 GB minimum, 32 GB recommended |
| **Storage** | 50 GB SSD (for Docker, ChromaDB data) |
| **Network** | Broadband internet for API calls |

#### Production Environment (Recommended)

| Component | Specification | Provider Options |
|-----------|---------------|------------------|
| **Backend Server** | 2 vCPU, 4 GB RAM | Railway, Render, AWS EC2 |
| **ChromaDB** | 2 vCPU, 4 GB RAM, 20 GB SSD | Self-hosted Docker |
| **Redis Cache** | 1 vCPU, 1 GB RAM | Railway, Render Redis |
| **Database** | Supabase Free/Pro tier | Supabase Cloud |

### C.1.2 Software Stack

#### Backend Technologies

| Technology | Version | Purpose | License |
|------------|---------|---------|---------|
| **Python** | 3.11+ | Runtime | PSF |
| **FastAPI** | 0.110+ | Web framework | MIT |
| **LangGraph** | 0.1+ | Agent orchestration | MIT |
| **LangChain** | 0.2+ | LLM abstractions | MIT |
| **Pydantic** | 2.7+ | Data validation | MIT |
| **ChromaDB** | 0.5+ | Vector database | Apache 2.0 |
| **Redis** | 5.0+ | Caching | BSD |
| **uvicorn** | 0.29+ | ASGI server | BSD |

#### Frontend Technologies

| Technology | Version | Purpose | License |
|------------|---------|---------|---------|
| **TypeScript** | 5.0+ | Language | Apache 2.0 |
| **React** | 18+ | UI framework | MIT |
| **Plasmo** | Latest | Extension framework | MIT |
| **Tailwind CSS** | 3.4+ | Styling | MIT |
| **Shadcn/UI** | Latest | Component library | MIT |
| **Supabase Client** | 2.4+ | Auth/Database | MIT |

#### AI Model Providers

| Provider | Model | Use Case | Pricing Model |
|----------|-------|----------|---------------|
| **Google** | Gemini 2.0 Flash | Default reasoning | Pay-per-token |
| **Google** | Gemini Embedding | Document vectorization | Pay-per-token |
| **Groq** | Llama 3.3 70B | Code generation | Free tier / Pay |
| **E2B** | Code Interpreter | Python sandbox | Pay-per-execution |

#### Infrastructure Services

| Service | Purpose | Provider |
|---------|---------|----------|
| **Authentication** | User auth, JWT | Supabase Auth |
| **Database** | User data, mastery | Supabase PostgreSQL |
| **Vector Store** | Course embeddings | ChromaDB (self-hosted) |
| **Observability** | Tracing, metrics | Langfuse |
| **Containerization** | Service isolation | Docker Compose |

### C.1.3 Development Tools

| Tool | Purpose |
|------|---------|
| **VS Code / Cursor** | IDE |
| **Docker Desktop** | Container management |
| **Postman / Thunder Client** | API testing |
| **Chrome DevTools** | Extension debugging |
| **Git / GitHub** | Version control |
| **pnpm** | Package management (frontend) |
| **pip** | Package management (backend) |

---

## C.2 AI Capability Description

### C.2.1 AI Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI CAPABILITY ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                        INPUT PROCESSING                               │ │
│   │                                                                        │ │
│   │   User Query → Tokenization → Embedding (for scope check)             │ │
│   │                                                                        │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      ▼                                      │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                     POLICY ENFORCEMENT LAYER                          │ │
│   │                          (GOVERNOR)                                   │ │
│   │                                                                        │ │
│   │   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │ │
│   │   │   Law 1        │  │   Law 2        │  │   Law 3        │         │ │
│   │   │   SCOPE        │  │   INTEGRITY    │  │   MASTERY      │         │ │
│   │   │                │  │                │  │                │         │ │
│   │   │ ChromaDB       │  │ Pattern        │  │ Prerequisites  │         │ │
│   │   │ Distance       │  │ Matching       │  │ Check          │         │ │
│   │   └────────────────┘  └────────────────┘  └────────────────┘         │ │
│   │                                                                        │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      ▼                                      │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                      INTENT CLASSIFICATION                            │ │
│   │                         (SUPERVISOR)                                  │ │
│   │                                                                        │ │
│   │   Input: User Query                                                   │ │
│   │   Output: Intent + Model Selection                                    │ │
│   │                                                                        │ │
│   │   Intents: tutor | math | coder | syllabus | fast                    │ │
│   │   Models:  Gemini Tutor | Gemini Flash | Groq Llama                  │ │
│   │                                                                        │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                    ┌─────────────────┼─────────────────┐                   │
│                    ▼                 ▼                 ▼                   │
│   ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐    │
│   │  PEDAGOGICAL       │ │  MATH              │ │  GENERAL           │    │
│   │  TUTOR AGENT       │ │  AGENT             │ │  AGENT             │    │
│   │                    │ │                    │ │                    │    │
│   │  - Socratic        │ │  - Step-by-step   │ │  - RAG retrieval  │    │
│   │  - Scaffolding     │ │  - LaTeX          │ │  - Tool calling   │    │
│   │  - Confusion       │ │  - Intuition      │ │  - Code gen       │    │
│   │    detection       │ │  - Practice       │ │                    │    │
│   └────────────────────┘ └────────────────────┘ └────────────────────┘    │
│                    │                 │                 │                   │
│                    └─────────────────┴─────────────────┘                   │
│                                      │                                      │
│                                      ▼                                      │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                      RESPONSE GENERATION                              │ │
│   │                                                                        │ │
│   │   - Streaming output (SSE)                                            │ │
│   │   - Source citation injection                                         │ │
│   │   - Generative UI markers (<quiz>, <code>, etc.)                     │ │
│   │                                                                        │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      ▼                                      │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                         EVALUATION                                    │ │
│   │                                                                        │ │
│   │   - Mastery score update                                              │ │
│   │   - Interaction logging                                               │ │
│   │   - Analytics capture                                                 │ │
│   │                                                                        │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### C.2.2 Model Specifications

#### Gemini 2.0 Flash (Primary Model)

| Attribute | Value |
|-----------|-------|
| **Provider** | Google AI |
| **Context Window** | 1M tokens |
| **Output Tokens** | 8K tokens |
| **Strengths** | Fast inference, strong reasoning, multimodal |
| **Use Cases** | Default tutoring, syllabus queries, general AI Q&A |
| **Temperature (Tutor)** | 0.9 (creative, exploratory) |
| **Temperature (General)** | 0.7 (balanced) |

#### Llama 3.3 70B via Groq

| Attribute | Value |
|-----------|-------|
| **Provider** | Groq |
| **Context Window** | 128K tokens |
| **Output Tokens** | 32K tokens |
| **Strengths** | Excellent code generation, fastest inference |
| **Use Cases** | Code generation, debugging assistance |
| **Temperature** | 0.5 (deterministic code) |

#### Gemini Embedding Model

| Attribute | Value |
|-----------|-------|
| **Model Name** | models/embedding-001 |
| **Dimensions** | 768 |
| **Max Input** | 2048 tokens |
| **Use Cases** | Document vectorization, query embedding |

### C.2.3 RAG Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RAG DATA PIPELINE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ DOCUMENT INGESTION                                                    │ │
│  │                                                                        │ │
│  │   Blackboard ZIP                                                      │ │
│  │        │                                                               │ │
│  │        ▼                                                               │ │
│  │   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │ │
│  │   │  Extract     │────▶│  Parse       │────▶│  Identify    │          │ │
│  │   │  Archive     │     │  Manifest    │     │  Documents   │          │ │
│  │   └──────────────┘     └──────────────┘     └──────────────┘          │ │
│  │                                                    │                   │ │
│  │                                                    ▼                   │ │
│  │   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │ │
│  │   │  Store in    │◀────│  Generate    │◀────│  Process     │          │ │
│  │   │  ChromaDB    │     │  Embeddings  │     │  & Chunk     │          │ │
│  │   └──────────────┘     └──────────────┘     └──────────────┘          │ │
│  │                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ QUERY PROCESSING                                                      │ │
│  │                                                                        │ │
│  │   User Query                                                          │ │
│  │        │                                                               │ │
│  │        ▼                                                               │ │
│  │   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │ │
│  │   │  Embed       │────▶│  Similarity  │────▶│  Rank &      │          │ │
│  │   │  Query       │     │  Search      │     │  Filter      │          │ │
│  │   └──────────────┘     └──────────────┘     └──────────────┘          │ │
│  │                                                    │                   │ │
│  │                                                    ▼                   │ │
│  │                                             ┌──────────────┐          │ │
│  │                                             │  Top-K       │          │ │
│  │                                             │  Documents   │          │ │
│  │                                             │  (k=5)       │          │ │
│  │                                             └──────────────┘          │ │
│  │                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### C.2.4 Pedagogical Strategies

| Strategy | Agent | Implementation |
|----------|-------|----------------|
| **Socratic Questioning** | Tutor | Ask clarifying questions before explaining |
| **Scaffolded Support** | Tutor | Hint → Guided → Explained progression |
| **Confusion Detection** | Tutor | Pattern matching for struggle signals |
| **Step-by-Step** | Math | Break derivations into numbered steps |
| **Visual First** | Math | Intuitive explanation before formal math |
| **Practice Problems** | Math | Generate follow-up practice |
| **Code Skeletons** | Coder | Provide structure, not full solutions |

---

## C.3 Database Schema

### C.3.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATABASE SCHEMA (ERD)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────┐         ┌─────────────────────┐                  │
│   │     auth.users      │         │      concepts       │                  │
│   │   (Supabase Auth)   │         │                     │                  │
│   ├─────────────────────┤         ├─────────────────────┤                  │
│   │ PK id (UUID)        │         │ PK id (TEXT)        │                  │
│   │    email            │         │    name             │                  │
│   │    created_at       │         │ FK parent_concept_id│──┐               │
│   │    ...              │         │    prerequisites[]  │  │               │
│   └─────────┬───────────┘         │    course_id        │  │               │
│             │                     │    created_at       │◀─┘               │
│             │                     └─────────────────────┘                  │
│             │                                                               │
│             │ 1                                                             │
│             │                                                               │
│             ├──────────────────────────────────┬───────────────────────┐   │
│             │                                  │                       │   │
│             ▼ N                                ▼ N                     ▼ N │
│   ┌─────────────────────┐         ┌─────────────────────┐  ┌─────────────┐│
│   │  student_mastery    │         │    interactions     │  │    chats    ││
│   ├─────────────────────┤         ├─────────────────────┤  ├─────────────┤│
│   │ PK,FK user_id (UUID)│         │ PK id (UUID)        │  │ PK id (UUID)││
│   │ PK concept_tag      │         │ FK student_id       │  │ FK user_id  ││
│   │    mastery_score    │         │    type             │  │ FK folder_id││
│   │    decay_factor     │         │    concept_focus    │  │    title    ││
│   │    last_assessed_at │         │    outcome          │  │    is_star  ││
│   └─────────────────────┘         │    intent           │  │    created  ││
│                                   │    agent_used       │  └──────┬──────┘│
│                                   │    scaffolding_level│         │       │
│                                   │    created_at       │         │ 1     │
│                                   └─────────────────────┘         │       │
│                                                                   ▼ N     │
│                                                           ┌─────────────┐ │
│                                                           │  messages   │ │
│                                                           ├─────────────┤ │
│                                                           │ PK id (UUID)│ │
│                                                           │ FK chat_id  │ │
│                                                           │    role     │ │
│                                                           │    content  │ │
│                                                           │    metadata │ │
│                                                           │    created  │ │
│                                                           └─────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### C.3.2 Table Definitions

```sql
-- Concepts table (static course data)
CREATE TABLE concepts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_concept_id TEXT REFERENCES concepts(id),
    prerequisites TEXT[],
    course_id TEXT DEFAULT 'COMP237',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Student Mastery table
CREATE TABLE student_mastery (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    concept_tag TEXT NOT NULL,
    mastery_score FLOAT CHECK (mastery_score >= 0 AND mastery_score <= 1),
    decay_factor FLOAT DEFAULT 0.95,
    last_assessed_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, concept_tag)
);

-- Interactions log table
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    concept_focus TEXT,
    outcome TEXT,
    intent TEXT,
    agent_used TEXT,
    scaffolding_level TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat history tables
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    parent_id UUID REFERENCES folders(id),
    is_starred BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
    title TEXT NOT NULL DEFAULT 'New Chat',
    is_starred BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### C.3.3 Row Level Security Policies

```sql
-- Enable RLS on all tables
ALTER TABLE student_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Students can only access their own data
CREATE POLICY "Users own mastery" ON student_mastery
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users own interactions" ON interactions
    FOR ALL USING (auth.uid() = student_id);

CREATE POLICY "Users own folders" ON folders
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users own chats" ON chats
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users own messages" ON messages
    FOR ALL USING (
        EXISTS (SELECT 1 FROM chats 
                WHERE chats.id = messages.chat_id 
                AND chats.user_id = auth.uid())
    );

-- Admins can view all (for analytics)
CREATE POLICY "Admins view all mastery" ON student_mastery
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM auth.users
                WHERE id = auth.uid()
                AND email LIKE '%@centennialcollege.ca')
    );
```

---

*This appendix provides the complete system design documentation. Additional technical diagrams and API documentation are available in the project repository.*
