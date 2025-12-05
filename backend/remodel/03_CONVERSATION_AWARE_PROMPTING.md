# Conversation-Aware Prompting

## The Problem

The current system treats every query as if it's a brand new conversation, even when it's turn 5 of an ongoing discussion. This leads to:

1. **Repetitive introductions**: "Gradient descent is an optimization algorithm..." on every turn
2. **Lost context**: Agent doesn't remember what was just explained
3. **Inappropriate scaffolding**: Full Socratic method on follow-ups that just need clarification
4. **Wasted tokens**: Re-explaining concepts the student just learned

---

## Current Flow (Broken)

```python
# chat.py - conversation_history is loaded but not used effectively
conversation_history = await get_conversation_history(chat_id, limit=10)

# tutor_agent.py - history passed through but prompts don't adapt
async def astream_agent(query, ..., conversation_history):
    initial_state = {
        "conversation_history": conversation_history,  # ← Present but ignored!
        # ... prompts are still static
    }
```

The `conversation_history` is available but:
- Not used to calculate turn number
- Not used to extract previous topic
- Not used to adjust response style
- Not used to avoid repetition

---

## Solution: Conversation State Machine

Implement a **ConversationStateTracker** that maintains context across turns:

```python
# NEW: backend/app/agents/conversation_tracker.py

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

class ConversationPhase(Enum):
    """What phase of learning is the student in?"""
    EXPLORING = "exploring"           # Just starting, asking what things are
    UNDERSTANDING = "understanding"   # Grasping concepts, asking how/why
    APPLYING = "applying"             # Trying to use knowledge
    DEBUGGING = "debugging"           # Stuck on something specific
    REVIEWING = "reviewing"           # Circling back to earlier topics

@dataclass
class ConversationState:
    """Tracks the state of an ongoing conversation."""
    turn_number: int = 0
    topics_discussed: List[str] = field(default_factory=list)
    current_topic: Optional[str] = None
    phase: ConversationPhase = ConversationPhase.EXPLORING
    scaffolding_history: List[str] = field(default_factory=list)  # What scaffolding levels we've used
    unanswered_questions: List[str] = field(default_factory=list)  # Questions we asked that weren't answered
    user_knowledge_signals: Dict[str, str] = field(default_factory=dict)  # topic -> "knows_basics", "confused", "advanced"
    last_response_type: Optional[str] = None  # "explanation", "example", "question", "clarification"
    last_response_length: int = 0

class ConversationTracker:
    """
    Tracks conversation state to enable context-aware responses.
    
    This solves the "every turn is the same" problem by maintaining
    awareness of what's been discussed and how the student is progressing.
    """
    
    # Topic extraction patterns
    TOPIC_PATTERNS = {
        "gradient_descent": r"\b(gradient.?descent|learning.?rate|optimi[sz]|step.?size)\b",
        "backpropagation": r"\b(backprop|chain.?rule|error.?propagat)\b",
        "neural_network": r"\b(neural.?net|perceptron|hidden.?layer|deep.?learn|mlp)\b",
        "classification": r"\b(classif|decision.?tree|knn|svm|categor)\b",
        "regression": r"\b(regress|linear.?model|predict.*(continuous|value))\b",
        "clustering": r"\b(cluster|k-?means|unsupervised|grouping)\b",
        "loss_function": r"\b(loss|cost.?function|mse|cross.?entropy|error.?function)\b",
        "activation": r"\b(activation|relu|sigmoid|tanh|softmax)\b",
        "overfitting": r"\b(overfit|underfit|regulariz|dropout|validation)\b",
    }
    
    # Phase detection patterns
    PHASE_PATTERNS = {
        ConversationPhase.EXPLORING: [
            r"\bwhat is\b", r"\bwhat are\b", r"\bdefine\b", r"\bexplain\b",
            r"\btell me about\b", r"\bwhat does .* mean\b"
        ],
        ConversationPhase.UNDERSTANDING: [
            r"\bhow does\b", r"\bwhy does\b", r"\bwhat happens when\b",
            r"\bcan you explain why\b", r"\bi don't understand\b"
        ],
        ConversationPhase.APPLYING: [
            r"\bhow do i\b", r"\bhow can i\b", r"\bimplement\b",
            r"\bcode\b", r"\bexample\b", r"\bpractice\b"
        ],
        ConversationPhase.DEBUGGING: [
            r"\bwhy isn't\b", r"\berror\b", r"\bwrong\b", r"\bnot working\b",
            r"\bstuck\b", r"\bhelp me with\b"
        ],
        ConversationPhase.REVIEWING: [
            r"\bearlier\b", r"\bbefore\b", r"\bback to\b", r"\bremember when\b",
            r"\byou said\b", r"\bwhat was\b"
        ]
    }
    
    def analyze_conversation(
        self,
        current_query: str,
        conversation_history: List[dict]
    ) -> ConversationState:
        """
        Analyze the full conversation to build state.
        
        Args:
            current_query: The user's current message
            conversation_history: List of {role, content, metadata} dicts
            
        Returns:
            ConversationState with full context
        """
        state = ConversationState()
        
        # Count turns (user messages only)
        user_messages = [m for m in conversation_history if m.get("role") == "user"]
        state.turn_number = len(user_messages) + 1  # +1 for current query
        
        # Extract topics from all messages
        all_text = " ".join([m.get("content", "") for m in conversation_history])
        all_text += " " + current_query
        state.topics_discussed = self._extract_topics(all_text)
        state.current_topic = self._extract_topics(current_query)[-1] if self._extract_topics(current_query) else None
        
        # Detect conversation phase
        state.phase = self._detect_phase(current_query)
        
        # Track scaffolding history from metadata
        for msg in conversation_history:
            if msg.get("role") == "assistant":
                scaffolding = msg.get("metadata", {}).get("scaffolding_level")
                if scaffolding:
                    state.scaffolding_history.append(scaffolding)
        
        # Detect user knowledge signals
        state.user_knowledge_signals = self._detect_knowledge_signals(conversation_history, current_query)
        
        # Get last response info
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant":
                state.last_response_type = self._classify_response_type(msg.get("content", ""))
                state.last_response_length = len(msg.get("content", ""))
                break
        
        return state
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract AI/ML topics mentioned in text."""
        topics = []
        text_lower = text.lower()
        for topic, pattern in self.TOPIC_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                if topic not in topics:
                    topics.append(topic)
        return topics
    
    def _detect_phase(self, query: str) -> ConversationPhase:
        """Detect what learning phase the student is in."""
        query_lower = query.lower()
        
        for phase, patterns in self.PHASE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return phase
        
        return ConversationPhase.EXPLORING
    
    def _detect_knowledge_signals(
        self,
        history: List[dict],
        current_query: str
    ) -> Dict[str, str]:
        """
        Detect signals about what the student knows.
        
        Returns dict of topic -> knowledge_level
        """
        signals = {}
        
        # Confusion signals suggest they need more help
        confusion_patterns = [
            r"\bi don't understand\b",
            r"\bconfused about\b",
            r"\bwhat do you mean\b",
            r"\bcan you explain .* again\b",
        ]
        
        # Competence signals suggest they know basics
        competence_patterns = [
            r"\bi know that\b",
            r"\bi understand .* but\b",
            r"\bbuilding on\b",
            r"\bso .* means\b",  # Paraphrasing
        ]
        
        all_user_text = " ".join([
            m.get("content", "") for m in history if m.get("role") == "user"
        ]) + " " + current_query
        
        # Check each topic
        for topic in self._extract_topics(all_user_text):
            # Default to unknown
            signals[topic] = "unknown"
            
            # Look for confusion about this topic
            for pattern in confusion_patterns:
                if re.search(pattern, all_user_text.lower()):
                    signals[topic] = "confused"
                    break
            
            # Look for competence signals
            for pattern in competence_patterns:
                if re.search(pattern, all_user_text.lower()):
                    if signals[topic] != "confused":  # Confusion overrides
                        signals[topic] = "knows_basics"
        
        return signals
    
    def _classify_response_type(self, response: str) -> str:
        """Classify what type of response was given."""
        response_lower = response.lower()
        
        if "?" in response and response.count("?") > 2:
            return "socratic_questions"
        elif "example" in response_lower or "for instance" in response_lower:
            return "example"
        elif "```" in response:
            return "code"
        elif response.count("$") > 2 or "\\frac" in response:
            return "math"
        elif len(response) < 300:
            return "brief"
        else:
            return "explanation"
    
    def should_skip_intro(self, state: ConversationState, topic: str) -> bool:
        """
        Determine if we should skip introductory explanation for a topic.
        
        Returns True if:
        - Topic was discussed in this conversation
        - We gave a full explanation recently
        - User showed competence signals
        """
        if topic in state.topics_discussed[:-1]:  # Discussed before current turn
            return True
        
        if state.user_knowledge_signals.get(topic) == "knows_basics":
            return True
        
        # If we just gave a long explanation and they're asking follow-up
        if state.last_response_type == "explanation" and state.last_response_length > 800:
            return True
        
        return False
    
    def get_response_guidance(self, state: ConversationState, query: str) -> str:
        """
        Generate specific guidance for the response based on conversation state.
        """
        guidance_parts = []
        
        # Turn-based guidance
        if state.turn_number == 1:
            guidance_parts.append("This is the start of the conversation. Give a complete but not overwhelming introduction.")
        elif state.turn_number <= 3:
            guidance_parts.append("Early in conversation. The student is still orienting. Be helpful but not verbose.")
        else:
            guidance_parts.append("Established conversation. The student knows the context. Be direct and build on what's discussed.")
        
        # Phase-based guidance
        phase_guidance = {
            ConversationPhase.EXPLORING: "Student is exploring. Provide clear explanations without assuming prior knowledge.",
            ConversationPhase.UNDERSTANDING: "Student is trying to understand deeply. Focus on 'why' and 'how', not just 'what'.",
            ConversationPhase.APPLYING: "Student wants to apply knowledge. Give practical guidance, examples, and code if relevant.",
            ConversationPhase.DEBUGGING: "Student is stuck. Be diagnostic. Ask clarifying questions if needed.",
            ConversationPhase.REVIEWING: "Student is reviewing. Help them connect to what was discussed earlier.",
        }
        guidance_parts.append(phase_guidance.get(state.phase, ""))
        
        # Topic continuity guidance
        if state.current_topic and state.current_topic in state.topics_discussed[:-1]:
            guidance_parts.append(f"'{state.current_topic}' was already discussed. Don't re-explain basics. Build on previous explanation.")
        
        # Response type variation
        if state.last_response_type == "explanation" and len(state.scaffolding_history) >= 2:
            guidance_parts.append("You've given multiple explanations. Consider using a different approach: example, analogy, or question.")
        
        return "\n".join([f"- {g}" for g in guidance_parts if g])


def build_conversation_context_prompt(
    tracker: ConversationTracker,
    query: str,
    conversation_history: List[dict]
) -> str:
    """
    Build a prompt section that gives the LLM conversation context.
    
    This replaces the static prompts with dynamic, context-aware instructions.
    """
    state = tracker.analyze_conversation(query, conversation_history)
    guidance = tracker.get_response_guidance(state, query)
    
    # Build conversation summary
    if state.turn_number == 1:
        conversation_summary = "This is a new conversation."
    else:
        topics_str = ", ".join(state.topics_discussed) if state.topics_discussed else "general"
        conversation_summary = f"""
Conversation turn: {state.turn_number}
Topics discussed so far: {topics_str}
Current topic: {state.current_topic or "unclear"}
Learning phase: {state.phase.value}
Last response type: {state.last_response_type or "none"}
"""
    
    return f"""
## Conversation Context
{conversation_summary}

## Response Guidance
{guidance}

## Anti-Repetition Rules
1. {'Do NOT re-explain ' + state.current_topic + ' from basics - it was just discussed' if state.current_topic and tracker.should_skip_intro(state, state.current_topic) else 'Topic is new - introduce it clearly'}
2. {'Previous response was long and detailed - be more concise now' if state.last_response_length > 1000 else 'Length should match complexity of question'}
3. {'User seems confused - provide more scaffolding and examples' if "confused" in state.user_knowledge_signals.values() else 'User seems to be following - proceed at pace'}
"""
```

---

## Integration with Existing System

### Update `astream_agent()` in `tutor_agent.py`:

```python
from app.agents.conversation_tracker import ConversationTracker, build_conversation_context_prompt

async def astream_agent(query, user_id, user_email, session_id, chat_id, conversation_history):
    # NEW: Analyze conversation state
    tracker = ConversationTracker()
    conv_state = tracker.analyze_conversation(query, conversation_history)
    conv_context_prompt = build_conversation_context_prompt(tracker, query, conversation_history)
    
    initial_state = {
        "query": query,
        "user_id": user_id,
        "user_email": user_email,
        "conversation_history": conversation_history,
        
        # NEW: Conversation tracking fields
        "turn_number": conv_state.turn_number,
        "current_topic": conv_state.current_topic,
        "topics_discussed": conv_state.topics_discussed,
        "conversation_phase": conv_state.phase.value,
        "conversation_context_prompt": conv_context_prompt,  # Inject into prompts
        
        # ... rest of state
    }
```

### Update `agent_node()` to use conversation context:

```python
def agent_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "fast")
    
    # Get conversation-aware context
    conv_context = state.get("conversation_context_prompt", "")
    
    # Build the full prompt with conversation awareness
    base_prompt = f"""You are Course Marshal, an AI tutor for COMP 237.

{conv_context}

## Your Task
Respond to the student's question, following the guidance above.
If this is a follow-up, don't repeat what you already explained.
Match response length and depth to what the student needs right now.

## Student Query
{state.get("query", "")}
"""
    
    # Add intent-specific additions (but NOT rigid structure!)
    if intent == "math":
        base_prompt += "\n\nInclude mathematical notation where helpful. Use LaTeX format."
    elif intent == "tutor" and state.get("student_confusion_detected"):
        base_prompt += "\n\nStudent seems confused. Use additional scaffolding and check understanding."
    
    # ... rest of agent_node
```

---

## Example: Before vs After

### Conversation Flow

**Turn 1**: "explain gradient descent"
**Turn 2**: "can you go deeper?"
**Turn 3**: "what about the learning rate specifically?"

### BEFORE (No Conversation Awareness)

**Turn 1 Response**:
```
**What it is**: Gradient descent is an optimization algorithm...
**How it works**: It iteratively adjusts parameters...
**Example**: In neural networks...
**Key point**: It finds the minimum by going downhill.

Would you like me to go deeper?
```

**Turn 2 Response** (User said "go deeper"):
```
**What it is**: Gradient descent is an optimization algorithm... [REPEATED]
**How it works**: It iteratively adjusts parameters... [REPEATED]
**Example**: Consider a more complex example... [SLIGHTLY DIFFERENT]
**Key point**: The key insight is... [SAME STRUCTURE]

Would you like me to go deeper?
```

**Turn 3 Response** (Learning rate question):
```
**What it is**: The learning rate is a hyperparameter... [FULL INTRO AGAIN]
**How it works**: It controls the step size...
**Example**: ...
**Key point**: ...

Would you like me to go deeper?
```

### AFTER (Conversation Aware)

**Turn 1 Response**:
```
Gradient descent is how machine learning models learn - it's the optimization algorithm that adjusts weights to minimize prediction error.

Imagine you're blindfolded on a hilly terrain trying to find the lowest valley. You can feel which way is downhill with your feet, so you take a step in that direction. Then feel again, step again. Eventually you reach the bottom.

Mathematically, at each step we:
1. Calculate the gradient (slope) of our loss function
2. Move our parameters in the opposite direction (downhill)
3. Repeat until we converge

The update rule: w_new = w_old - α × ∇L

Where α is the learning rate - a crucial hyperparameter we'll discuss if you want to go deeper.
```

**Turn 2 Response** (Context: already explained basics):
```
Let's go deeper into the mechanics.

The gradient ∇L is computed using calculus - specifically partial derivatives with respect to each parameter:

$$\nabla L = \left[ \frac{\partial L}{\partial w_1}, \frac{\partial L}{\partial w_2}, ... \right]$$

For neural networks, this gets computed via backpropagation (chain rule through all layers).

Key considerations:
- **Batch size**: Do we compute gradient on all data (batch), one sample (stochastic), or chunks (mini-batch)?
- **Learning rate**: How big are our steps?
- **Momentum**: Do we build up "velocity" to escape local minima?

The course materials cover SGD variants in the optimization module. Want me to focus on any of these aspects?
```

**Turn 3 Response** (Context: now asking about learning rate, previously mentioned):
```
The learning rate α is probably the most important hyperparameter to get right.

Remember from our update rule: w_new = w_old - α × ∇L

If α is too small:
- Learning is stable but painfully slow
- May take thousands of epochs to converge
- Good for fine-tuning

If α is too large:
- Learning is fast but unstable
- Can overshoot the minimum and oscillate
- May even diverge (loss goes to infinity!)

**Practical approach in COMP 237:**
1. Start with α = 0.01 (common default)
2. If loss oscillates: reduce by factor of 10
3. If learning is too slow: increase by factor of 2-3
4. Use learning rate schedulers to reduce α as training progresses

Your course materials show this tradeoff visually in the loss landscape diagrams.
```

---

## Success Metrics

| Metric | Before | After Target |
|--------|--------|--------------|
| Turn 2 repeats Turn 1 content | ~80% | <20% |
| "What it is" section on follow-ups | 100% | <10% |
| Response adapts to "go deeper" | No | Yes |
| Previous topic referenced | Never | When relevant |
| Learning phase detected | N/A | Yes |

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/agents/conversation_tracker.py` | CREATE | New ConversationTracker class |
| `backend/app/agents/tutor_agent.py` | MODIFY | Integrate tracker into astream_agent |
| `backend/app/agents/state.py` | MODIFY | Add conversation state fields |
| `backend/tests/test_conversation_tracking.py` | CREATE | Test conversation awareness |
