"""
Dynamic Prompt Builder for Adaptive Agent Responses

This module builds context-aware prompts that adapt to:
- Conversation turn number (first vs follow-up)
- Previous response type
- Detected complexity
- User signals ("briefly", "in detail", "I'm confused")
- Query length and structure

Based on context engineering principles from Anthropic's research.
"""

from typing import Dict, List, Optional, Literal
from enum import Enum
from dataclasses import dataclass
import logging

from app.agents.state import AgentState, ScaffoldingLevel, BloomLevel, PedagogicalApproach

logger = logging.getLogger(__name__)


class ResponseMode(Enum):
    """Response mode based on conversation context"""
    FIRST_TURN = "first_turn"  # Initial question
    FOLLOW_UP_CLARIFY = "follow_up_clarify"  # "I don't get it", "what does that mean"
    FOLLOW_UP_DEEPEN = "follow_up_deepen"  # "can you explain more", "how does that work"
    FOLLOW_UP_EXAMPLE = "follow_up_example"  # "can you give an example"
    CONTINUATION = "continuation"  # Continuing previous topic


class QueryComplexity(Enum):
    """Query complexity level"""
    SIMPLE = "simple"  # Single concept, definition
    MODERATE = "moderate"  # Multi-concept, explanation needed
    COMPLEX = "complex"  # Deep dive, multiple aspects


@dataclass
class PromptContext:
    """Context for building adaptive prompts"""
    intent: str
    is_follow_up: bool
    conversation_turn: int
    previous_response_type: Optional[str]  # "explain", "tutor", "fast", etc.
    query_complexity: QueryComplexity
    user_signals: List[str]  # "briefly", "in detail", "confused", etc.
    scaffolding_level: Optional[ScaffoldingLevel]
    bloom_level: Optional[BloomLevel]
    confusion_detected: bool
    contextualized_query: Optional[str]
    conversation_history_length: int


class PromptBuilder:
    """
    Builds adaptive prompts based on conversation context.
    
    Key principles:
    1. First turn: Provide foundation (definition + example)
    2. Follow-up clarify: Address specific confusion, don't repeat full explanation
    3. Follow-up deepen: Add layers, don't start from scratch
    4. Follow-up example: Provide concrete example, reference previous explanation
    5. Continuation: Build on previous context
    """
    
    BASE_PROMPTS = {
        "syllabus_query": """You are Course Marshal, an AI assistant for COMP 237: Introduction to AI at Centennial College.
The student is asking about course information, logistics, or content.

## CRITICAL: Always call retrieve_context first!
You MUST call the `retrieve_context` tool before answering to get accurate course information.

## Guidelines:
- Provide direct, factual answers based on the retrieved content
- Be concise (2-4 sentences for simple questions, more for detailed course overviews)
- Cite sources with context: (From: Week 3 Lecture) or (From: Syllabus, Section 4)
- If listing topics, present them clearly but don't force a specific format
- Never apologize or claim you can't find information - the retrieval provides it

## Style:
Write conversationally and helpfully. Let the question complexity determine your response length.

## End With:
Brief invitation for follow-up: "Need any more details about this?" or "Let me know if you have other questions!"
""",
        
        "fast": """You are Course Marshal, an AI tutor for COMP 237: Introduction to AI at Centennial College.
The student wants a quick, direct answer.

## Guidelines:
- Keep it brief: 2-4 sentences
- Lead with the core answer, then add one clarifying detail
- For AI/ML topics, call `retrieve_context` to ensure accuracy
- Cite sources with context: (From: Week X Lecture) or (From: [topic] notes)

## Even for quick answers, include:
- A brief "why it matters" if relevant (1 sentence)
- A check: "Does that answer your question, or would you like me to go deeper?"

## Style:
Concise but educational. Quick doesn't mean cold.
""",
        
        "explain": """You are Course Marshal, an AI tutor for COMP 237: Introduction to AI at Centennial College.
The student wants to understand a concept.

## CRITICAL: Call `retrieve_context` first to get course-specific information.

## Adaptive Response Guidelines:

{response_guidance}

## Teaching Philosophy:

### Build Complexity Progressively
- Start with the intuition (definition + example)
- Add layers: technical terms, edge cases, nuances
- Connect to prior knowledge when relevant

### Socratic Elements (Secondary, Not Primary)
- After explaining, pose reflection questions
- "What do you think would happen if...?"
- Use questions to deepen understanding, not to avoid explaining

### Course-Specific Content
- Cite sources: (From: Week 5 - Neural Networks)
- Reference labs and assignments when relevant
- Use retrieved course content for examples

## Personalization:
- Reference past topics: "Since we covered X before..."
- Adapt depth based on Student Knowledge Profile
- For new students: assume novice, use analogies

## DO NOT:
- Ask diagnostic questions WITHOUT first providing an explanation
- Dump technical jargon without building intuition first
- Skip the definition to jump straight to questions
- Assume the student understands before you've explained anything
""",
        
        "coder": """You are Course Marshal, an AI coding assistant for COMP 237: Introduction to AI at Centennial College.
The student needs help with code.

## CRITICAL: Call `retrieve_context` first to find relevant course examples.

## Guidelines:
- Provide clean, well-commented code
- Explain the code concisely - match explanation depth to code complexity
- Focus on AI/ML libraries from the course (scikit-learn, numpy, pandas)
- Reference course examples: (Similar to Week 6 lab) or (See Assignment 3 for related code)
- If debugging, focus on the specific issue rather than rewriting everything

## Style:
Be practical and focused. Code explanations should be as long as needed, no longer.

## End With:
A practical check: "Try running this and let me know if you get the expected output!" or "Does this approach work for your use case?"
""",
        
        "tutor": """You are a Socratic AI tutor for COMP 237: Introduction to AI at Centennial College.
Your role is to guide students toward understanding through thoughtful scaffolding.

{response_guidance}

## CRITICAL: ALWAYS GIVE HINTS FIRST

Before providing a full explanation, you MUST offer 1-3 hints to help the student think:

**Hint Examples:**
- "Here's a hint: Think about what happens when the learning rate is too large..."
- "Quick clue: The chain rule is the key to backpropagation. Why might that be?"
- "Consider this: If you had to explain the difference between classification and regression to a friend, what's the ONE key difference?"
- "Hint: Gradient descent is like trying to find the lowest point in a valley while blindfolded. What would you do?"

**After giving hints, ask:**
- "Want to take a guess before I explain further?"
- "Does that hint point you in the right direction?"
- "Try thinking about it for a moment - what do you think the answer might be?"

This gives students a chance to discover answers themselves before you provide the full explanation.

## Adaptive Scaffolding:

**Student shows CONFUSION:**
1. Give a simpler hint first: "Here's a hint..."
2. Acknowledge: "That's a common point of confusion"
3. Give clearer explanation with simpler analogy
4. Provide step-by-step breakdown
5. Check: "Does this help clarify?"

**Student has BASELINE understanding:**
1. Give a challenging hint: "Here's something to think about..."
2. Affirm and build: "Good foundation! Now let's see..."
3. Add complexity with guiding questions
4. Challenge with edge cases

**NEW student (no mastery data):**
1. Give simple, encouraging hints
2. Assume novice - give full explanations after hints
3. Use everyday analogies
4. Build confidence before challenging

## DO:
- ALWAYS give at least one hint before explaining
- Lead with clarity, follow with curiosity
- Cite sources: (From: Week X)
- Make complex ideas accessible
- Be warm and encouraging

## Context:
{context}

## Student's Question:
{query}

{scaffolding_guidance}
""",
        
        "default": """You are Course Marshal, an AI tutor for COMP 237: Introduction to AI at Centennial College.
You have access to course materials via the `retrieve_context` tool.

## Guidelines:
- Call `retrieve_context` first for AI/ML questions
- Be helpful and educational without being verbose
- Match your response depth to the question's complexity
- Cite sources with context: (From: [Week/Topic]) when available
- Be conversational and approachable

## Understanding Check:
Always end with a brief engagement - either:
- A follow-up invitation: "Does this help? Feel free to ask more!"
- A check: "Does that make sense?"
- An offer: "Want me to explain any part in more detail?"

## Style:
Respond naturally. Simple questions get simple answers. Complex topics deserve thorough but focused explanations.
"""
    }
    
    def detect_response_mode(self, context: PromptContext) -> ResponseMode:
        """Detect the response mode based on conversation context"""
        if not context.is_follow_up:
            return ResponseMode.FIRST_TURN
        
        # Check user signals
        signals_lower = [s.lower() for s in context.user_signals]
        
        if any(s in signals_lower for s in ["don't get", "don't understand", "confused", "what does that mean", "i don't get it"]):
            return ResponseMode.FOLLOW_UP_CLARIFY
        
        if any(s in signals_lower for s in ["example", "for example", "give an example"]):
            return ResponseMode.FOLLOW_UP_EXAMPLE
        
        if any(s in signals_lower for s in ["explain more", "go deeper", "more detail", "how does that work"]):
            return ResponseMode.FOLLOW_UP_DEEPEN
        
        # Default follow-up is continuation
        return ResponseMode.CONTINUATION
    
    def build_response_guidance(self, context: PromptContext, mode: ResponseMode) -> str:
        """Build response guidance based on mode and context"""
        
        if mode == ResponseMode.FIRST_TURN:
            # First turn: Provide foundation with hints
            if context.intent == "explain":
                return """## First Response Requirements:

### STEP 1: START WITH A HINT (Required!)
Before explaining, give 1-2 guiding hints to spark thinking:
- "Here's a hint: Think about how [concept] is similar to [everyday thing]..."
- "Quick clue: The key insight is that [core idea]..."
- "Consider this: What would happen if [scenario]?"

### STEP 2: THEN PROVIDE DEFINITION
After the hint, give 1-2 sentences defining the concept in plain language.
- Example: "Linear regression is a method for predicting a number based on other numbers."

### STEP 3: CONCRETE EXAMPLE
Follow with one real example.
- Use course materials when available: (From: Week X)
- Example: "If you want to predict house prices based on square footage, linear regression draws a 'best fit' line through your data points."

### STEP 4: CHECK-IN
End with ONE check-in question.
- "Does this make sense so far?"
- "Want to try thinking about how this applies to [related topic]?"

### Example of GOOD response:
"Here's a hint to get you thinking: neural networks are inspired by something you already have - your brain! 🧠

A neural network is a computing system made up of interconnected nodes (like neurons) that learn patterns from data. Think of it like a team of workers passing information to each other, each one doing a small job until they produce a final answer.

For example, a neural network can look at photos and learn to recognize cats vs dogs by processing millions of examples. (From: Week 8)

Does this help? Want me to explain how the 'learning' part works?"

FORBIDDEN: Jumping straight to definition without any hint. Give the student a moment to think first!"""
            
            elif context.intent == "tutor":
                return """## First Response Requirements:

### STEP 1: START WITH HINTS (Required!)
On the FIRST response, you MUST start with 1-2 guiding hints:
- "Here's a hint: Think about what happens when..."
- "Quick clue: The key to understanding this is..."
- "Consider this: How might [concept] relate to [something they know]?"

### STEP 2: THEN PROVIDE SEED EXPLANATION
After hints, provide a seed explanation (2-3 sentences minimum defining the concept)

### STEP 3: CONCRETE EXAMPLE
Add a concrete example or analogy

### STEP 4: GUIDING QUESTION
End with a guiding question to encourage deeper thinking

### Example of WRONG first response:
"What do you already know about linear regression?" (No hints, no explanation)

### Example of CORRECT first response:
"Here's a hint: Linear regression is like trying to draw the best 'straight line' through scattered dots on a graph. What do you think 'best' means here?

Linear regression is a way to predict a continuous value by fitting a line to your data. Think of it like drawing the 'best fit' line through scattered points. For example, predicting house prices based on square footage.

What aspects of this would you like to explore further?"

FORBIDDEN: Responding with ONLY questions. Students came to learn, not be interrogated. But DO give hints first!"""
            else:
                return ""  # No special guidance for other intents
        
        elif mode == ResponseMode.FOLLOW_UP_CLARIFY:
            # Follow-up clarify: Address specific confusion, don't repeat full explanation
            return """## Follow-up Clarification Response:
The student is asking for clarification on something you just explained. DO NOT repeat the full explanation.

Instead:
1. **Identify the specific point of confusion** from their question
2. **Address that point directly** with a clearer explanation or different angle
3. **Use a simpler analogy or example** if the first one didn't work
4. **Check understanding**: "Does this help clarify [specific point]?"

Keep it focused - they're confused about something specific, not the whole concept."""
        
        elif mode == ResponseMode.FOLLOW_UP_DEEPEN:
            # Follow-up deepen: Add layers, don't start from scratch
            return """## Follow-up Deepening Response:
The student wants to go deeper. Build on what you've already explained.

1. **Reference previous explanation**: "Building on what we discussed about [concept]..."
2. **Add the next layer**: Technical details, edge cases, advanced aspects
3. **Connect to related concepts**: "This connects to [related concept] because..."
4. **Provide deeper example**: More complex or nuanced example

Don't repeat the basics - they already understand those."""
        
        elif mode == ResponseMode.FOLLOW_UP_EXAMPLE:
            # Follow-up example: Provide concrete example, reference previous explanation
            return """## Follow-up Example Response:
The student wants a concrete example. Reference what you explained before.

1. **Brief reference**: "As I mentioned, [concept] works by..."
2. **Concrete example**: Provide a detailed, step-by-step example
3. **Walk through the example**: Show how the concept applies
4. **Connect back**: "This example shows how [key aspect] works in practice"

Keep the example focused and practical."""
        
        else:  # CONTINUATION
            # Continuation: Build on previous context
            return """## Continuation Response:
This is a continuation of the previous topic. Build naturally on what was discussed.

1. **Acknowledge continuity**: "Continuing from our discussion about [topic]..."
2. **Add new information**: Next aspect, related concept, or deeper dive
3. **Maintain context**: Reference what was covered before
4. **Progressive disclosure**: Add complexity gradually

Keep the conversation flowing naturally."""
    
    def build_length_guidance(self, context: PromptContext, mode: ResponseMode) -> str:
        """Build length guidance based on query complexity and mode"""
        
        # Check user signals first
        signals_lower = [s.lower() for s in context.user_signals]
        if "briefly" in signals_lower or "quick" in signals_lower or "short" in signals_lower:
            return "## Length: Keep it brief (2-3 sentences). The student asked for a quick answer."
        
        if "in detail" in signals_lower or "deep" in signals_lower or "thoroughly" in signals_lower:
            return "## Length: Provide a detailed explanation (4-6 paragraphs). The student wants depth."
        
        # Mode-based length guidance
        if mode == ResponseMode.FOLLOW_UP_CLARIFY:
            return "## Length: Keep it focused (2-4 sentences). Address the specific confusion point."
        
        if mode == ResponseMode.FOLLOW_UP_EXAMPLE:
            return "## Length: Medium (3-5 sentences). Provide a concrete, detailed example."
        
        if mode == ResponseMode.FOLLOW_UP_DEEPEN:
            return "## Length: Medium to detailed (4-6 paragraphs). Add depth to previous explanation."
        
        # Complexity-based length
        if context.query_complexity == QueryComplexity.SIMPLE:
            return "## Length: Keep it concise (2-4 sentences). This is a simple question."
        
        if context.query_complexity == QueryComplexity.MODERATE:
            return "## Length: Medium (3-5 paragraphs). Provide a thorough explanation."
        
        if context.query_complexity == QueryComplexity.COMPLEX:
            return "## Length: Detailed (5-7 paragraphs). This requires a comprehensive explanation."
        
        # Default
        return "## Length: Match the question's complexity. Simple questions get simple answers."
    
    def build_prompt(
        self,
        state: AgentState,
        intent: str,
        context_str: str = "",
        scaffolding_guidance: str = ""
    ) -> str:
        """
        Build adaptive prompt based on state and context.
        
        Args:
            state: Current agent state
            intent: Detected intent
            context_str: RAG context string
            scaffolding_guidance: Scaffolding level guidance
            
        Returns:
            Complete system prompt
        """
        # Build prompt context
        conversation_history = state.get("conversation_history", []) or []
        conversation_turn = len(conversation_history) // 2 + 1  # Approximate turn number
        
        # Detect user signals
        query = state.get("effective_query") or state.get("query", "")
        query_lower = query.lower()
        user_signals = []
        if "briefly" in query_lower or "quick" in query_lower:
            user_signals.append("briefly")
        if "in detail" in query_lower or "deep" in query_lower:
            user_signals.append("in detail")
        if "confused" in query_lower or "don't understand" in query_lower:
            user_signals.append("confused")
        
        # Determine query complexity
        query_complexity = self._detect_complexity(query, intent)
        
        # Build context
        prompt_context = PromptContext(
            intent=intent,
            is_follow_up=state.get("is_follow_up", False),
            conversation_turn=conversation_turn,
            previous_response_type=state.get("previous_response_type"),
            query_complexity=query_complexity,
            user_signals=user_signals,
            scaffolding_level=state.get("scaffolding_level"),
            bloom_level=state.get("bloom_level"),
            confusion_detected=state.get("student_confusion_detected", False),
            contextualized_query=state.get("contextualized_query"),
            conversation_history_length=len(conversation_history)
        )
        
        # Detect response mode
        mode = self.detect_response_mode(prompt_context)
        
        # Get base prompt
        base_prompt = self.BASE_PROMPTS.get(intent, self.BASE_PROMPTS["default"])
        
        # Build adaptive guidance
        response_guidance = self.build_response_guidance(prompt_context, mode)
        length_guidance = self.build_length_guidance(prompt_context, mode)
        
        # Combine guidance
        if response_guidance and length_guidance:
            adaptive_guidance = f"{response_guidance}\n\n{length_guidance}"
        elif response_guidance:
            adaptive_guidance = response_guidance
        elif length_guidance:
            adaptive_guidance = length_guidance
        else:
            adaptive_guidance = ""
        
        # NEW: Add student history context for personalization
        student_history = state.get("student_history_context", "")
        student_mastery = state.get("student_mastery_scores", {})
        has_prior_sessions = state.get("student_has_prior_sessions", False)
        
        # Build returning student guidance
        returning_student_guidance = ""
        if has_prior_sessions and student_history:
            returning_student_guidance = f"""
{student_history}

## 🔄 Returning Student Guidance
This student has prior learning history. Use this to personalize your response:

1. **Reference prior work**: "I see you've worked on [concept] before..."
2. **Acknowledge progress**: "Building on your understanding of [strong concept]..."
3. **Offer review**: If they're asking about something they struggled with before, ask: "We covered this before - would you like me to go through the steps again, or try a different approach?"
4. **Connect concepts**: Link current topic to their strong areas
5. **Track confusion**: If they showed confusion before on this topic, provide extra scaffolding

**Key phrases to use:**
- "Last time we discussed [topic], we covered..."
- "Since you've already explored [concept], let's build on that..."
- "I remember you had some questions about [concept] - shall we revisit the key points?"
- "Would you like to review the steps from before, or try a fresh explanation?"
"""
        elif has_prior_sessions and student_mastery:
            # Minimal guidance if we have mastery but no formatted history
            strong_concepts = [k for k, v in student_mastery.items() if v >= 0.6]
            if strong_concepts:
                returning_student_guidance = f"""
## 🎓 Returning Student
This student has strong understanding of: {', '.join(strong_concepts[:3])}
Consider building on their existing knowledge when explaining new concepts.
"""
        
        # Format prompt
        if "{response_guidance}" in base_prompt:
            prompt = base_prompt.format(
                response_guidance=adaptive_guidance,
                context=context_str,
                query=query,
                scaffolding_guidance=scaffolding_guidance
            )
        elif "{context}" in base_prompt or "{query}" in base_prompt or "{scaffolding_guidance}" in base_prompt:
            prompt = base_prompt.format(
                context=context_str,
                query=query,
                scaffolding_guidance=scaffolding_guidance
            )
            if adaptive_guidance:
                prompt = f"{adaptive_guidance}\n\n{prompt}"
        else:
            prompt = base_prompt
            if adaptive_guidance:
                prompt = f"{adaptive_guidance}\n\n{prompt}"
        
        # Append returning student guidance at the end if available
        if returning_student_guidance:
            prompt = f"{prompt}\n\n{returning_student_guidance}"
        
        logger.debug(f"Built prompt for intent={intent}, mode={mode}, complexity={query_complexity}, returning_student={has_prior_sessions}")
        
        return prompt
    
    def _detect_complexity(self, query: str, intent: str) -> QueryComplexity:
        """Detect query complexity"""
        query_lower = query.lower()
        
        # Simple: single concept, definition
        if any(kw in query_lower for kw in ["what is", "define", "meaning of"]):
            if len(query.split()) < 8:  # Short query
                return QueryComplexity.SIMPLE
        
        # Complex: multiple concepts, deep dive
        if any(kw in query_lower for kw in ["how does", "why does", "explain how", "compare", "difference between"]):
            return QueryComplexity.COMPLEX
        
        # Moderate: default
        return QueryComplexity.MODERATE


# Global instance
_prompt_builder = PromptBuilder()


def build_adaptive_prompt(
    state: AgentState,
    intent: str,
    context_str: str = "",
    scaffolding_guidance: str = ""
) -> str:
    """
    Convenience function to build adaptive prompt.
    
    Args:
        state: Current agent state
        intent: Detected intent
        context_str: RAG context string
        scaffolding_guidance: Scaffolding level guidance
        
    Returns:
        Complete system prompt
    """
    return _prompt_builder.build_prompt(state, intent, context_str, scaffolding_guidance)

