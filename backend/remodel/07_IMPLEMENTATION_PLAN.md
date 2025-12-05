# Implementation Plan: Step-by-Step Execution

## Executive Summary

This plan prioritizes **quick wins first** to immediately improve UX, then tackles architectural changes.

**Timeline**: 3 phases over ~2 weeks
**Priority Order**: Fix visible bugs → Improve prompts → Consolidate architecture

---

## Phase 1: Quick Wins (Days 1-3)

These changes have **immediate user impact** with **minimal risk**.

### 1.1 Fix Unknown Sources (Day 1)

**File**: `backend/app/agents/source_metadata.py` (CREATE)

```bash
# Create the source metadata module
touch backend/app/agents/source_metadata.py
```

**Changes**:
1. Create `Source` dataclass (see `04_SOURCE_METADATA_FIX.md`)
2. Create `extract_sources()` utility function
3. Create `format_sources_for_response()` utility

**Test**:
```bash
docker exec api_brain python -c "
from app.agents.source_metadata import Source, extract_sources

# Test with sample RAG output
sample = [{'content': 'test', 'metadata': {'source_file': 'test.pdf'}}]
sources = extract_sources(sample)
print(f'Extracted: {[s.filename for s in sources]}')
assert sources[0].filename == 'test.pdf'
print('✅ Source extraction works')
"
```

**Files Modified**:
- `backend/app/agents/source_metadata.py` - CREATE
- `backend/app/agents/sub_agents.py` - Use `extract_sources()`
- `backend/app/agents/tutor_agent.py` - Add source collection

---

### 1.2 Remove Rigid Prompt Structure (Day 1-2)

**File**: `backend/app/agents/tutor_agent.py`

**Current** (Line ~120):
```python
SYSTEM_PROMPTS = {
    "explain": """...
    3. Structure your response like this:
       - **What it is**: 1-2 sentence definition
       - **How it works**: Brief explanation
       - **Example**: One concrete example
       - **Key point**: 1 sentence summary
    4. End with: "Would you like me to go deeper..."
    """,
}
```

**New**:
```python
SYSTEM_PROMPTS = {
    "explain": """You are Course Marshal, an AI tutor for COMP 237.

Guidelines:
1. Explain concepts clearly and accessibly
2. Use examples from course materials when available
3. Match explanation depth to the question complexity
4. Cite sources naturally: "According to the course materials..."

Do NOT:
- Use a rigid template structure
- Always end with "Would you like me to..."
- Over-explain simple questions

Adapt your response to what the student actually needs.""",
    
    "fast": """You are Course Marshal. Give a direct, concise answer.
Keep it under 3 sentences unless more is genuinely needed.
Don't ask follow-up questions.""",
    
    "tutor": """You are Course Marshal, a Socratic tutor for COMP 237.

If the student is confused:
- Ask clarifying questions to understand their gap
- Use analogies and simpler explanations
- Check understanding before moving on

If the student is NOT confused:
- Don't force Socratic questioning
- Answer directly while being pedagogical

Adapt your approach to the student's needs.""",
}
```

**Test**:
```bash
# Run multiple explain queries, check for variety
docker exec api_brain python -c "
from app.agents.tutor_agent import run_agent

responses = []
for topic in ['gradient descent', 'backpropagation', 'decision trees']:
    r = run_agent(f'explain {topic}', 'test', 'test@test.com')
    responses.append(r.get('response', ''))

# Check none have rigid structure
rigid_count = 0
for r in responses:
    if '**What it is**:' in r and '**How it works**:' in r:
        rigid_count += 1

print(f'Responses with rigid structure: {rigid_count}/3')
assert rigid_count == 0, 'Should not have rigid structure'
print('✅ Rigid structure removed')
"
```

---

### 1.3 Add Response Length Signals (Day 2)

**Goal**: Detect and honor "briefly", "in detail" requests.

**File**: `backend/app/agents/supervisor.py`

Add to `INTENT_PATTERNS`:
```python
INTENT_PATTERNS = {
    # ... existing patterns ...
    
    "fast_explicit": [
        r"^briefly\b",
        r"^quick(ly)?\b",
        r"\bin (one|a) sentence\b",
        r"\bshort answer\b",
        r"\btl;?dr\b",
    ],
    "detail_explicit": [
        r"\bin detail\b",
        r"\bgo deep(er)?\b",
        r"\belaborate\b",
        r"\bexplain (thoroughly|completely)\b",
    ],
}
```

Update `route_with_reasoning()`:
```python
def route_with_reasoning(self, state):
    query = state.get("query", "").lower()
    
    # Check for explicit length signals FIRST
    for pattern in self.INTENT_PATTERNS.get("fast_explicit", []):
        if re.search(pattern, query):
            state["response_length_hint"] = "brief"
            # Can still be any intent, just short
            break
    
    for pattern in self.INTENT_PATTERNS.get("detail_explicit", []):
        if re.search(pattern, query):
            state["response_length_hint"] = "detailed"
            break
    
    # ... rest of routing
```

---

## Phase 2: Conversation Awareness (Days 4-7)

### 2.1 Create Conversation Tracker (Day 4)

**File**: `backend/app/agents/conversation_tracker.py` (CREATE)

See `03_CONVERSATION_AWARE_PROMPTING.md` for full implementation.

```bash
touch backend/app/agents/conversation_tracker.py
```

**Test**:
```bash
docker exec api_brain python -c "
from app.agents.conversation_tracker import ConversationTracker

tracker = ConversationTracker()

# Simulate 3-turn conversation
history = [
    {'role': 'user', 'content': 'explain gradient descent'},
    {'role': 'assistant', 'content': 'Gradient descent is...'},
    {'role': 'user', 'content': 'go deeper'},
    {'role': 'assistant', 'content': 'Let me elaborate...'},
]

state = tracker.analyze_conversation('what about learning rate?', history)
print(f'Turn: {state.turn_number}')
print(f'Topics: {state.topics_discussed}')
print(f'Phase: {state.phase}')

assert state.turn_number == 3
assert 'gradient_descent' in state.topics_discussed
print('✅ Conversation tracking works')
"
```

---

### 2.2 Integrate Tracker with Agent (Day 5)

**File**: `backend/app/agents/tutor_agent.py`

Update `astream_agent()`:
```python
from app.agents.conversation_tracker import (
    ConversationTracker, 
    build_conversation_context_prompt
)

async def astream_agent(query, user_id, user_email, session_id, chat_id, conversation_history):
    # NEW: Analyze conversation
    tracker = ConversationTracker()
    conv_state = tracker.analyze_conversation(query, conversation_history)
    conv_context = build_conversation_context_prompt(tracker, query, conversation_history)
    
    initial_state = {
        "query": query,
        "conversation_history": conversation_history,
        # NEW: Conversation awareness
        "turn_number": conv_state.turn_number,
        "current_topic": conv_state.current_topic,
        "topics_discussed": conv_state.topics_discussed,
        "conversation_context": conv_context,
        "skip_intro": tracker.should_skip_intro(conv_state, conv_state.current_topic or ""),
        # ... rest of state
    }
```

Update `agent_node()` to use `conversation_context`:
```python
def agent_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "fast")
    base_prompt = SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["explain"])
    
    # Inject conversation context
    conv_context = state.get("conversation_context", "")
    if conv_context:
        full_prompt = f"{base_prompt}\n\n{conv_context}"
    else:
        full_prompt = base_prompt
    
    # Add skip_intro instruction if needed
    if state.get("skip_intro"):
        full_prompt += "\n\nIMPORTANT: This topic was just discussed. Do NOT repeat the introduction or definition. Build on what was said."
```

---

### 2.3 Add State Fields (Day 5)

**File**: `backend/app/agents/state.py`

```python
class AgentState(TypedDict):
    # ... existing fields ...
    
    # NEW: Conversation tracking
    turn_number: Optional[int]
    current_topic: Optional[str]
    topics_discussed: Optional[List[str]]
    conversation_context: Optional[str]
    skip_intro: bool
    response_length_hint: Optional[Literal["brief", "normal", "detailed"]]
    previous_intent: Optional[str]
```

---

### 2.4 Write Conversation Tests (Day 6-7)

**File**: `backend/tests/test_conversation_coherence.py` (CREATE)

See `06_TEST_SUITE_DESIGN.md` for test implementations.

```bash
# Run conversation tests
pytest backend/tests/test_conversation_coherence.py -v
```

---

## Phase 3: Architecture Cleanup (Days 8-14)

### 3.1 Create Unified Router (Day 8-9)

**File**: `backend/app/agents/unified_router.py` (CREATE)

See `05_AGENT_CONSOLIDATION.md` for full implementation.

**Feature Flag**:
```python
# In tutor_agent.py
import os
USE_UNIFIED_ROUTER = os.getenv("USE_UNIFIED_ROUTER", "false").lower() == "true"
```

**Test**:
```bash
# Test with feature flag enabled
USE_UNIFIED_ROUTER=true docker exec api_brain python -c "
from app.agents.unified_router import UnifiedRouter

router = UnifiedRouter()
decision = router.route('explain gradient descent')

print(f'Intent: {decision.intent.value}')
print(f'Confidence: {decision.confidence}')
print(f'Topic: {decision.topic}')

assert decision.intent.value in ['explain', 'tutor']
print('✅ Unified router works')
"
```

---

### 3.2 A/B Test Old vs New (Day 10)

Create comparison test:
```python
# backend/tests/test_router_comparison.py

def test_routing_equivalence():
    """Ensure new router produces same results as old system."""
    from app.agents.unified_router import UnifiedRouter
    from app.agents.supervisor import Supervisor
    from app.agents.reasoning_node import reasoning_node
    
    test_queries = [
        ("briefly what is ML", "fast"),
        ("explain gradient descent", "explain"),
        ("I'm confused about backprop", "tutor"),
        ("when is the midterm", "syllabus_query"),
    ]
    
    old_supervisor = Supervisor()
    new_router = UnifiedRouter()
    
    mismatches = []
    for query, expected in test_queries:
        # Old system
        old_state = {"query": query}
        old_state = reasoning_node(old_state)
        old_state = old_supervisor.supervisor_node(old_state)
        old_intent = old_state.get("intent")
        
        # New system
        new_decision = new_router.route(query)
        new_intent = new_decision.intent.value
        
        if old_intent != new_intent:
            mismatches.append((query, old_intent, new_intent))
    
    print(f"Mismatches: {len(mismatches)}/{len(test_queries)}")
    for q, old, new in mismatches:
        print(f"  '{q}': old={old}, new={new}")
    
    # Allow some divergence if new is reasonable
    assert len(mismatches) <= 1, f"Too many mismatches: {mismatches}"
```

---

### 3.3 Enable Unified Router (Day 11)

Once tests pass:
```bash
# Update docker-compose.yml or .env
echo "USE_UNIFIED_ROUTER=true" >> backend/.env
```

Monitor Langfuse for any routing anomalies.

---

### 3.4 Remove Deprecated Code (Day 12-14)

After 2 days of stable operation:

1. Remove `reasoning_node.py` (functionality merged into `unified_router.py`)
2. Simplify `supervisor.py` (keep only fast-path patterns for backward compat)
3. Update `tutor_agent.py` to only use unified router

---

## Verification Checklist

After each phase, verify:

### Phase 1 Verification
- [ ] Sources display actual filenames, not "Unknown"
- [ ] Responses show varied structure
- [ ] "briefly" queries get short responses
- [ ] "in detail" queries get comprehensive responses

### Phase 2 Verification
- [ ] Follow-up questions don't repeat intro
- [ ] Topic switches are handled cleanly
- [ ] Turn 5 is shorter than Turn 1
- [ ] "I'm confused" triggers scaffolding

### Phase 3 Verification
- [ ] Single LLM call for routing (not 2)
- [ ] Latency reduced by ~500ms
- [ ] No routing conflicts
- [ ] All existing tests still pass

---

## Rollback Plan

If issues arise:

### Phase 1 Rollback
```bash
# Revert source_metadata.py changes
git checkout HEAD~1 -- backend/app/agents/source_metadata.py
git checkout HEAD~1 -- backend/app/agents/sub_agents.py
```

### Phase 2 Rollback
```bash
# Remove conversation_tracker.py
rm backend/app/agents/conversation_tracker.py
git checkout HEAD~1 -- backend/app/agents/tutor_agent.py
```

### Phase 3 Rollback
```bash
# Disable unified router
echo "USE_UNIFIED_ROUTER=false" > backend/.env
docker-compose restart api_brain
```

---

## Success Metrics

| Metric | Current | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|---------|
| Unknown sources | Common | 0% | 0% | 0% |
| Rigid structure | 100% | 0% | 0% | 0% |
| Follow-up repeats intro | Yes | Yes | No | No |
| Routing LLM calls | 2 | 2 | 2 | 1 |
| Avg latency | ~2s | ~2s | ~2s | ~1.5s |
| Test pass rate | ~20% | ~50% | ~85% | ~95% |

---

## Files Summary

### New Files
| File | Phase | Purpose |
|------|-------|---------|
| `source_metadata.py` | 1 | Fix source extraction |
| `conversation_tracker.py` | 2 | Track conversation state |
| `unified_router.py` | 3 | Single routing decision point |
| `prompt_builder.py` | 2 | Adaptive prompt generation |

### Modified Files
| File | Phase | Changes |
|------|-------|---------|
| `tutor_agent.py` | 1,2,3 | Remove rigid prompts, add conversation awareness, use unified router |
| `supervisor.py` | 1,3 | Add length signals, simplify to fast-path only |
| `sub_agents.py` | 1 | Fix source metadata |
| `state.py` | 2 | Add conversation fields |

### Removed Files (Phase 3)
| File | Reason |
|------|--------|
| `reasoning_node.py` | Merged into unified_router |

---

## Estimated Effort

| Phase | Days | Risk | Impact |
|-------|------|------|--------|
| Phase 1: Quick Wins | 3 | Low | High |
| Phase 2: Conversation | 4 | Medium | High |
| Phase 3: Architecture | 7 | Medium | Medium |

**Total: ~14 days of focused work**

Recommend starting Phase 1 immediately as it has highest impact-to-risk ratio.
