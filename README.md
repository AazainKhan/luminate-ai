# Luminate AI Course Marshal

<div align="center">

![Luminate AI](https://img.shields.io/badge/Luminate-AI-6366f1?style=for-the-badge)
![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)

**Agentic AI Tutoring Platform for Centennial College COMP 237**

[Quick Start](#-quick-start) • [Architecture](#-architecture) • [For AI Agents](#-for-ai-agents) • [Documentation](#-documentation)

</div>

---

## 🎯 What is This?

Luminate AI is an intelligent tutoring system delivered as a Chrome Extension. It uses a **Governor-Agent pattern** with LangGraph to:

- ✅ Provide Socratic, scaffolded tutoring for AI concepts
- ✅ Enforce academic integrity (no full solutions to assignments)
- ✅ Auto-detect student intent and route to specialized agents
- ✅ Track student mastery and adapt teaching approach

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Node.js | 18+ | `node --version` |
| Python | 3.11+ | `python --version` |
| Docker | Latest | `docker --version` |
| pnpm | 8+ | `pnpm --version` |
| Chrome | Latest | - |

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/AazainKhan/luminate-ai.git
cd luminate-ai

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Extension
cd ../extension
pnpm install
```

### 2. Environment Setup

Create environment files:

**`backend/.env`**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
GOOGLE_API_KEY=your-gemini-key
ANTHROPIC_API_KEY=your-claude-key
E2B_API_KEY=your-e2b-key
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
```

**`extension/.env.local`**
```env
PLASMO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
PLASMO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
PLASMO_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Services

```bash
# Terminal 1: Docker services (ChromaDB, Redis, Langfuse)
docker-compose up -d

# Terminal 2: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload

# Terminal 3: Extension (dev mode with HMR)
cd extension
pnpm dev
```

### 4. Load Extension

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select `extension/build/chrome-mv3-dev/`
5. Click the Luminate icon → Open Side Panel

---

## 🏗️ Architecture

### Agent Pipeline (LangGraph)

```
                           USER QUERY
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    🛡️ GOVERNOR NODE                          │
│  Enforces 3 Laws:                                            │
│  • Law 1: Scope (COMP 237 topics only)                      │
│  • Law 2: Integrity (no full solutions)                     │
│  • Law 3: Mastery (verify understanding)                    │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    🎯 SUPERVISOR NODE                         │
│  Auto-routes to specialized agents:                          │
│                                                              │
│  ┌────────┬────────┬────────┬──────────┬────────┐           │
│  │ tutor  │  math  │ coder  │ syllabus │  fast  │           │
│  └───┬────┴───┬────┴───┬────┴────┬─────┴───┬────┘           │
└──────┼────────┼────────┼─────────┼─────────┼─────────────────┘
       ▼        ▼        ▼         ▼         ▼
┌──────────┐ ┌──────┐ ┌───────┐ ┌───────┐ ┌───────┐
│PEDAGOGICAL│ │ MATH │ │ CODE  │ │  RAG  │ │GEMINI │
│  TUTOR   │ │AGENT │ │ AGENT │ │SEARCH │ │ FLASH │
│          │ │      │ │       │ │       │ │       │
│ Socratic │ │LaTeX │ │Claude │ │ChromaDB│ │ Quick │
│Scaffolding││Derive│ │Sonnet │ │       │ │Answer │
└────┬─────┘ └──┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
     └──────────┴─────────┴─────────┴─────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    ✅ EVALUATOR NODE                          │
│  • Tracks student mastery                                    │
│  • May loop back for follow-up questions                     │
│  • Logs intent, agent_used, scaffolding_level                │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
                   RESPONSE TO USER
```

### Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Plasmo, React 18, TypeScript, Tailwind CSS, Shadcn UI |
| **Backend** | FastAPI, LangGraph, LangChain, Pydantic V2 |
| **AI Models** | Gemini 1.5 Pro/Flash, Claude 3.5 Sonnet |
| **Vector DB** | ChromaDB with Gemini Embeddings |
| **Database** | Supabase (PostgreSQL + Auth + RLS) |
| **Infra** | Docker, GitHub Actions, E2B (code sandbox) |

### 🧭 Frontend → Backend Request Flow

1) **Student sends a prompt in the Chrome side panel**  
   - UI: `extension/src/sidepanel.tsx` uses the `use-chat` hook.  
   - Auth: Supabase session token is attached to the request headers.

2) **Side panel streams to the backend**  
   - Endpoint: `POST /api/chat/stream` (FastAPI).  
   - Payload: prior messages + new user message, optional `chat_id` and `session_id`.  
   - Transport: Server-Sent Events (AI SDK v5 format) keep the connection open for streaming.

3) **Backend initializes chat + history**  
   - Creates or reuses a `chat_id` and saves the user message.  
   - Fetches recent history for conversational context.

4) **LangGraph agent pipeline runs**  
   - Planner node: scope/integrity checks → intent classification + scaffolding level.  
   - Router: sends to Tutor (default) or Math; Reject if policy fails.  
   - Tutor/Math nodes: RAG via ChromaDB → scaffolded response generation.  
   - Evaluator node: concept detection + mastery logging; emits evaluation events.

5) **Streaming events flow back to the browser**  
   - Events: `thinking` (decision trace), `sources`/`citations` (RAG hits), `reasoning-delta`, `text-delta`, and final `finish` with `chatId`/`traceId`.  
   - The `use-chat` hook assembles these chunks into the visible answer, inline citations, and thinking trace UI.

6) **Persistence & observability**  
   - Messages + metadata (sources, thinking steps, evaluation) are stored for history retrieval.  
   - Langfuse traces capture spans for each node; Supabase stores chat content; ChromaDB backs RAG retrieval.

### Project Structure

```
luminate-ai/
├── backend/                    # FastAPI + LangGraph
│   ├── app/
│   │   ├── agents/            # LangGraph nodes & state
│   │   │   ├── tutor_agent.py      # Main entry point
│   │   │   ├── governor.py         # Policy enforcement
│   │   │   ├── supervisor.py       # Intent routing
│   │   │   ├── pedagogical_tutor.py # Socratic scaffolding
│   │   │   ├── math_agent.py       # Math derivations
│   │   │   └── state.py            # AgentState TypedDict
│   │   ├── api/routes/        # FastAPI endpoints
│   │   ├── etl/               # Blackboard ETL pipeline
│   │   ├── rag/               # ChromaDB client
│   │   └── tools/             # E2B code execution
│   └── main.py
│
├── extension/                  # Plasmo Chrome Extension
│   ├── src/
│   │   ├── sidepanel.tsx      # Student chat UI
│   │   ├── admin-sidepanel.tsx # Faculty dashboard
│   │   ├── components/        # React components
│   │   └── hooks/             # useAuth, useChat
│   └── test/e2e/              # WebdriverIO E2E tests
│
├── docs/                       # Documentation
│   ├── agent-chain/           # 🤖 AI Agent continuity
│   │   ├── CURRENT_STATUS.md  # READ FIRST
│   │   ├── COMPLETED_WORK.md  # History log
│   │   ├── DECISION_LOG.md    # ADRs
│   │   └── KNOWN_ISSUES.md    # Bugs & debt
│   ├── for-next-agent/        # Detailed handover
│   └── migrations/            # SQL migrations
│
├── features/                   # Feature specs (01-11)
├── .github/workflows/          # CI/CD
└── docker-compose.yml
```

---

## 🤖 For AI Agents

> **This project uses an agent chain system for continuous AI collaboration.**

### First Steps (EVERY Session)

```bash
# 1. Pull latest and read status
git pull origin main
cat docs/agent-chain/CURRENT_STATUS.md

# 2. Check recent changes
git log --oneline -10

# 3. Run health check
cd backend && source venv/bin/activate
python -c "from app.agents.tutor_agent import run_agent; print('✅ Agent OK')"
```

### Before Ending Session

```bash
# 1. Commit your changes
git add -A
git commit -m "<type>(<scope>): <description>"

# 2. Update docs/agent-chain/CURRENT_STATUS.md

# 3. Push
git push origin main
```

### Documentation Map

| What You Need | Where to Look |
|---------------|---------------|
| **Live Status** | `docs/agent-chain/CURRENT_STATUS.md` |
| **Full Context** | `docs/for-next-agent/HANDOVER.md` |
| **Architecture Decisions** | `docs/agent-chain/DECISION_LOG.md` |
| **Known Bugs** | `docs/agent-chain/KNOWN_ISSUES.md` |
| **Coding Guidelines** | `.github/copilot-instructions.md` |

---

## 🔐 Authentication

| Role | Email Domain | Access |
|------|--------------|--------|
| **Student** | `@my.centennialcollege.ca` | Chat, study tools |
| **Admin** | `@centennialcollege.ca` | Chat + file upload + analytics |

Uses Supabase passwordless OTP authentication.

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Test intent routing
python -c "from app.agents.supervisor import Supervisor; s = Supervisor(); print(s.route_intent('Explain gradient descent'))"

# Test full agent
python -c "from app.agents.tutor_agent import run_agent; print(run_agent('What is backpropagation?'))"
```

### E2E Tests

```bash
cd extension
pnpm build
pnpm test:e2e
```

---

## 🎯 Features

- ✅ Student chat interface with streaming responses
- ✅ Admin dashboard for course management
- ✅ LangGraph agentic AI with model routing
- ✅ RAG with ChromaDB vector store
- ✅ E2B code execution sandbox
- ✅ Student mastery tracking
- ✅ Generative UI (quizzes, code blocks, visualizations)
- ✅ Blackboard ETL pipeline

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [SETUP.md](./SETUP.md) | Detailed setup & troubleshooting |
| [PROJECT_STATUS.md](./PROJECT_STATUS.md) | Implementation status |
| [PRD.md](./docs/PRD.md) | Product Requirements |
| [HANDOVER.md](./docs/for-next-agent/HANDOVER.md) | Agent handover notes |
| [Database Schema](./docs/database_schema.sql) | Supabase tables |
| [Feature Specs](./features/) | Numbered feature docs |

---

## 🔒 Security

- ✅ Environment files are gitignored - never commit API keys
- ✅ Row Level Security (RLS) on all Supabase tables
- ✅ JWT validation on all API endpoints
- ✅ Role-based access control (student/admin)
- ✅ E2B sandboxed code execution

---

## 📄 License

Proprietary - Centennial College Internal Use

---

<div align="center">

**Built with ❤️ for COMP 237 students**

</div>
