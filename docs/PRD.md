Product Requirements Document (PRD)

Project Name: Luminate AI

Version

Date

Status

Author

1.0

November 22, 2025

Planning

[Your Name/Role]

1. Executive Summary

Course Marshal AI is an agentic tutoring platform designed specifically for Centennial College's COMP 237 (Introduction to AI) course. It bridges the gap between static learning materials (Blackboard exports, PDFs) and active mastery (coding, reasoning) through a "Course Marshal" architecture.

Unlike generic chatbots, this system acts as a Proctor and Tutor: it enforces syllabus constraints, validates student mastery before revealing answers, and executes code in secure sandboxes. It is delivered as a single Chrome Extension (built with Plasmo/React) that serves both Students (via Side Panel) and Admins (via Options Page).

2. User Roles & Authentication

2.1 Student (The Learner)

Access Point: Chrome Extension Side Panel.

Authentication:

Method: Passwordless Email OTP (One-Time Password) via Supabase.

Constraint: Email must end in @my.centennialcollege.ca.

Capabilities:

Chat with the Agentic Tutor.

Receive "Generative UI" artifacts (Quizzes, Interactive Graphs).

View personal progress/mastery scores.

Restrictions: Cannot access the "Admin" or "Upload" features.

2.2 Admin (The Faculty/Professor)

Access Point: Chrome Extension Options Page (Full-screen React view).

Authentication:

Method: Passwordless Email OTP.

Constraint: Email must end in @centennialcollege.ca.

Capabilities:

Upload Blackboard Export Packages (.zip).

Upload Textbook/Supplementary PDFs.

Trigger the Course ETL (Extract, Transform, Load) pipeline.

View system health and ingestion status.

3. Functional Requirements

3.1 The "Brain" (Backend Intelligence)

The system uses a Hierarchical Supervisor architecture implemented in LangGraph.

FR-01: Model Routing (The "Three-Mode" Engine)

Fast Mode (Default): Uses Gemini 1.5 Flash for logistics ("When is the quiz?"), definitions, and summaries. Low latency (<1s).

Coder Mode: Automatically switches to Claude 3.5 Sonnet when code generation or debugging is requested.

Reasoning Mode: Automatically switches to Gemini 1.5 Pro (or o1-preview) for complex mathematical derivations (e.g., Backpropagation calculus).

FR-02: Syllabus Grounding (RAG)

The agent must prioritize retrieved context from ChromaDB over pre-trained knowledge.

If a query is out of scope (not in COMP_237.pdf), the agent must flag it.

FR-03: Code Execution

Generated Python code must run in an E2B Sandbox (cloud microVM), not on the user's machine or backend server.

Outputs (stdout, charts) are returned to the chat stream.

3.2 Student Experience (Frontend - Side Panel)

FR-04: Streaming & Optimistic UI

Utilize Vercel AI SDK (useChat) to stream responses token-by-token.

Display a "Thinking..." accordion component that reveals the Agent's internal steps (e.g., "Searching Syllabus...", "Running Python Code...").

FR-05: Generative UI Artifacts

Quiz Card: Render a structured React component for multiple-choice questions. Visual feedback (Green/Red) on submission.

Code Block: Syntax-highlighted code with a "Run" button (triggers backend execution) and "Copy" button.

Visualizer: Interactive graphs (Mermaid.js or Recharts) generated on-the-fly for algorithms (e.g., DFS/BFS trees).

3.3 Admin Experience (Frontend - Options Page)

FR-06: Course Ingestion Pipeline

File Upload: Drag-and-drop interface for Blackboard ZIPs.

Discovery Script: Backend must parse imsmanifest.xml to map cryptic file IDs (res00001.dat) to human-readable titles (Week1_Lecture.pdf).

Status Tracking: Real-time progress bar for the ETL process (Unzipping $\to$ Parsing $\to$ Chunking $\to$ Vectorizing).

FR-07: Default Content

The system initializes with COMP 237 data pre-loaded. Admin intervention is only needed for updates.

4. Technical Architecture

4.1 Technology Stack

Layer

Technology

Role

Justification

Frontend

Plasmo (React)

Extension Framework

Native Chrome API access, React HMR, Single-repo simplicity.

UI Library

Shadcn/UI

Component System

Accessible, copy-paste components, matches modern "Vercel" aesthetic.

Styling

Tailwind CSS

CSS Framework

Utility-first, scoped styles via Plasmo to prevent website leakage.

State

Vercel AI SDK

AI Integration

Handles streaming state, tool calls, and optimistic updates.

Backend

FastAPI (Python)

API Server

Async support for concurrent agents, native Pydantic integration.

Orchestrator

LangGraph

Agent Logic

Stateful, cyclic graph architecture for complex "Tutor Loops".

Database

Supabase

User/Relational DB

Auth, Row Level Security, Student Mastery tables.

Vector DB

ChromaDB

Knowledge Base

Dockerized local vector store, dedicated to course content.

Sandbox

E2B

Code Execution

Secure, ephemeral cloud environments for Python execution.

Observability

Langfuse/VoltOps

Tracing

Debugging agent thought chains and latency.

4.2 Deployment Architecture

Local Dev: docker-compose runs FastAPI, ChromaDB, Redis, and Langfuse.

Extension: Loaded as "Unpacked Extension" in Chrome Developer Mode.

Production: Backend deployed to Railway or Render. Extension distributed via Itero (Beta) or Chrome Web Store.

5. Data Strategy

5.1 Vector Schema (ChromaDB)

{
  "id": "uuid",
  "embedding": [0.12, ...],
  "document": "The chain rule states...",
  "metadata": {
    "source_filename": "Week9_Backprop.pdf",
    "course_id": "COMP237",
    "content_type": "concept_definition", // vs 'assignment_instruction'
    "week_number": 9
  }
}


5.2 Student Mastery Schema (Supabase)

create table student_mastery (
  user_id uuid references auth.users,
  concept_tag text, -- e.g. 'dfs_algorithm'
  mastery_score float check (mastery_score between 0 and 1),
  last_interaction timestamp default now()
);

6. Development Roadmap (Vibe Coding Plan)
Phase 1: The Skeleton (Infrastructure)
Goal: Working "Hello World" chat between Plasmo and FastAPI.

Tasks:

Initialize Plasmo (React) repo.

Setup docker-compose.yml (FastAPI, Redis, ChromaDB).

Implement Supabase Auth (Magic Link) in sidepanel.tsx.

Verify Docs (@Plasmo, @FastAPI) are indexed in Cursor.

Phase 2: The Brain (ETL & RAG)
Goal: Agent can answer questions about COMP 237.

Tasks:

Build imsmanifest.xml parser in Python.

Create Admin Options Page for Zip upload.

Implement LangGraph "Router" node (Gemini vs. Claude switching).

Ingest COMP 237 sample data.

Phase 3: The Interface (Generative UI)
Goal: Rich, interactive tutoring experience.

Create QuizCard and ThinkingAccordion components (Shadcn).

Connect streamUI from Vercel AI SDK to render components based on Tool Calls.

Integrate E2B Sandbox for the "Run Code" button.

7. Documentation & Compliance
System Prompt (.cursorrules): Must be present in root to enforce tech stack constraints (React-only, Supabase Auth rules).

Context Injection: Developers must reference indexed docs (@Plasmo, @LangGraph) to prevent hallucinated API usage.

MCP Usage: Use shadcn MCP for UI generation and sequential MCP for complex logic planning.

8. Success Metrics
Latency: <2s for "Fast Mode" text responses.

Accuracy: 100% accuracy on Syllabus logistics (Dates, Grading Scheme).

Safety: 0% rate of providing direct solutions to "Graded" assignments (must provide hints instead).