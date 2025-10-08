# 1-line summary...
Exported on 04/10/2025 at 16:45:22 [from ChatGPT](https://chatgpt.com/g/g-p-68e179fc70b881919d2631e4ce4b8799-luminate-ai/c/68e17ca5-d46c-8326-b813-eb90f31f8a35) - with [SaveMyChatbot](https://save.hugocollin.com)

## User
I am building a Chrome extension which populates on the Blackboard LMS. We call it Luminate AI. And what it basically does is it populates a chat interface onto a specific course, which is COMP237. It will populate a chat AI button at the bottom right of the page. I will give you the URL of the Luminate AI course page it needs to inject into. I also have the exported entire course folder which has all the course modules and files. I need to first go through the raw data and make it into digestible files which can be used by the model. The purpose of this ChatAI is a tutor bot. It is an intelligent agent which employs all the best practices and research available about tutoring agents. Everything will run locally, so the backend runs locally, and we will also develop the frontend, which is the Chrome extension, to communicate with the backend locally. The chat window is going to be built using Shadc and UI, using their components, Tailwind CSS, JavaScript, actually even better, TypeScript. And the backend can be a hybrid of Node.js and Python FastAPI. The data is going to get used by this agent, and we will use LandGraph. I don't have much knowledge about LandGraph, so I need diagrams and a proper plan to understand how it's going to communicate exactly. I also want the interface to have two modes, one called Educate and one called Navigate. The Navigate feature, although this is data from exported content, there are taggings which match the URL in some shape or form. So when the user clicks on Navigate mode and searches for some content, it should be able to search the database of the local files, and also produce the links on the Luminate page, which are live links to live content. But because the exported data and the course content is the same, all it needs to do is match the local data with online results from the course shell. So this is important to be part of the plan. We will use ChromaDB, and we will start with Olama local models. I don't really know which model would be the best, but I want it to be open source for now. Do research and check various Tutor AI agents' research papers so we can best formulate the plan. The use cases are students of COM 237 installing the Chrome extension so it can better interact with the Blackboard LMS and aid their studies. The Educate mode is an intelligent agent as well. So it will have all the techniques and all agents which will utilize course content and external sources which are set by the admin. But for the first MVP, we will skip on the admin panel and also the authentication. I just want the navigate feature to work properly first. The student should be able to search for something and get intelligent results which the student can click and open. The navigate mode is made to navigate the course. The Educate mode is made to better help the students learn. There will be a Postgres database to store the student information and their chat session histories which will also be used in Educate mode's context awareness of the student's understanding. Any questions?

## ChatGPT
Understood. Below is a compact, actionable plan, architecture, data pipeline, research-backed tutoring features, technology recommendations, and next steps to get Navigate working as your first MVP.

1-line summary
==============

Build a Chrome extension UI (TypeScript + shadcn/ui + Tailwind) that talks to a local hybrid backend (Node.js + Python FastAPI) which ingests the exported COMP237 course, indexes it into ChromaDB (embeddings) plus a small LangGraph knowledge graph, and serves two modes: Navigate (fast linkable RAG → live course URLs) and Educate (tutor strategies + student context from Postgres). Use Ollama to run local open-source LLMs.

Key citations (most load-bearing facts)
---------------------------------------

*   Intelligent tutoring systems (ITS) generally improve learning outcomes; recent systematic reviews show positive but mixed effects and stress adaptive feedback and scaffolding. [PMC+1](https://pmc.ncbi.nlm.nih.gov/articles/PMC12078640/?utm_source=chatgpt.com)
    
*   LangGraph (part of LangChain ecosystem) is suitable for combining agent workflows with knowledge-graph tooling. [langchain.com+1](https://www.langchain.com/langgraph?utm_source=chatgpt.com)
    
*   ChromaDB is a practical local vector DB for embeddings and retrieval. [Chroma Docs](https://docs.trychroma.com/getting-started?utm_source=chatgpt.com)
    
*   Ollama is a mature tool for running local open models (ML models like Llama family, Mistral, etc.). Good for a local-first stack. [Ollama+1](https://ollama.com/?utm_source=chatgpt.com)
    

* * *

Architecture (concise)
======================

Components:

1.  Chrome extension (TypeScript, React). UI: shadcn/ui components + Tailwind. Injects a small floating chat button into COMP237 pages.
    
2.  Local Backend Gateway (Node.js + Express) — handles CORS, extension auth (MVP: none), static file serving for UI dev, and proxies to Python services.
    
3.  Python FastAPI services:
    
    *   Ingest service (file parsing, metadata extraction, chunking, embeddings).
        
    *   Retrieval / RAG API (query → Chroma → rerank → LLM prompt → response).
        
    *   LangGraph adapter (build/serve knowledge graph edges for Navigate).
        
4.  Vector store: ChromaDB running locally (embedding index + metadata). [Chroma Docs](https://docs.trychroma.com/getting-started?utm_source=chatgpt.com)
    
5.  Local LLM runtime: Ollama hosting chosen open models for generation and local embeddings if desired. [Ollama+1](https://ollama.com/?utm_source=chatgpt.com)
    
6.  Relational DB: Postgres (student profiles, session history, transcripts).
    
7.  Optional small graph DB (Neo4j) or an in-memory graph (LangGraph abstraction) to hold pages, topics, and URL mappings. Use LangGraph to orchestrate agents and graph queries. [langchain.com+1](https://www.langchain.com/langgraph?utm_source=chatgpt.com)
    

Dataflow (Navigate):  
Extension → HTTP POST `/query/navigate` → Backend Retrieval → Chroma similarity search + LangGraph match on tags → return top passages + original course shell URLs (live links) → extension renders list; clicking opens LMS URL in new tab.

Dataflow (Educate):  
Extension → `/chat/educate` → backend loads student context from Postgres → retrieval over Chroma + graph → constructs pedagogical prompt (scaffolding, hints, multiple-step solver) → local LLM via Ollama → response and update session in Postgres.

* * *

Ingest pipeline (detailed steps you can implement now)
======================================================

1.  **Normalize files**
    
    *   Walk course folder. For each file type: HTML, PDF, PPTX, DOCX, Markdown, TXT, CSV, images (OCR needed), Blackboard-export XML.
        
    *   Extract text with tools:
        
        *   PDF: `pdfminer` or `pypdf` + fallback OCR (Tesseract) for scanned pages.
            
        *   PPTX/DOCX: `python-pptx`, `python-docx`.
            
        *   HTML: sanitize and extract visible text (remove nav chrome).
            
        *   Blackboard export XML: parse anchor tags and stored URLs to get original LMS link metadata.
            
2.  **Metadata enrich** (critical)
    
    *   For each document chunk store: `course_id`, `module_id`, `file_name`, `original_file_path`, `original_lms_url` (if present), `tags` (if export has them), `content_type`, `created_at`.
        
    *   If original LMS URL is not in export, create URL mapping rules based on known pattern of COMP237 course shell (user will supply shell URL).
        
3.  **Chunking**
    
    *   Text chunks: 500–800 tokens (approx 3500–6000 characters) with 50% overlap. Store chunk-level start/end offsets and heading context.
        
4.  **Embeddings**
    
    *   Use a local embedding model. Options: sentence-transformers `all-MiniLM-L6-v2` or use Ollama-supported embedding models. Compute vectors and upsert to Chroma with metadata. [Chroma Docs+1](https://docs.trychroma.com/getting-started?utm_source=chatgpt.com)
        
5.  **Graph extraction** (LangGraph)
    
    *   From TOC/headings, create nodes: `Topic`, `Page`, `File`. Create edges: `CONTAINS`, `RELATED_TO`, `NEXT_IN_MODULE`. Store mapping to `original_lms_url`. This enables Navigate mode to return clickable pages.
        
6.  **Quality checks**
    
    *   Dedup similar chunks (vector cosine threshold 0.95) and dedupe identical file names. Keep canonical file -> live URL mapping.
        

* * *

Navigate mode: exact behavior
=============================

User types search -> backend:

1.  **Semantic search**: Chroma nearest neighbors on query embedding (top 20).
    
2.  **Filter/Boost**: If query contains URL-like tag or Blackboard-specific tag, add metadata filter.
    
3.  **Graph join**: For each top chunk, find `Page` node and return `original_lms_url` from graph. If a chunk has no URL, return module parent URL.
    
4.  **Return**: JSON payload `{title, excerpt, score, live_url, module, file_path}`. Extension shows list with direct open-in-LMS links.
    

Important: Use exact URL mapping so users open _live_ course shell pages. Build mapping heuristics from export structure if export lacks direct URLs.

* * *

Educate mode: evidence-based tutoring features
==============================================

Incorporate these strategies shown effective in ITS literature: personalized feedback, stepwise hints, worked examples, scaffolding, retrieval practice, and mastery checks. Implementable features:

*   **Diagnostic probe** at session start (short questions) to set level.
    
*   **Adaptive hinting**: 3-tier hints (light → medium → worked example).
    
*   **Socratic questioning** for conceptual gaps.
    
*   **Progressive problem decomposition** for coding tasks (auto-solve in steps).
    
*   **Spacing & retrieval prompts** from session history to force recall.
    
*   **Explainability**: always provide source links (chunks + LMS URL) used to create answer.
    

Sources: ITS systematic reviews and recent agent frameworks stress scaffolding, adaptive feedback, and human-in-the-loop checks. [PMC+1](https://pmc.ncbi.nlm.nih.gov/articles/PMC12078640/?utm_source=chatgpt.com)

* * *

Model & infra recommendations (practical)
=========================================

*   **Local LLM runner**: Ollama for running open models locally. Use a moderate-sized model for MVP (e.g., Llama 3 8B or Mistral 7B) depending on host GPU/RAM. Ollama simplifies model management. [Ollama+1](https://ollama.com/?utm_source=chatgpt.com)
    
*   **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` for fast indexing. Upgrade later to `instructor` style models if you need instruction-following embedding.
    
*   **Vector DB**: ChromaDB (local). [Chroma Docs](https://docs.trychroma.com/getting-started?utm_source=chatgpt.com)
    
*   **Graph**: Use LangGraph orchestration and either in-memory graph or Neo4j for heavy graph queries. LangGraph integrates with LangChain patterns. [langchain.com+1](https://www.langchain.com/langgraph?utm_source=chatgpt.com)
    
*   **Backend**: FastAPI (Python) for ingestion + retrieval; Node.js for extension-facing gateway. Keep simple HTTP JSON APIs.
    

* * *

Minimal API spec (MVP)
======================

*   `POST /ingest/start` — upload/export zip path → starts ingestion job.
    
*   `GET /ingest/status` — job status.
    
*   `POST /query/navigate` {q, size, filters} → returns `[{title, excerpt, score, live_url}]`.
    
*   `POST /chat/educate` {student\_id, message, session\_id} → returns chat response and sources.
    
*   `GET /student/{id}/history` — session transcripts.
    

* * *

Postgres schema (small)
=======================

`students(id, name, email)`  
`sessions(id, student_id, started_at)`  
`messages(id, session_id, role, text, created_at, sources JSONB)`  
`student_profiles(id, student_id, mastery_json)` — store simple skill map.

* * *

Implementation roadmap (practical milestones)
=============================================

1.  **Mapping + proof-of-concept** (2 days): write parsing script to extract text + metadata from a few representative files. Create sample Chroma collection and insert a handful of chunks mapped to LMS URLs.
    
2.  **Local query API (Navigate)** (2–3 days): implement `/query/navigate` retrieving from Chroma and returning live URLs. Build Chrome extension floating button UI that sends queries and lists results.
    
3.  **Graph overlay** (2 days): build simple LangGraph/Neo4j mapping for module/page relations and use it to enrich Navigate results.
    
4.  **Educate MVP** (4–7 days): add FastAPI chat endpoint, integrate with Ollama model, add Postgres session storage, implement simple scaffolding/hinting.
    
5.  **Polish & security** (ongoing): URL mapping robustness, dedupe, rate limiting, local auth if needed.
    

* * *

Immediate next steps I can deliver for you now (pick items)
===========================================================

1.  A runnable Python script that ingests a zipped course folder and outputs chunk+metadata JSON ready for Chroma.
    
2.  A minimal FastAPI `/query/navigate` implementation that queries a local Chroma collection and returns LMS links.
    
3.  A minimal Chrome extension scaffold (TS + React + shadcn/ui) that injects the floating button and calls `/query/navigate`.
    

Tell me which one to produce first and provide the course exported folder zip or the course shell URL for URL-mapping rules. I will generate the code and examples in this session.undefined

## User
what are the use cases and features

## ChatGPT
Use cases and features are below, grouped by mode and purpose.

* * *

1\. Core use cases
------------------

### For students (COMP237)

*   **Navigate mode**: quickly locate readings, lectures, and assignments inside Blackboard without manually browsing modules.
    
*   **Educate mode**: get on-demand tutoring and clarification of course concepts using the same course materials.
    
*   **Revision aid**: summarize modules, quiz self, or review difficult topics with context-aware prompts.
    
*   **Contextual links**: open the correct live Blackboard page from local search results.
    
*   **Offline study**: use exported data locally when Blackboard is unavailable.
    

### For instructors (later phase)

*   Analyze which topics cause frequent confusion.
    
*   Upload or update course data easily for the agent to re-index.
    
*   Monitor student progress (via Postgres session analytics).
    

* * *

2\. System-level use cases
--------------------------

*   **Chrome extension injection**: attach an AI chat icon onto COMP237 course pages.
    
*   **Local backend orchestration**: run all components locally for privacy and performance.
    
*   **Hybrid RAG search**: semantic retrieval from course files + direct URL linking to Blackboard.
    
*   **LangGraph integration**: maintain knowledge graph of modules, topics, and dependencies.
    
*   **Session memory**: persist chat histories for personalized tutoring.
    
*   **Adaptive feedback**: use stored performance to tailor future responses.
    

* * *

3\. Navigate mode features
--------------------------

| Category | Feature |
| --- | --- |
| Search | Semantic + keyword search over local course data (ChromaDB). |
| Results | Return short excerpts and direct “Open in Blackboard” links. |
| Filtering | Restrict by module, week, file type, or tags. |
| Highlighting | Show context snippet around the match. |
| Offline index | Works from exported course content even without internet. |
| URL sync | Map local files to live Blackboard URLs for one-click navigation. |

* * *

4\. Educate mode features
-------------------------

| Category | Feature |
| --- | --- |
| Context-aware tutoring | Use previous chats + session data for continuity. |
| Scaffolded hints | Multi-tier hinting and guided problem solving. |
| Worked examples | Generate step-by-step demonstrations from course content. |
| Concept linking | Traverse LangGraph to suggest prerequisite or related topics. |
| Adaptive questioning | Pose diagnostic or review questions based on gaps. |
| Citations | Always display source chunks and module links. |
| Quiz generation | Form short quizzes from content for retrieval practice. |
| Session summary | Provide end-of-session recap and suggested readings. |

* * *

5\. Supporting features (system)
--------------------------------

*   **Local LLM execution** via Ollama (privacy-preserving).
    
*   **Vector store** with ChromaDB for retrieval.
    
*   **Postgres** for session and profile storage.
    
*   **LangGraph orchestration** for module-topic relationships.
    
*   **FastAPI + Node gateway** for clear separation of data and UI.
    
*   **TypeScript + shadcn/ui + Tailwind** for modern interface.
    
*   **Offline first** design: no external API dependency.
    

* * *

These define the MVP boundary:

1.  Working Navigate mode (semantic search + live URL mapping).
    
2.  Basic Educate mode (chat with course-based answers).
    

Later additions can include instructor dashboards, user authentication, analytics, and external source integration.

## User
okay what are the steps

## ChatGPT
Sequential build plan with clear milestones.

* * *

Phase 1 — Setup and architecture (1–2 days)
-------------------------------------------

1.  Define local dev environment (Node.js, Python, Postgres, ChromaDB, Ollama).
    
2.  Create shared `.env` and folder structure:
    
    ```bash
    /extension
    /backend
      /node_gateway
      /fastapi_service
    /data
    /db
    ```
3.  Install dependencies:
    
    *   **Extension**: React, TypeScript, Tailwind, shadcn/ui, Vite.
        
    *   **Backend**: FastAPI, ChromaDB, langchain, langgraph, psycopg2, sentence-transformers.
        
    *   **Gateway**: Express + Axios proxy.
        

* * *

Phase 2 — Data ingestion (2–3 days)
-----------------------------------

1.  Parse exported Blackboard folder.
    
2.  Extract raw text and metadata (title, tags, file path, LMS URL).
    
3.  Chunk text (500–800 tokens).
    
4.  Generate embeddings and insert into ChromaDB.
    
5.  Build URL mapping table linking local files to Blackboard URLs.
    
6.  Output sample JSON to verify indexing integrity.
    

* * *

Phase 3 — Backend APIs (3–4 days)
---------------------------------

1.  **FastAPI endpoints**
    
    *   `/ingest/start` — load files.
        
    *   `/query/navigate` — semantic + metadata search, return JSON `{title, excerpt, url}`.
        
    *   `/chat/educate` — call Ollama model with retrieved context.
        
2.  Integrate ChromaDB queries with LangGraph (for module relationships).
    
3.  Test API responses with Postman.
    
4.  Create local Postgres schema (`students`, `sessions`, `messages`).
    

* * *

Phase 4 — Chrome extension frontend (3–4 days)
----------------------------------------------

1.  Scaffold extension manifest v3.
    
2.  Inject floating chat button on COMP237 URLs only.
    
3.  Build chat panel using shadcn/ui + Tailwind.
    
4.  Add mode toggle: **Navigate / Educate**.
    
5.  Connect to backend:
    
    *   Navigate: send `/query/navigate` request and render list of results.
        
    *   Educate: send `/chat/educate` and render chat history.
        

* * *

Phase 5 — Integration & testing (2–3 days)
------------------------------------------

1.  Run local backend + extension simultaneously.
    
2.  Validate CORS and local proxying.
    
3.  Verify Navigate mode:
    
    *   Search for topic.
        
    *   Display excerpts.
        
    *   Click opens live Blackboard link.
        
4.  Verify Educate mode:
    
    *   Ask conceptual question.
        
    *   LLM responds with course-based answer + source.
        

* * *

Phase 6 — Optimization (ongoing)
--------------------------------

1.  Improve embeddings with better models.
    
2.  Add caching of results.
    
3.  Implement context persistence per student.
    
4.  Add simple admin CLI for re-indexing.
    
5.  Add logging + analytics.
    

* * *

Phase 7 — Optional future work
------------------------------

*   Authentication and user roles.
    
*   Instructor analytics dashboard.
    
*   Multi-course support.
    
*   Cloud deployment option if desired later.
    

* * *

You can start Phase 1 now. Do you want me to generate the exact folder skeleton and dependency setup scripts next?

## User
because the exported data being used is static, will it have to be inputted into the vector db everytime or just once

## ChatGPT
Only once.

Explanation:

*   The exported course data is static and does not change unless you update or re-export the course.
    
*   You run the **ingestion + embedding** process once to build the ChromaDB index.
    
*   The resulting Chroma collection (typically stored as local files in a directory like `./chroma/`) persists on disk.
    
*   At runtime, the backend just loads the existing Chroma collection and serves queries; no re-embedding occurs.
    

You only repeat ingestion when:

1.  Course content changes.
    
2.  You switch embedding model (vectors must be regenerated).
    
3.  You alter chunking or metadata schema.
    

Otherwise, it’s a one-time cost.

## User
how does langgraph work here? what are all the agents and their roles and everything in between

## ChatGPT
LangGraph in your system organizes reasoning and data traversal among specialized agents. It builds a **directed workflow graph** of small, single-purpose nodes that collaborate to answer a query.

Below is the structure and role of each part in your Luminate AI architecture.

* * *

1\. Concept
-----------

LangGraph = a graph-based orchestration layer on top of LangChain.  
It defines **nodes** (agents or functions) and **edges** (data flow between them).  
Each node executes logic: retrieval, reasoning, query reformulation, ranking, or response generation.

For you, LangGraph is not the database; it coordinates agents and uses metadata from Chroma and Postgres.

* * *

2\. Graph overview for Luminate AI
----------------------------------

```css
[User Query]
     │
     ▼
 ┌─────────────┐
 │ Input Router│  ← decides Educate / Navigate
 └─────────────┘
     │
 ┌─────────────┬──────────────┐
 │             │              │
 ▼             ▼              ▼
 NavigateGraph EducateGraph   AdminGraph (future)
```

Each subgraph has internal nodes (agents) with clear roles.

* * *

3\. NavigateGraph
-----------------

Purpose: find the correct Blackboard resource for a query.

**Agents / nodes:**

1.  **Query Preprocessor**
    
    *   Normalize query (lowercase, strip stopwords).
        
    *   Detect possible Blackboard tags or module keywords.
        
2.  **Embedding Search Agent**
    
    *   Embed query → search ChromaDB for top chunks.
        
    *   Outputs ranked results with metadata (file path, module, url).
        
3.  **Graph Join Agent**
    
    *   Receives chunk metadata.
        
    *   Queries the LangGraph knowledge base of module relationships.
        
    *   Attaches `parent_module`, `topic`, and `live_url`.
        
4.  **Rerank Agent**
    
    *   Optional re-ranking based on URL confidence and relevance.
        
5.  **Response Formatter Agent**
    
    *   Produces structured JSON: title, snippet, live link.
        

Data flow:  
`Query → Preprocess → Chroma → Graph Join → Rerank → Format → Output`

* * *

4\. EducateGraph
----------------

Purpose: act as an intelligent tutor using course content and student history.

**Agents / nodes:**

1.  **Context Collector**
    
    *   Pulls last N messages and profile from Postgres.
        
    *   Determines skill level and learning history.
        
2.  **Retriever Agent**
    
    *   Embeds question → searches Chroma for relevant chunks.
        
3.  **Pedagogical Planner**
    
    *   Chooses teaching strategy: direct explanation, hint chain, quiz, worked example.
        
    *   Uses simple rules now; can later be replaced by policy model.
        
4.  **Response Composer (LLM Agent)**
    
    *   Assembles prompt with course chunks, context, and chosen pedagogy.
        
    *   Calls local LLM via Ollama.
        
    *   Returns text + cited sources.
        
5.  **Feedback Logger**
    
    *   Writes session turn into Postgres.
        
    *   Updates student profile (e.g., topic mastery increment).
        

Data flow:  
`User Question → Context Collector → Retriever → Pedagogical Planner → LLM → Feedback Logger → Output`

* * *

5\. Shared components (used by both graphs)
-------------------------------------------

*   **Knowledge Graph DB (LangGraph memory)**  
    Nodes: `Module`, `Topic`, `File`, `URL`.  
    Edges: `CONTAINS`, `RELATES_TO`, `NEXT`.  
    Each edge has metadata so Navigate mode can map chunks to live URLs or related topics.
    
*   **Vector DB (Chroma)**  
    Provides semantic retrieval to feed Graph nodes.
    
*   **Local LLM via Ollama**  
    Handles generation tasks (explanations, paraphrasing, etc.).
    
*   **Postgres**  
    Stores sessions and user profiles for Educate mode context.
    

* * *

6\. Runtime coordination
------------------------

1.  FastAPI calls LangGraph engine with `mode` and `query`.
    
2.  LangGraph selects the subgraph and executes nodes sequentially or conditionally.
    
3.  Each node returns structured data; errors short-circuit with fallbacks.
    
4.  The engine aggregates final output and sends JSON back to the extension.
    

* * *

7\. Example: Navigate query flow
--------------------------------

**Input:** “week 4 lab instructions”

*   Preprocessor detects “week 4”.
    
*   Embedding search retrieves chunks tagged `Week_4_Lab`.
    
*   Graph Join links to Module → `Lab Assignments`.
    
*   Output JSON:
    
    ```arduino
    [
      {title: "Week 4 Lab", snippet: "Instructions on ...", live_url: "..."},
      ...
    ]
    ```

* * *

8\. Example: Educate query flow
-------------------------------

**Input:** “Can you explain TCP three-way handshake?”

*   Context Collector pulls student level: networking basics known.
    
*   Retriever gets COMP237 lecture slides chunks.
    
*   Pedagogical Planner selects “worked example + question”.
    
*   LLM composes answer citing lecture material.
    
*   Feedback Logger stores that “TCP handshake” is now covered.
    

* * *

9\. Summary of agent roles
--------------------------

| Agent | Graph | Function |
| --- | --- | --- |
| Query Preprocessor | Navigate | Normalize and tag query |
| Embedding Search | Navigate / Educate | Chroma semantic search |
| Graph Join | Navigate | Map chunks to LMS URLs |
| Rerank | Navigate | Improve result ordering |
| Response Formatter | Navigate | Return structured JSON |
| Context Collector | Educate | Load session + student data |
| Pedagogical Planner | Educate | Choose teaching strategy |
| Response Composer | Educate | Generate response via LLM |
| Feedback Logger | Educate | Store chat + update profile |

* * *

This structure keeps computation modular, interpretable, and easily extensible.  
Would you like a system diagram (graph-style visual) showing this full LangGraph layout next?

