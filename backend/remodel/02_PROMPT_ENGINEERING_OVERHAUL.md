# Prompt Engineering Overhaul

## The Problem

Current prompts in `SYSTEM_PROMPTS` dictionary force **rigid, identical response structures** regardless of:
- Query complexity
- Conversation context  
- Student's prior knowledge
- Whether it's a follow-up question

### Current Problematic Prompts

```python
# tutor_agent.py - Line ~120
SYSTEM_PROMPTS = {
    "explain": """You are Course Marshal...
    3. Structure your response like this:
       - **What it is**: 1-2 sentence definition      # <-- ALWAYS same structure
       - **How it works**: Brief explanation (2-3 sentences)
       - **Example**: One concrete example from the course materials
       - **Key point**: 1 sentence summary
    4. End with: "Would you like me to go deeper..."  # <-- ALWAYS same ending
    """,
    
    "fast": """...
    Keep your response under 3 sentences.            # <-- Good length constraint
    Don't ask follow-up questions.                   # <-- Good, but too rigid
    """,
    
    "tutor": """You are Course Marshal...
    - **Activation:** [Connect to prior knowledge]   # <-- Same structure every time
    - **Exploration:** [Socratic questions]
    - **Guidance:** [Progressive hints]
    - **Challenge:** [Closing question]
    """
}
```

---

## The Solution: Dynamic Prompt Templates

Replace rigid structures with **adaptive prompt templates** that consider:

1. **Conversation Turn Number** - First turn vs follow-up
2. **Prior Response Type** - What did we just explain?
3. **Detected Complexity** - Simple definition vs complex concept
4. **User Signals** - "briefly", "in detail", "I'm confused"

### New Prompt Architecture

```python
# NEW: backend/app/agents/prompt_builder.py

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

class ResponseMode(Enum):
    FIRST_TOUCH = "first_touch"       # First time discussing this topic
    FOLLOW_UP = "follow_up"           # Continuing previous discussion
    CLARIFICATION = "clarification"   # User asked for clarification
    DEEP_DIVE = "deep_dive"           # User explicitly asked for more detail
    QUICK_ANSWER = "quick_answer"     # User wants brevity

@dataclass
class ConversationContext:
    turn_number: int
    previous_topic: Optional[str]
    previous_response_type: Optional[str]
    user_depth_preference: Optional[str]
    scaffolding_level: Optional[str]
    detected_confusion: bool

class PromptBuilder:
    """
    Builds adaptive prompts based on conversation context.
    
    Instead of: "Always structure as What/How/Example/Key point"
    Does: "Adapt structure based on what user needs right now"
    """
    
    BASE_IDENTITY = """You are Course Marshal, an AI tutor for COMP 237: Introduction to AI.
You adapt your teaching style based on the student's needs and the conversation flow.
You prioritize course materials over general knowledge.
You never give complete solutions for graded assignments."""

    def build_prompt(
        self,
        intent: str,
        context: ConversationContext,
        retrieved_sources: List[dict],
        query: str
    ) -> str:
        """Build a context-aware prompt."""
        
        # Determine response mode
        mode = self._determine_mode(context, query)
        
        # Get mode-specific instructions
        mode_instructions = self._get_mode_instructions(mode, context)
        
        # Get intent-specific guidance (NOT structure)
        intent_guidance = self._get_intent_guidance(intent)
        
        # Build source context
        source_context = self._format_sources(retrieved_sources)
        
        return f"""{self.BASE_IDENTITY}

## Current Conversation State
- Turn: {context.turn_number}
- Mode: {mode.value}
- Previous topic: {context.previous_topic or 'None (new conversation)'}
- User preference: {context.user_depth_preference or 'Not stated'}
- Confusion detected: {'Yes - provide more scaffolding' if context.detected_confusion else 'No'}

## Response Guidelines
{mode_instructions}

## Teaching Approach
{intent_guidance}

## Retrieved Course Materials
{source_context}

## Important Rules
1. NEVER repeat information you just gave in the previous turn
2. If this is a follow-up, BUILD on what was said, don't restart
3. Cite sources naturally: "According to the course materials..." or "In the COMP 237 syllabus..."
4. If you don't know something, say so - don't make up information
5. Match response length to complexity and user signals

## Student Query
{query}

Respond naturally as an expert tutor would, adapting to the conversation flow:"""

    def _determine_mode(self, context: ConversationContext, query: str) -> ResponseMode:
        """Determine response mode from context and query."""
        query_lower = query.lower()
        
        # Quick answer signals
        if any(kw in query_lower for kw in ["briefly", "quick", "short", "one sentence", "tldr"]):
            return ResponseMode.QUICK_ANSWER
        
        # Deep dive signals  
        if any(kw in query_lower for kw in ["more detail", "go deeper", "explain more", "elaborate", "in depth"]):
            return ResponseMode.DEEP_DIVE
        
        # Clarification signals
        if any(kw in query_lower for kw in ["what do you mean", "clarify", "don't understand", "confused"]):
            return ResponseMode.CLARIFICATION
        
        # Check if this is a follow-up on same topic
        if context.turn_number > 1 and context.previous_topic:
            # Heuristic: if query is short and doesn't introduce new topic
            if len(query.split()) < 10:
                return ResponseMode.FOLLOW_UP
        
        return ResponseMode.FIRST_TOUCH

    def _get_mode_instructions(self, mode: ResponseMode, context: ConversationContext) -> str:
        """Get mode-specific instructions."""
        
        if mode == ResponseMode.QUICK_ANSWER:
            return """
**Quick Answer Mode**
- Give a direct, concise answer (1-3 sentences)
- Skip scaffolding and examples unless essential
- End with a brief offer: "Want more detail?" (don't elaborate further)
"""
        
        if mode == ResponseMode.FOLLOW_UP:
            return f"""
**Follow-Up Mode** (continuing from previous turn)
- DO NOT redefine or re-explain "{context.previous_topic}"
- Build on what was already discussed
- Add new information, examples, or perspectives
- If the student asks "more", give the NEXT level of detail, not the same level again
- Response should feel like a continuation, not a new lecture
"""
        
        if mode == ResponseMode.CLARIFICATION:
            return """
**Clarification Mode** (student expressed confusion)
- Identify what aspect is confusing
- Offer an alternative explanation or analogy
- Use simpler language than before
- Ask a check-in question: "Does that make more sense?"
"""
        
        if mode == ResponseMode.DEEP_DIVE:
            return """
**Deep Dive Mode** (student wants more detail)
- Provide comprehensive explanation
- Include technical details, math if relevant
- Give multiple examples
- Cover edge cases and nuances
- It's OK to be longer here - the student asked for depth
"""
        
        # FIRST_TOUCH
        return """
**First Touch Mode** (new topic introduction)
- Start with a clear, accessible explanation
- Gauge complexity from the question
- Provide ONE good example
- End with an invitation to explore further (but don't force it)
- Length: Match the apparent complexity of the question
"""

    def _get_intent_guidance(self, intent: str) -> str:
        """Get intent-specific guidance (not structure!)."""
        
        guidance = {
            "explain": """
Focus on building understanding. Use analogies if helpful.
Don't just define - help the student grasp WHY this concept matters.
Connect to other concepts they've likely learned.""",
            
            "tutor": """
Use Socratic method when appropriate - ask guiding questions.
But don't FORCE questions if the student just needs information.
Scaffold based on detected confusion level.
If they're not confused, don't treat them like they are.""",
            
            "math": """
Focus on mathematical intuition first, then formalism.
Show step-by-step derivations when relevant.
Use LaTeX for equations: $equation$ for inline, $$equation$$ for blocks.
Explain what each step means, not just how to do it.""",
            
            "syllabus_query": """
Give direct, factual answers about course logistics.
Cite specific dates, policies, or requirements.
Be brief - students asking about logistics want quick answers.""",
            
            "fast": """
Maximum brevity. Direct answer only.
No scaffolding, no examples, no follow-up questions.
If more context is needed, the student will ask.""",
            
            "coder": """
Provide guidance, not complete solutions.
Explain the approach conceptually first.
For graded work, give hints and let them implement.
For learning exercises, you can show more code."""
        }
        
        return guidance.get(intent, guidance["explain"])

    def _format_sources(self, sources: List[dict]) -> str:
        """Format retrieved sources for the prompt."""
        if not sources:
            return "No course materials retrieved. Use your knowledge but note this limitation."
        
        formatted = []
        for i, source in enumerate(sources[:5], 1):  # Max 5 sources
            content = source.get("content", source.get("text", ""))[:500]
            filename = source.get("source_filename") or source.get("source_file") or "Unknown"
            score = source.get("relevance_score", 0.0)
            
            formatted.append(f"""
[Source {i}: {filename}] (relevance: {score:.2f})
{content}
---""")
        
        return "\n".join(formatted)
```

---

## Integration Points

### 1. Update `tutor_agent.py`

Replace `SYSTEM_PROMPTS` dictionary usage with `PromptBuilder`:

```python
# OLD (tutor_agent.py line ~200)
def agent_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "fast")
    system_prompt = SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["explain"])
    # ... uses static prompt

# NEW
from app.agents.prompt_builder import PromptBuilder, ConversationContext

def agent_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "fast")
    
    # Build conversation context
    context = ConversationContext(
        turn_number=_calculate_turn_number(state),
        previous_topic=_extract_previous_topic(state),
        previous_response_type=state.get("previous_intent"),
        user_depth_preference=state.get("user_depth_preference"),
        scaffolding_level=state.get("scaffolding_level"),
        detected_confusion=state.get("student_confusion_detected", False)
    )
    
    # Build adaptive prompt
    builder = PromptBuilder()
    system_prompt = builder.build_prompt(
        intent=intent,
        context=context,
        retrieved_sources=state.get("retrieved_context", []),
        query=state.get("query", "")
    )
    
    # ... rest of agent_node
```

### 2. Update `state.py`

Add conversation tracking fields:

```python
class AgentState(TypedDict):
    # ... existing fields ...
    
    # NEW: Conversation tracking
    turn_number: Optional[int]  # Which turn in the conversation
    previous_topic: Optional[str]  # Topic from previous turn
    previous_intent: Optional[str]  # Intent from previous turn
    previous_response_length: Optional[int]  # Chars in previous response
```

### 3. Update `astream_agent()`

Calculate turn number from conversation history:

```python
async def astream_agent(query, user_id, user_email, session_id, chat_id, conversation_history):
    # Calculate turn number
    turn_number = len([m for m in conversation_history if m.get("role") == "user"]) + 1
    
    # Extract previous topic from last assistant message
    previous_topic = None
    previous_intent = None
    if conversation_history:
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant":
                # Could use LLM to extract topic, or simpler heuristics
                previous_topic = _extract_topic_from_message(msg.get("content", ""))
                previous_intent = msg.get("metadata", {}).get("intent")
                break
    
    initial_state = {
        # ... existing fields ...
        "turn_number": turn_number,
        "previous_topic": previous_topic,
        "previous_intent": previous_intent,
        "conversation_history": conversation_history,
    }
```

---

## Before/After Examples

### Example 1: Simple Explanation

**Query**: "explain gradient descent"

**BEFORE** (Rigid Structure):
```
**What it is**: Gradient descent is an optimization algorithm used to minimize a loss function.

**How it works**: The algorithm iteratively adjusts parameters by moving in the direction opposite to the gradient of the loss function. At each step, it calculates the gradient and updates the parameters using a learning rate.

**Example**: In COMP 237, when training a neural network to recognize digits, gradient descent adjusts the weights to minimize the difference between predicted and actual labels.

**Key point**: Gradient descent finds the minimum of a function by taking small steps downhill.

Would you like me to go deeper or try a practice problem?
```

**AFTER** (Adaptive):
```
Gradient descent is how neural networks learn - it's the algorithm that adjusts weights to make predictions more accurate.

Think of it like finding the lowest point in a valley while blindfolded. You can't see the bottom, but you can feel which way is downhill. You take a step in that direction, feel again, step again. Eventually you reach the bottom.

In mathematical terms: you calculate the gradient (slope) of the loss function, then move your parameters in the opposite direction. The "learning rate" controls how big each step is.

The course materials cover this in the optimization module - want me to walk through the math, or is this intuition enough for now?
```

### Example 2: Follow-Up Question

**Turn 1**: "explain gradient descent"  
**Turn 2**: "go deeper"

**BEFORE** (Same Structure Again):
```
**What it is**: Gradient descent is an iterative optimization algorithm...

**How it works**: The algorithm computes partial derivatives... [REPEATS everything]

**Example**: Consider a neural network... [SAME example style]

**Key point**: The key insight is... [SAME ending]
```

**AFTER** (Builds On Previous):
```
Let's get into the math.

The gradient ∇L is a vector of partial derivatives - one for each parameter:

$$\nabla L = \left[ \frac{\partial L}{\partial w_1}, \frac{\partial L}{\partial w_2}, ..., \frac{\partial L}{\partial w_n} \right]$$

The update rule is: $w_{new} = w_{old} - \alpha \cdot \nabla L$

Where $\alpha$ is the learning rate. This is where it gets interesting:
- Too small: takes forever to converge
- Too large: overshoots and oscillates (or diverges!)

The course materials show this tradeoff in the perceptron training examples. There's also a neat visualization of how different learning rates affect convergence paths.

Want me to work through a concrete example with numbers?
```

---

## Testing the Change

Create test cases that verify adaptive behavior:

```python
# test_prompt_builder.py

def test_first_touch_vs_followup():
    """Ensure follow-up prompts don't repeat intro material."""
    builder = PromptBuilder()
    
    # First touch
    first_prompt = builder.build_prompt(
        intent="explain",
        context=ConversationContext(turn_number=1, previous_topic=None, ...),
        ...
    )
    assert "new topic introduction" in first_prompt.lower()
    
    # Follow-up
    followup_prompt = builder.build_prompt(
        intent="explain", 
        context=ConversationContext(turn_number=2, previous_topic="gradient descent", ...),
        ...
    )
    assert "DO NOT redefine" in followup_prompt
    assert "gradient descent" in followup_prompt

def test_quick_answer_mode():
    """Ensure 'briefly' triggers concise mode."""
    builder = PromptBuilder()
    
    prompt = builder.build_prompt(
        intent="explain",
        context=ConversationContext(...),
        query="briefly, what is backpropagation?"
    )
    assert "Quick Answer Mode" in prompt
    assert "1-3 sentences" in prompt

def test_confusion_increases_scaffolding():
    """Ensure confusion detection changes prompt."""
    builder = PromptBuilder()
    
    normal_prompt = builder.build_prompt(
        context=ConversationContext(detected_confusion=False, ...),
        ...
    )
    
    confused_prompt = builder.build_prompt(
        context=ConversationContext(detected_confusion=True, ...),
        ...
    )
    
    assert "more scaffolding" in confused_prompt
    assert "more scaffolding" not in normal_prompt
```

---

## Migration Path

1. **Create `prompt_builder.py`** with new PromptBuilder class
2. **Add state fields** for conversation tracking
3. **Update `astream_agent()`** to calculate turn number and previous topic
4. **Update `agent_node()`** to use PromptBuilder instead of SYSTEM_PROMPTS
5. **Keep SYSTEM_PROMPTS as fallback** during transition
6. **Test extensively** with conversation simulation
7. **Remove SYSTEM_PROMPTS** once confident

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Response structure variety | 1 pattern | 5+ patterns |
| Follow-up response similarity to first | 90%+ | <40% |
| User complaints about repetition | Common | Rare |
| "Would you like me to..." ending frequency | 100% | <30% |
