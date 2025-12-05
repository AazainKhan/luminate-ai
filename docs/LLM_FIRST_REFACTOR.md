# LLM-First Architecture Refactor

## Summary

This document describes the refactoring from a **regex-first** to **LLM-first** routing architecture for the Course Marshal AI tutor.

## Problem Statement

The original architecture used regex pattern matching as the primary routing mechanism:

```
User Query → Regex Patterns (95%) → Intent → Agent
                    ↓
              LLM Fallback (5%) → Intent → Agent
```

**Issues:**
1. Brittle patterns that missed nuances ("explain X" vs "I don't understand X")
2. No multi-step reasoning before routing
3. No context awareness in routing decisions
4. Hard to maintain growing pattern lists

## New Architecture

```
User Query → Governor → Reasoning Node → Supervisor → Agent
                              ↓
                        Multi-step LLM Analysis
                        (Perceive → Analyze → Plan → Decide)
```

**Benefits:**
1. LLM understands query nuances and confusion signals
2. Multi-step reasoning provides better context
3. Confidence scores enable fallback logic
4. Extensible without pattern maintenance

## Files Changed

### New Files

#### 1. `backend/app/agents/reasoning_node.py`
- Multi-step reasoning engine
- Phases: Perceive → Analyze → Plan → Decide
- Output: `ReasoningOutput` with structured analysis
- Uses Gemini Flash at low temperature (0.1) for consistency

#### 2. `backend/app/agents/context_engineer.py`
- Context curation and compaction
- Methods:
  - `curate_context()` - Filter by relevance scores
  - `compact_history()` - Summarize long conversations
  - `build_student_context()` - Aggregate mastery/preferences
  - `format_for_prompt()` - XML-structured output

### Modified Files

#### 3. `backend/app/agents/supervisor.py`
- New routing method: `route_with_reasoning(state)`
- Fast-path patterns reduced to 95%+ confidence cases only
- LLM classification as primary method
- Intent mapping now includes `explain` intent

#### 4. `backend/app/agents/state.py`
New fields added:
```python
# Reasoning node output
reasoning_complete: bool
reasoning_intent: Optional[str]
reasoning_confidence: Optional[float]
reasoning_strategy: Optional[str]
reasoning_context_needed: Optional[List[str]]
reasoning_trace: Optional[str]

# Context engineering
curated_context: Optional[str]
context_budget_tokens: Optional[int]
context_relevance_scores: Optional[dict]
```

#### 5. `backend/app/agents/tutor_agent.py`
- Added reasoning node to graph
- New flow: `governor → reasoning → supervisor → [agent]`
- Updated queue events for UI feedback

#### 6. `backend/app/agents/tools.py`
- Enhanced tool descriptions with WHEN TO USE / WHEN NOT TO USE
- Better input validation schemas
- Example queries in docstrings

## Intent Routing Rules

| Query Pattern | Intent | Response Style |
|--------------|--------|----------------|
| "briefly, what is X" | `fast` | 1-3 sentences |
| "explain X" (no confusion) | `explain` | 3-5 paragraphs |
| "I don't understand X" | `tutor` | Full Socratic scaffolding |
| "derive the formula for X" | `math` | Step-by-step derivation |
| "what is this course about" | `syllabus_query` | 2-4 sentences |
| "implement X in Python" | `coder` | Code + explanation |

## Testing

Run the routing test suite:

```bash
docker exec api_brain python -c "
import uuid
from app.agents.tutor_agent import run_agent

tests = [
    ('what is this course about?', 'syllabus_query'),
    ('briefly, what is gradient descent?', 'fast'),
    ('explain neural networks', 'explain'),
    ('derive the chain rule for backprop', 'math'),
    ('I dont understand classification', 'tutor'),
]

for query, expected in tests:
    result = run_agent(query=query, user_id=str(uuid.uuid4()), user_email='test@test.com')
    intent = result.get('intent', 'unknown')
    match = '✅' if intent == expected else '❌'
    print(f'{match} [{expected:15}→{intent:15}] \"{query}\"')
"
```

Expected: All ✅

## Observability

The reasoning node creates Langfuse spans with:
- Reasoning trace (full thinking process)
- Intent confidence scores
- Strategy selection rationale
- Processing time metrics

Check Langfuse dashboard: `http://localhost:3000`

## Future Improvements

1. **Caching**: Cache reasoning outputs for similar queries
2. **Fine-tuning**: Collect routing data for potential model fine-tuning
3. **A/B Testing**: Compare LLM-first vs regex-first performance
4. **Observability**: Track routing accuracy over time

## Rollback

If issues occur, revert to regex-first by:

1. In `supervisor.py`, change `supervisor_node()` to call `route_with_hybrid()` instead of `route_with_reasoning()`
2. In `tutor_agent.py`, remove reasoning node from graph flow

---

*Refactor Date: January 2025*
*Author: Course Marshal Development Team*
