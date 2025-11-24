# Luminate AI Course Marshal

Agentic AI tutoring platform for Centennial College COMP 237 course, delivered as a Chrome Extension.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker and Docker Compose
- Chrome browser

### Setup Steps

1. **Install Dependencies**

   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Extension
   cd ../extension
   npm install
   ```

2. **Environment Variables**

   Environment files are already configured:
   - `backend/.env` - Backend configuration (Supabase, API keys)
   - `extension/.env.local` - Extension configuration (Supabase, API URL)

3. **Start Docker Services**

   ```bash
   docker-compose up -d
   ```

   This starts:
   - FastAPI backend (http://localhost:8000)
   - ChromaDB (http://localhost:8001)
   - Redis (port 6379)
   - Langfuse (http://localhost:3000)

4. **Start Backend** (if not using Docker)

   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload
   ```

5. **Build Extension**

   ```bash
   cd extension
   npm run dev
   ```

6. **Load Extension in Chrome**

   - Open Chrome → `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `extension` directory

## 📁 Project Structure

```
luminate-ai/
├── extension/          # Plasmo Chrome Extension
│   ├── src/
│   │   ├── sidepanel.tsx          # Student chat interface
│   │   ├── admin-sidepanel.tsx    # Admin dashboard
│   │   ├── components/            # React components
│   │   └── lib/                   # Utilities (Supabase, API)
│   └── package.json
├── backend/            # FastAPI + LangGraph backend
│   ├── app/
│   │   ├── agents/               # LangGraph agent definitions
│   │   ├── api/                  # FastAPI routes
│   │   ├── etl/                  # ETL pipeline
│   │   ├── rag/                  # RAG & vector store
│   │   └── tools/                 # Agent tools (E2B, etc.)
│   ├── main.py
│   └── requirements.txt
├── docs/               # Documentation
├── features/           # Feature documentation (numbered)
├── raw_data/          # COMP 237 course materials
└── docker-compose.yml  # Local development stack
```

## 🔐 Authentication

- **Students**: Email ending with `@my.centennialcollege.ca`
- **Admins**: Email ending with `@centennialcollege.ca`

Uses Supabase passwordless OTP authentication.

## 🎯 Features

- ✅ Student chat interface with streaming responses
- ✅ Admin dashboard for course management
- ✅ LangGraph agentic AI with model routing
- ✅ RAG with ChromaDB vector store
- ✅ E2B code execution sandbox
- ✅ Student mastery tracking
- ✅ Generative UI (quizzes, code blocks, visualizations)
- ✅ Blackboard ETL pipeline

## 🛠️ Tech Stack

- **Frontend**: Plasmo, React, TypeScript, Tailwind CSS, Shadcn UI
- **Backend**: Python 3.11, FastAPI, LangGraph, Pydantic V2
- **AI**: Gemini 1.5 Pro/Flash, Claude 3.5 Sonnet
- **Database**: Supabase (Postgres + Auth), ChromaDB (Vector)
- **Infrastructure**: Docker, Docker Compose

## 📝 Development

See [SETUP.md](./SETUP.md) for detailed development setup and troubleshooting.

## 🔒 Security Notes

- `.env` files are gitignored - never commit API keys
- Row Level Security (RLS) enabled on Supabase tables
- JWT token validation on all backend endpoints
- Role-based access control (student/admin)

## 📚 Documentation

- [PRD](./docs/PRD.md) - Product Requirements Document
- [Setup Guide](./SETUP.md) - Detailed setup instructions
- [Project Status](./PROJECT_STATUS.md) - Current project status and implementation details
- [Feature Docs](./features/) - Numbered feature documentation

## 📄 License

Proprietary - Centennial College Internal Use
