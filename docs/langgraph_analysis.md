# LangGraph Implementation Analysis

**Date:** October 8, 2025  
**Purpose:** Detailed analysis of current LangGraph architecture for migration to LangFlow

---

## 1. Agent Inventory

### Identified Agents (11 Total)

#### Navigate Mode (4 agents)
1. **Query Understanding Agent** (`query_understanding_agent`)
   - **Purpose:** Parse and enhance student queries
   - **Inputs:** `query` (raw user input)
   - **Outputs:** `parsed_query` (enhanced query dict with category, student_goal, expanded_query)
   - **Tools:** LLM-based query analysis

2. **Retrieval Agent** (`retrieval_agent`)
   - **Purpose:** Search ChromaDB for relevant course materials
   - **Inputs:** `query`, `chroma_db`, `parsed_query`
   - **Outputs:** `retrieved_chunks` (list of documents), `retrieval_metadata`
   - **Tools:** ChromaDB vector search

3. **Context Agent** (`context_agent`)
   - **Purpose:** Add graph-based context (prerequisites, related topics)
   - **Inputs:** `retrieved_chunks`, `parsed_query`
   - **Outputs:** `enriched_results` (with course structure context)
   - **Tools:** Knowledge graph logic

4. **Formatting Agent** (`formatting_agent`)
   - **Purpose:** Create UI-ready response with Gemini 2.0
   - **Inputs:** `enriched_results`, `query`
   - **Outputs:** `formatted_response` (final JSON for UI)
   - **Tools:** Gemini 2.0 Flash LLM

#### Educate Mode (7 agents)
5. **Student Model Agent** (`student_model_agent`)
   - **Purpose:** Track student understanding and mastery levels
   - **Inputs:** `query`, `student_id`, `conversation_history`
   - **Outputs:** `student_insights` (mastery levels, misconceptions)
   - **Tools:** Supabase for persistence, LLM for analysis

6. **Math Translation Agent** (`MathTranslationAgent` / `explain_formula`)
   - **Purpose:** Translate mathematical formulas into explanations
   - **Inputs:** `query` (formula text)
   - **Outputs:** `math_markdown` (LaTeX + explanation)
   - **Tools:** Regex pattern matching, formula database

7. **Pedagogical Planner Agent** (`pedagogical_planner_agent`)
   - **Purpose:** Choose teaching strategy (scaffolding, worked example, Socratic)
   - **Inputs:** `parsed_query`, `student_insights`, `retrieved_chunks`
   - **Outputs:** `teaching_strategy`, `interaction_prompts`
   - **Tools:** LLM-based strategy selection

8. **Interactive Formatting Agent** (`interactive_formatting_agent`)
   - **Purpose:** Generate hints, quizzes, worked examples
   - **Inputs:** `teaching_strategy`, `query`, `retrieved_chunks`
   - **Outputs:** `formatted_response` (with interactive elements)
   - **Tools:** Gemini 2.5 Flash LLM

9. **Quiz Generator Agent** (`quiz_generator_agent`)
   - **Purpose:** Create adaptive quizzes
   - **Inputs:** `query`, `student_insights`, `retrieved_chunks`
   - **Outputs:** `quiz_data` (questions, difficulty)
   - **Tools:** LLM-based quiz generation

10. **Study Planner Agent** (`study_planner_agent`)
    - **Purpose:** Create personalized study schedules
    - **Inputs:** `query`, `student_context`, `retrieved_chunks`
    - **Outputs:** `study_plan` (timeline, topics)
    - **Tools:** LLM-based planning + calendar logic

11. **External Resources Agent** (`external_resources_agent`)
    - **Purpose:** Find supplementary learning resources (YouTube, OER)
    - **Inputs:** `query`, `understood_query`
    - **Outputs:** `external_resources` (video/article links)
    - **Tools:** API calls (YouTube Data API, etc.)

---

## 2. State Management

### Navigate Mode State (`NavigateState`)
```python
{
    "query": str,                        # Raw user query
    "chroma_db": Any,                    # ChromaDB instance
    "parsed_query": Dict,                # Enhanced query from understanding agent
    "retrieved_chunks": List[Dict],      # Documents from ChromaDB
    "enriched_results": List[Dict],      # With context added
    "external_resources": List[Dict],    # YouTube/OER links
    "formatted_response": Dict,          # Final UI output
    "retrieval_metadata": Dict,          # Stats (total_results, after_dedup)
    "retrieval_error": str,              # Error messages
    "context_warning": str,              # Warnings
    "is_in_scope": bool,                 # COMP237 scope check
    "trace_callback": Callable           # For logging/tracing
}
```

### Educate Mode State (`EducateState`)
```python
{
    "query": str,                        # Raw user query
    "chroma_db": Any,                    # ChromaDB instance
    "math_markdown": str,                # Formula translation
    "parsed_query": Dict,                # Enhanced query
    "retrieved_chunks": List[Dict],      # Documents
    "enriched_results": List[Dict],      # With context
    "teaching_strategy": str,            # Chosen pedagogy
    "interaction_prompts": Dict,         # Hints/questions
    "student_context": Dict,             # From Supabase
    "student_insights": Dict,            # Mastery levels
    "quiz_data": Dict,                   # Generated quiz
    "study_plan": Dict,                  # Study schedule
    "detected_misconception": str,       # Misconceptions found
    "formatted_response": Dict           # Final UI output
}
```

### Orchestrator State (`OrchestratorState`)
```python
{
    "query": str,
    "student_id": str,
    "session_id": str,
    "conversation_history": List,        # Dialogue turns
    "mode": Literal["navigate", "educate"],
    "confidence": float,                 # Mode selection confidence
    "reasoning": str,                    # Why mode was chosen
    "next_graph": Literal["navigate_graph", "educate_graph"],
    "last_mode": str,                    # Previous mode
    "mode_switch_count": int,            # Session switches
    "conversation_turns": int,           # Total turns
    "is_follow_up": bool,                # Follow-up detection
    "should_confirm": bool,              # Ask user for confirmation
    "student_context": dict              # Supabase student data
}
```

---

## 3. LangGraph Workflow Flows

### Navigate Mode Flow
```
START
  ↓
understand_query (query_understanding_agent)
  ↓
retrieve (retrieval_agent)
  ↓
search_external (external_resources_agent)
  ↓
add_context (context_agent)
  ↓
format_response (formatting_agent)
  ↓
END
```

### Educate Mode Flow
```
START
  ↓
understand_query (query_understanding_agent)
  ↓
student_model (student_model_agent)
  ↓
math_translate (_math_translate_node)
  ↓
pedagogical_plan (pedagogical_planner_agent)
  ↓
generate_visualization (_generate_visualization_node)
  ↓
retrieve (retrieval_agent)
  ↓
[CONDITIONAL ROUTING: _route_after_retrieval]
  ├─→ quiz_generator (quiz_generator_agent) → interactive_format
  ├─→ study_planner (study_planner_agent) → interactive_format
  └─→ add_context (context_agent) → interactive_format
       ↓
interactive_format (interactive_formatting_agent)
  ↓
END
```

---

## 4. Tools & Dependencies

### External Services
1. **ChromaDB**
   - Purpose: Vector database for semantic search
   - Used by: `retrieval_agent`
   - Access: `state['chroma_db']` instance

2. **Supabase**
   - Purpose: Student data persistence (mastery, misconceptions, progress)
   - Used by: `student_model_agent`, `study_planner_agent`
   - Access: Environment variable `SUPABASE_URL`, `SUPABASE_KEY`

3. **Gemini LLMs**
   - **2.0 Flash**: Navigate mode formatting (fast, cheap)
   - **2.5 Flash**: Educate mode (advanced reasoning)
   - Access: `GOOGLE_API_KEY` environment variable

4. **External APIs**
   - YouTube Data API (for video search)
   - OER Commons API (for educational resources)
   - Used by: `external_resources_agent`

### Python Libraries
- `langgraph` (v0.6.8): StateGraph, conditional edges
- `langchain` (v0.3.23): LLM integrations
- `chromadb`: Vector storage
- `supabase-py`: Database client
- `google-generativeai`: Gemini SDK

---

## 5. Key Features to Preserve

### Educational AI Features
1. **Adaptive Tutoring:** Student model tracks mastery → adjusts difficulty
2. **Scaffolding:** Progressive hints (Socratic method)
3. **Misconception Detection:** Identifies conceptual gaps
4. **Multi-modal Learning:** Text, code, formulas, visualizations
5. **Personalization:** Study plans based on student history

### Technical Features
1. **Streaming Responses:** FastAPI SSE for real-time UI updates
2. **Mode Switching:** Orchestrator routes between Navigate/Educate
3. **Conversation Context:** Multi-turn dialogue with history
4. **Error Handling:** Graceful fallbacks for retrieval/LLM failures
5. **Tracing:** Agent execution logging via `trace_callback`

---

## 6. Migration Challenges

### Challenge 1: Custom States (TypedDict)
- **Issue:** LangFlow uses YAML/JSON for state; LangGraph uses Python TypedDict
- **Solution:** Map TypedDict fields to LangFlow variables/Memory nodes

### Challenge 2: Conditional Routing
- **Issue:** `_route_after_retrieval` dynamically chooses quiz/study/teach
- **Solution:** Use LangFlow conditional branches (if-else logic nodes)

### Challenge 3: Supabase Integration
- **Issue:** `student_model_agent` directly queries Supabase
- **Solution:** Create LangFlow custom component with Supabase SDK

### Challenge 4: ChromaDB Retrieval
- **Issue:** `retrieval_agent` uses ChromaDB instance from state
- **Solution:** LangFlow has built-in "Vector Store Retriever" component

### Challenge 5: Trace Callbacks
- **Issue:** `_wrap_agent_with_trace` logs agent execution
- **Solution:** LangFlow has native tracing; use built-in logging

---

## 7. Estimated Agent Count: 11 Total

**Note:** The migration guide mentions "13 agents"—actual count is **11 unique agents** across both modes (some agents are reused, e.g., `retrieval_agent` used in both modes).

---

## Next Steps
1. Create `migration_map.json` mapping LangGraph nodes → LangFlow components
2. Export LangGraph configs to JSON for import into LangFlow
3. Build 3-5 LangFlow flows grouping agents by function
