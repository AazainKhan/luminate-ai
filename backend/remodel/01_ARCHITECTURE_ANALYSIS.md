# Architecture Analysis: What's Working and What's Not

## Executive Summary

The Luminate AI tutor has a **well-structured multi-agent architecture** but suffers from **over-engineering** that hurts user experience. The main issues:

1. **Repetitive Response Patterns**: Hard-coded prompt formats force identical structure
2. **No Conversation Awareness**: Follow-ups treated same as initial queries
3. **Unknown Sources**: RAG metadata extraction fails silently
4. **Reasoning Leakage**: Internal reasoning may leak to user stream
5. **Redundant Classification**: Both `reasoning_node` and `supervisor` classify intent

---

## Current Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TUTOR_AGENT.PY GRAPH                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   User Query                                                            │
│       │                                                                 │
│       ▼                                                                 │
│   ┌─────────────┐                                                       │
│   │  Governor   │◄─── Law 1: Scope (ChromaDB distance < 0.80)           │
│   │  (3 Laws)   │◄─── Law 2: Integrity (no full solutions)              │
│   │             │◄─── Law 3: Mastery (deferred)                         │
│   └──────┬──────┘                                                       │
│          │                                                              │
│          ▼                                                              │
│   ┌─────────────┐    PROBLEM: Does full query analysis                  │
│   │  Reasoning  │◄─── including intent classification                   │
│   │    Node     │     confusion detection, bloom level                  │
│   │ (LLM Call)  │                                                       │
│   └──────┬──────┘                                                       │
│          │                                                              │
│          ▼                                                              │
│   ┌─────────────┐    PROBLEM: Also classifies intent!                   │
│   │ Supervisor  │◄─── fast-path regex, then LLM fallback                │
│   │  (Router)   │     Redundant with reasoning_node                     │
│   └──────┬──────┘                                                       │
│          │                                                              │
│          ▼                                                              │
│   ┌─────────────────────────────────────────────────────┐               │
│   │                 AGENT NODE                           │              │
│   │  Routes to one of:                                   │              │
│   │  • fast → Quick response                            │              │
│   │  • explain → Medium response                        │              │
│   │  • tutor → Full Socratic (pedagogical_tutor.py)    │              │
│   │  • math → Step-by-step derivations                 │              │
│   │  • coder → Code assistance                         │              │
│   │  • syllabus_query → Course info                    │              │
│   │                                                     │              │
│   │  PROBLEM: Each intent has rigid SYSTEM_PROMPTS     │              │
│   │  that force identical response structure            │              │
│   └──────┬──────────────────────────────────────────────┘               │
│          │                                                              │
│          ▼                                                              │
│   ┌─────────────┐                                                       │
│   │  Evaluator  │◄─── Logs to Supabase, Langfuse                        │
│   │             │◄─── Updates mastery                                   │
│   └─────────────┘                                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Problem 1: Repetitive Response Patterns

### Root Cause
The `SYSTEM_PROMPTS["explain"]` in `tutor_agent.py` forces this structure:

```python
"explain": """...
3. Structure your response like this:
   - **What it is**: 1-2 sentence definition
   - **How it works**: Brief explanation (2-3 sentences)  
   - **Example**: One concrete example from the course materials
   - **Key point**: 1 sentence summary
4. End with: "Would you like me to go deeper or try a practice problem?"
"""
```

This causes EVERY `explain` response to look identical, regardless of:
- What the concept is
- How complex it is
- Whether the student already knows basics
- Whether it's a follow-up question

### Evidence
When user asks "explain gradient descent", they get:
```
**What it is**: Gradient descent is...
**How it works**: The algorithm works by...
**Example**: In COMP 237, you'll see...
**Key point**: The key insight is...

Would you like me to go deeper or try a practice problem?
```

When they say "go deeper", they get the SAME structure, just longer.

### Solution
See `02_PROMPT_ENGINEERING_OVERHAUL.md`

---

## Problem 2: No Conversation Awareness

### Root Cause
The `astream_agent()` function treats EVERY query the same:

```python
async def astream_agent(query, user_id, user_email, session_id, chat_id, conversation_history):
    # conversation_history is loaded but NOT used to adjust behavior
    initial_state = {
        "query": query,
        "conversation_history": conversation_history,  # <-- Present but ignored
        # ... same state initialization for turn 1 or turn 20
    }
```

The prompts don't adapt based on:
- Is this a follow-up to the previous message?
- Has the user already seen the basic explanation?
- What scaffolding level was used in the last turn?

### Evidence
Turn 1: "explain gradient descent" → Full 4-section response
Turn 2: "go deeper" → ANOTHER full 4-section response with "What it is" again

The user JUST asked about gradient descent. Why explain "What it is" again?

### Solution
See `03_CONVERSATION_AWARE_PROMPTING.md`

---

## Problem 3: Unknown Sources

### Root Cause
The RAG pipeline loses source metadata at multiple points:

1. **ChromaDB stores it correctly** (verified):
   ```python
   # In langchain_chroma.py
   metadata = {
       "source_file": filename,  # ✓ Stored
       "course_id": "COMP237",
       # ...
   }
   ```

2. **Retrieval returns it** (verified):
   ```python
   # RAGAgent.retrieve_context() returns:
   [{"content": "...", "source_filename": "...", "relevance_score": 0.65}]
   ```

3. **BUT: sub_agents.py loses it**:
   ```python
   # In generate_response_node():
   source = doc.get("source_filename") or doc.get("metadata", {}).get("source_filename", "Unknown")
   #                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   #                                     This fallback path gets "Unknown" if structure is different
   ```

4. **AND: tutor_agent.py also loses it**:
   ```python
   # In _process_event():
   sources = state.get("response_sources", [])
   # But response_sources is populated differently by different agents
   # Sometimes it's strings, sometimes dicts, sometimes empty
   ```

### Evidence
User sees: `[Sources: Unknown, Unknown]` instead of `[Sources: COMP_237_COURSEOUTLINE.pdf, module3_slides.pdf]`

### Solution
See `04_SOURCE_METADATA_FIX.md`

---

## Problem 4: Reasoning Leakage

### Root Cause
The `reasoning_node.py` outputs a JSON structure:

```json
{
  "query_type": "conceptual_explanation",
  "topic_domain": "optimization",
  "confusion_signals": [],
  "bloom_level": "understand",
  "recommended_intent": "explain"
}
```

This is stored in state as `reasoning_trace`. The `_process_event()` function attempts to filter it:

```python
# In tutor_agent.py:
def _is_internal_output(content: str) -> bool:
    # Detect internal reasoning outputs that shouldn't be streamed
    internal_patterns = [
        "reasoning_trace",
        "query_type",
        # ...
    ]
```

**BUT**: The filtering happens AFTER streaming starts. If the LLM includes reasoning in its response, it leaks.

### Evidence
Sometimes users see fragments like:
```
Based on my analysis: query_type=conceptual, recommended_intent=explain

**What it is**: Gradient descent...
```

### Solution
- Move filtering to happen BEFORE yield
- Strip reasoning blocks from final response
- Use separate channels for internal vs user-facing content

---

## Problem 5: Redundant Classification

### Root Cause
Intent is classified **TWICE**:

1. **reasoning_node.py** (LLM call):
   ```python
   response = self.model.invoke(...)
   # Returns: {"recommended_intent": "explain", "confidence": 0.85}
   ```

2. **supervisor.py** (fast-path + LLM fallback):
   ```python
   # First tries regex patterns
   if self._check_fast_path_patterns(query):
       return "fast"
   # Then calls LLM if confidence < 0.7
   classification = self._llm_classify_intent(query)
   ```

These can disagree! When reasoning_node says `"explain"` but supervisor says `"tutor"`, which wins?

Currently: **supervisor always wins**, making reasoning_node's intent classification wasted tokens.

### Evidence
In logs:
```
reasoning_node: recommended_intent=explain (0.85)
supervisor: intent=tutor (0.72)  # Different!
agent_node: using intent=tutor   # Supervisor wins
```

### Solution
See `05_AGENT_CONSOLIDATION.md`

---

## Redundancy Analysis

| Component | Purpose | Redundant With | Recommendation |
|-----------|---------|----------------|----------------|
| `reasoning_node` | Intent + strategy analysis | `supervisor` | **Merge** - keep reasoning, remove supervisor's LLM classification |
| `supervisor.py` fast-path | Quick regex routing | `reasoning_node` confidence | **Keep** - useful for very obvious queries |
| `governor.py` | Policy enforcement | Nothing | **Keep** - essential |
| `pedagogical_tutor.py` | Socratic scaffolding | `SYSTEM_PROMPTS["tutor"]` | **Keep** - but simplify prompt |
| `math_agent.py` | Math derivations | Could be merged with tutor | **Keep** - specialized behavior |
| `evaluator.py` | Quality + mastery | Nothing | **Keep** - essential |
| `sub_agents.py` RAGAgent | Context retrieval | `retrieve_context` tool | **Merge** - one RAG path |
| `generate_response_node` | Response generation | `agent_node` | **Remove** - duplicate |

### Simplified Architecture Proposal

```
User Query
    │
    ▼
┌─────────────┐
│  Governor   │  (Keep - essential)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │  (Merge reasoning + supervisor)
│  (LLM-First │   Single LLM call for:
│   Unified)  │   - Intent classification
└──────┬──────┘   - Confusion detection
       │          - Teaching strategy
       │
       ▼
┌─────────────────────────────────────┐
│           AGENT NODE                │
│  • ConversationAwarePromptBuilder  │
│    (adapts based on turn, history) │
│  • Calls tools as needed           │
│  • Routes to specialized handlers  │
│    only when necessary             │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌─────────────┐
        │  Evaluator  │  (Keep - essential)
        └─────────────┘
```

**Result**: 2 fewer LLM calls per request, clearer control flow

---

## Files To Modify

| Priority | File | Change Required |
|----------|------|-----------------|
| P0 | `tutor_agent.py` | Remove rigid prompt formats, add conversation awareness |
| P0 | `sub_agents.py` | Fix source metadata propagation |
| P1 | `supervisor.py` | Remove LLM classification (use reasoning_node's) |
| P1 | `reasoning_node.py` | Expand to be the single routing decision point |
| P2 | `pedagogical_tutor.py` | Simplify prompts, remove duplicate scaffolding logic |
| P2 | `state.py` | Add conversation turn tracking fields |
| P3 | `evaluator.py` | Add conversation coherence scoring |

---

## Next Steps

1. Read `02_PROMPT_ENGINEERING_OVERHAUL.md` - Fix rigid prompts
2. Read `03_CONVERSATION_AWARE_PROMPTING.md` - Add turn awareness
3. Read `04_SOURCE_METADATA_FIX.md` - Fix unknown sources
4. Read `05_AGENT_CONSOLIDATION.md` - Merge redundant components
5. Read `06_TEST_SUITE_DESIGN.md` - Comprehensive UX tests
6. Read `07_IMPLEMENTATION_PLAN.md` - Step-by-step execution plan
