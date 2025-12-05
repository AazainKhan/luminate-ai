# Agent Consolidation: Removing Redundancy

## The Problem

The current architecture has **redundant classification** where multiple components do the same job:

1. **reasoning_node** (LLM call): Classifies intent, detects confusion, recommends strategy
2. **supervisor** (regex + LLM fallback): Also classifies intent

This wastes tokens, adds latency, and creates conflicts when they disagree.

---

## Current Redundant Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  User Query: "explain gradient descent"                                 │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  REASONING NODE (LLM Call #1)                                    │   │
│  │                                                                  │   │
│  │  Input: query + conversation_history                             │   │
│  │  Output: {                                                       │   │
│  │    "query_type": "conceptual_explanation",                       │   │
│  │    "topic_domain": "optimization",                               │   │
│  │    "confusion_signals": [],                                      │   │
│  │    "bloom_level": "understand",                                  │   │
│  │    "recommended_intent": "explain",  ◀── Intent classified       │   │
│  │    "teaching_strategy": "progressive_disclosure",                │   │
│  │    "confidence": 0.87                                            │   │
│  │  }                                                               │   │
│  │                                                                  │   │
│  │  Cost: ~500 tokens input, ~150 tokens output                     │   │
│  └───────────────────────────┬─────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  SUPERVISOR (Regex + LLM Call #2)                                │   │
│  │                                                                  │   │
│  │  1. Fast-path regex: No match                                    │   │
│  │  2. Check reasoning confidence: 0.87 > 0.7 ✓                     │   │
│  │  3. BUT THEN: Still calls LLM for "verification"! ❌             │   │
│  │                                                                  │   │
│  │  Output: "explain" (or sometimes different!) ◀── REDUNDANT       │   │
│  │                                                                  │   │
│  │  Cost: Another ~300 tokens                                       │   │
│  └───────────────────────────┬─────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│                                                                         │
│  Total cost per query: ~950 tokens just for intent classification!     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The Conflict Problem

When reasoning_node and supervisor disagree:

```python
# reasoning_node output
{
    "recommended_intent": "explain",
    "confidence": 0.85
}

# supervisor output (called anyway)
{
    "intent": "tutor",  # Different!
    "confidence": 0.72
}

# What happens: supervisor ALWAYS wins
# Result: reasoning_node's analysis is wasted
```

This happens because in `tutor_agent.py`:

```python
# supervisor.route_with_reasoning() is called
# It can override reasoning_node's recommendation
state = supervisor_node(state)  # ← This sets final intent
```

---

## Proposed Solution: Unified Router

Merge reasoning and routing into **one intelligent router**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  User Query: "explain gradient descent"                                 │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  UNIFIED ROUTER (Single LLM Call)                                │   │
│  │                                                                  │   │
│  │  Fast-path regex: Check first (0 tokens if matches)              │   │
│  │                   ↓ (no match)                                   │   │
│  │  LLM Classification: Single call for everything                  │   │
│  │                                                                  │   │
│  │  Output: {                                                       │   │
│  │    "intent": "explain",                                          │   │
│  │    "confidence": 0.87,                                           │   │
│  │    "topic": "gradient_descent",                                  │   │
│  │    "confusion_detected": false,                                  │   │
│  │    "bloom_level": "understand",                                  │   │
│  │    "teaching_strategy": "progressive_disclosure",                │   │
│  │    "context_needed": ["rag"],                                    │   │
│  │    "scaffolding_hint": "standard"                                │   │
│  │  }                                                               │   │
│  │                                                                  │   │
│  │  Cost: ~500 tokens (same as reasoning_node alone)                │   │
│  └───────────────────────────┬─────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│                                                                         │
│  Total cost: ~500 tokens (was ~950)                                    │
│  Latency: 1 LLM call (was 2)                                          │
│  Conflicts: Impossible (single source of truth)                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation: Unified Router

```python
# NEW: backend/app/agents/unified_router.py

from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import re
import json
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

logger = logging.getLogger(__name__)

class Intent(Enum):
    FAST = "fast"           # Quick factual answer
    EXPLAIN = "explain"     # Medium-depth explanation
    TUTOR = "tutor"         # Full Socratic scaffolding
    MATH = "math"           # Mathematical derivations
    CODER = "coder"         # Code assistance
    SYLLABUS = "syllabus_query"  # Course logistics

@dataclass
class RoutingDecision:
    """Complete routing decision from unified router."""
    intent: Intent
    confidence: float
    topic: Optional[str]
    confusion_detected: bool
    bloom_level: str
    teaching_strategy: str
    context_needed: List[str]  # ["rag", "syllabus", "none"]
    scaffolding_hint: str  # "minimal", "standard", "heavy"
    reasoning_trace: str  # For debugging/observability

class UnifiedRouter:
    """
    Single router that replaces both reasoning_node and supervisor.
    
    Combines:
    - Fast-path regex (supervisor's best feature)
    - LLM analysis (reasoning_node's intelligence)
    - Intent classification (both did this)
    
    Into ONE component with ONE decision.
    """
    
    # Fast-path patterns: Skip LLM entirely for obvious cases
    FAST_PATH_PATTERNS = {
        Intent.FAST: [
            r"^briefly\b",
            r"^quick(ly)?\b",
            r"^what is the definition of\b",
            r"^define\b",
        ],
        Intent.SYLLABUS: [
            r"\b(when|what time) is (the )?(midterm|exam|final|quiz)\b",
            r"\bdue date\b",
            r"\boffice hours\b",
            r"\bgrading (policy|weight|breakdown)\b",
            r"\blate (submission|policy)\b",
        ],
        Intent.CODER: [
            r"^(write|implement|code|create) (a |the )?(python|function|class)\b",
            r"\bsyntax error\b",
            r"\bdebug (this|my)\b",
        ],
        Intent.MATH: [
            r"\bderive\b",
            r"\bprove (that|the)\b",
            r"\bstep[- ]by[- ]step\b.*(formula|equation|derivation)",
        ],
    }
    
    # Confusion signals that override other routing
    CONFUSION_PATTERNS = [
        r"\bi don'?t understand\b",
        r"\bconfused about\b",
        r"\bwhat do you mean\b",
        r"\bcan you explain .* again\b",
        r"\bi'?m lost\b",
        r"\bstill don'?t get\b",
    ]
    
    ROUTING_PROMPT = """Analyze this student query and determine the best response strategy.

QUERY: {query}

CONVERSATION CONTEXT:
- Turn number: {turn_number}
- Previous topic: {previous_topic}
- Previous intent: {previous_intent}

Respond with a JSON object:
{{
    "intent": "fast|explain|tutor|math|coder|syllabus_query",
    "confidence": 0.0-1.0,
    "topic": "detected AI/ML topic or null",
    "confusion_detected": true/false,
    "bloom_level": "remember|understand|apply|analyze|evaluate|create",
    "teaching_strategy": "direct|progressive_disclosure|socratic|worked_example",
    "context_needed": ["rag", "syllabus", "none"],
    "scaffolding_hint": "minimal|standard|heavy"
}}

INTENT GUIDELINES:
- fast: Simple factual questions, definitions, quick lookups
- explain: Conceptual explanations, "explain X", "how does Y work"
- tutor: Student shows confusion, needs scaffolding, says "don't understand"
- math: Mathematical derivations, proofs, step-by-step calculations
- coder: Code writing, debugging, implementation help
- syllabus_query: Course logistics, dates, policies, administrative info

IMPORTANT:
- If confusion detected, intent should usually be "tutor" with heavy scaffolding
- For follow-up questions on same topic, consider lighter scaffolding
- Match context_needed to what's actually required (don't always use RAG)

JSON only, no other text:"""
    
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.1,  # Low temp for consistent routing
        )
    
    def route(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None,
        turn_number: int = 1,
        previous_topic: Optional[str] = None,
        previous_intent: Optional[str] = None,
    ) -> RoutingDecision:
        """
        Route the query to the appropriate handler.
        
        Tries fast-path first, falls back to LLM.
        """
        query_lower = query.lower().strip()
        
        # Step 1: Check for confusion (always override to tutor)
        if self._detect_confusion(query_lower):
            logger.info("🔄 Router: Confusion detected, routing to tutor")
            return RoutingDecision(
                intent=Intent.TUTOR,
                confidence=0.95,
                topic=self._extract_topic(query_lower),
                confusion_detected=True,
                bloom_level="understand",
                teaching_strategy="socratic",
                context_needed=["rag"],
                scaffolding_hint="heavy",
                reasoning_trace="confusion_override"
            )
        
        # Step 2: Try fast-path patterns
        fast_path_result = self._try_fast_path(query_lower)
        if fast_path_result:
            logger.info(f"🔄 Router: Fast-path to {fast_path_result.value}")
            return RoutingDecision(
                intent=fast_path_result,
                confidence=0.90,
                topic=self._extract_topic(query_lower),
                confusion_detected=False,
                bloom_level="remember" if fast_path_result == Intent.FAST else "understand",
                teaching_strategy="direct",
                context_needed=["rag"] if fast_path_result not in [Intent.SYLLABUS] else ["syllabus"],
                scaffolding_hint="minimal",
                reasoning_trace="fast_path"
            )
        
        # Step 3: Use LLM for complex routing
        return self._llm_route(query, turn_number, previous_topic, previous_intent)
    
    def _detect_confusion(self, query: str) -> bool:
        """Check if query contains confusion signals."""
        for pattern in self.CONFUSION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _try_fast_path(self, query: str) -> Optional[Intent]:
        """Try to match fast-path patterns."""
        for intent, patterns in self.FAST_PATH_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent
        return None
    
    def _extract_topic(self, query: str) -> Optional[str]:
        """Extract AI/ML topic from query."""
        topic_patterns = {
            "gradient_descent": r"\b(gradient.?descent|learning.?rate|optimi[sz])\b",
            "backpropagation": r"\b(backprop|chain.?rule|error.?propagat)\b",
            "neural_network": r"\b(neural.?net|perceptron|hidden.?layer|deep.?learn)\b",
            "classification": r"\b(classif|decision.?tree|knn|svm)\b",
            "regression": r"\b(regress|linear.?model)\b",
            "clustering": r"\b(cluster|k-?means|unsupervised)\b",
        }
        
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return topic
        return None
    
    def _llm_route(
        self,
        query: str,
        turn_number: int,
        previous_topic: Optional[str],
        previous_intent: Optional[str],
    ) -> RoutingDecision:
        """Use LLM for routing decision."""
        prompt = self.ROUTING_PROMPT.format(
            query=query,
            turn_number=turn_number,
            previous_topic=previous_topic or "None",
            previous_intent=previous_intent or "None",
        )
        
        try:
            response = self.model.invoke(prompt)
            content = response.content.strip()
            
            # Parse JSON response
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            
            intent_map = {
                "fast": Intent.FAST,
                "explain": Intent.EXPLAIN,
                "tutor": Intent.TUTOR,
                "math": Intent.MATH,
                "coder": Intent.CODER,
                "syllabus_query": Intent.SYLLABUS,
            }
            
            return RoutingDecision(
                intent=intent_map.get(result.get("intent", "explain"), Intent.EXPLAIN),
                confidence=float(result.get("confidence", 0.5)),
                topic=result.get("topic"),
                confusion_detected=bool(result.get("confusion_detected", False)),
                bloom_level=result.get("bloom_level", "understand"),
                teaching_strategy=result.get("teaching_strategy", "progressive_disclosure"),
                context_needed=result.get("context_needed", ["rag"]),
                scaffolding_hint=result.get("scaffolding_hint", "standard"),
                reasoning_trace="llm_route"
            )
            
        except Exception as e:
            logger.error(f"LLM routing failed: {e}, falling back to explain")
            return RoutingDecision(
                intent=Intent.EXPLAIN,
                confidence=0.5,
                topic=self._extract_topic(query.lower()),
                confusion_detected=False,
                bloom_level="understand",
                teaching_strategy="progressive_disclosure",
                context_needed=["rag"],
                scaffolding_hint="standard",
                reasoning_trace=f"fallback_error: {str(e)}"
            )


def unified_router_node(state: dict) -> dict:
    """
    LangGraph node that replaces both reasoning_node and supervisor_node.
    
    This is the ONLY routing decision point in the graph.
    """
    router = UnifiedRouter()
    
    query = state.get("query", "")
    conversation_history = state.get("conversation_history", [])
    
    # Calculate turn info
    turn_number = len([m for m in conversation_history if m.get("role") == "user"]) + 1
    previous_topic = None
    previous_intent = None
    for msg in reversed(conversation_history):
        if msg.get("role") == "assistant":
            previous_topic = msg.get("metadata", {}).get("topic")
            previous_intent = msg.get("metadata", {}).get("intent")
            break
    
    # Get routing decision
    decision = router.route(
        query=query,
        conversation_history=conversation_history,
        turn_number=turn_number,
        previous_topic=previous_topic,
        previous_intent=previous_intent,
    )
    
    # Update state with routing decision
    state["intent"] = decision.intent.value
    state["routing_confidence"] = decision.confidence
    state["current_topic"] = decision.topic
    state["student_confusion_detected"] = decision.confusion_detected
    state["bloom_level"] = decision.bloom_level
    state["teaching_strategy"] = decision.teaching_strategy
    state["context_needed"] = decision.context_needed
    state["scaffolding_hint"] = decision.scaffolding_hint
    state["reasoning_trace"] = decision.reasoning_trace
    state["turn_number"] = turn_number
    
    # Set model based on intent
    model_mapping = {
        "fast": "gemini-flash",
        "explain": "gemini-flash",
        "tutor": "gemini-tutor",
        "math": "gemini-flash",
        "coder": "groq-llama-70b",
        "syllabus_query": "gemini-flash",
    }
    state["model_selected"] = model_mapping.get(decision.intent.value, "gemini-flash")
    
    logger.info(
        f"🔄 Unified Router: intent={decision.intent.value} "
        f"confidence={decision.confidence:.2f} "
        f"topic={decision.topic} "
        f"trace={decision.reasoning_trace}"
    )
    
    return state
```

---

## Migration Plan

### Phase 1: Create Unified Router (Non-Breaking)

1. Create `unified_router.py` (above)
2. Keep existing `reasoning_node.py` and `supervisor.py`
3. Add feature flag to switch between old and new

```python
# tutor_agent.py
USE_UNIFIED_ROUTER = os.getenv("USE_UNIFIED_ROUTER", "false").lower() == "true"

if USE_UNIFIED_ROUTER:
    # New: Single routing node
    graph.add_node("router", unified_router_node)
    graph.add_edge("governor", "router")
    graph.add_edge("router", "agent")
else:
    # Old: reasoning_node → supervisor
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_edge("governor", "reasoning")
    graph.add_edge("reasoning", "supervisor")
    graph.add_edge("supervisor", "agent")
```

### Phase 2: Test and Validate

Run A/B comparison:

```python
# test_router_parity.py

def test_routing_parity():
    """Ensure unified router makes same decisions as old system."""
    test_cases = [
        ("briefly what is ML", "fast"),
        ("explain gradient descent", "explain"),
        ("I don't understand backprop", "tutor"),
        ("when is the midterm", "syllabus_query"),
        ("derive the loss function", "math"),
        ("write python code for KNN", "coder"),
    ]
    
    old_router = OldRoutingSystem()
    new_router = UnifiedRouter()
    
    for query, expected in test_cases:
        old_result = old_router.route(query)
        new_result = new_router.route(query)
        
        assert old_result.intent == new_result.intent.value, \
            f"Mismatch for '{query}': old={old_result.intent}, new={new_result.intent.value}"
```

### Phase 3: Remove Old Code

Once validated:

```bash
# Remove redundant files
rm backend/app/agents/reasoning_node.py  # Merged into unified_router
# Keep supervisor.py but remove LLM classification (keep fast-path only for reference)
```

---

## Token Savings Calculation

| Operation | Old System | New System | Savings |
|-----------|------------|------------|---------|
| Intent classification | ~950 tokens | ~500 tokens | 450 tokens |
| Latency (LLM calls) | 2 calls | 1 call | 50% faster |
| Conflicts possible | Yes | No | 100% consistent |

**Per-query savings: ~450 tokens, 1 fewer LLM call**

At 1000 queries/day:
- Token savings: 450,000 tokens/day
- At $0.075/1M tokens (Gemini Flash): ~$33/day saved
- Latency improvement: ~500ms per query

---

## Files Summary

| File | Action |
|------|--------|
| `backend/app/agents/unified_router.py` | CREATE |
| `backend/app/agents/tutor_agent.py` | MODIFY (add feature flag) |
| `backend/app/agents/reasoning_node.py` | DEPRECATE then DELETE |
| `backend/app/agents/supervisor.py` | SIMPLIFY (remove LLM, keep regex) |
| `backend/tests/test_unified_router.py` | CREATE |
