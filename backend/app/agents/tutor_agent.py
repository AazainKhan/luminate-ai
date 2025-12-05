"""
Main Tutor Agent using LangGraph
Implements the Governor-Agent pattern with Supervisor routing

Architecture (LLM-First Refactor 2025):
Governor → Reasoning → Supervisor → [Tutor|Math|Agent] → Tools → Evaluator

Key changes:
- Reasoning node performs multi-step analysis BEFORE routing
- Supervisor uses reasoning output for intelligent routing (LLM-first)
- Context engineering provides optimized prompts
"""

from typing import Dict, List, Any, Optional
import logging
import time
import uuid
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, ToolMessage
import json

from app.agents.state import AgentState
from app.agents.governor import governor_node
from app.agents.supervisor import supervisor_node, Supervisor
from app.agents.evaluator import evaluator_node
from app.agents.pedagogical_tutor import pedagogical_tutor_node
from app.agents.math_agent import math_agent_node
from app.agents.reasoning_node import reasoning_node  # NEW: Multi-step reasoning
from app.agents.tools import tutor_tools
from app.agents.source_metadata import extract_sources, Source  # Standardized source extraction
from app.observability import create_trace, flush_langfuse, get_langfuse_handler
from app.observability.langfuse_client import (
    create_observation,
    update_observation_with_usage,
    calculate_cost,
)

logger = logging.getLogger(__name__)


def extract_text_from_content(content) -> str:
    """
    Extract text from LLM response content, handling both string and list formats.
    
    Gemini 2.5+ returns content as a list of content blocks after tool calls:
    [{'type': 'text', 'text': 'actual response text'}, ...]
    
    This function normalizes both formats to a plain string.
    
    Args:
        content: Either a string or a list of content blocks
        
    Returns:
        The extracted text as a string
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Extract text from content blocks
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
            elif isinstance(block, str):
                text_parts.append(block)
        return ''.join(text_parts)
    else:
        return str(content) if content else ""


# Intent-specific system prompts for optimal response length/style
# These prompts are designed to be ADAPTIVE - the LLM should choose the best structure
# based on the actual question, not force a rigid template.
SYSTEM_PROMPTS = {
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

## Quick Hint Pattern:
Even for fast answers, consider giving a 1-line hint:
- "Quick hint: [core insight]. The answer is: [direct answer]"
- This helps learning stick better than just giving answers

## Even for quick answers, include:
- A brief "why it matters" if relevant (1 sentence)
- A check: "Does that answer your question, or would you like me to go deeper?"

## Style:
Concise but educational. Quick doesn't mean cold.
""",

    "explain": """You are Course Marshal, an AI tutor for COMP 237: Introduction to AI at Centennial College.
The student wants to understand a concept.

## Guidelines:
- Call `retrieve_context` first for course-specific information
- Keep explanations focused and appropriately sized for the question

## CRITICAL: ALWAYS GIVE A HINT FIRST
Before explaining, offer a hint to encourage thinking:
- "Here's a hint: Think about what makes [concept] different from [related concept]..."
- "Quick clue: The key to understanding this is [insight]..."
- "Consider this: What would happen if [scenario]?"

Then ask: "Want to try thinking about it, or should I explain?"

## Recommended Response Pattern:
For most explanations, this pattern works well:

1. **Start with a hint**: Give a guiding clue to encourage thinking
   - "Here's a hint: Gradient descent is like rolling a ball downhill..."

2. **Follow with definition**: 1-2 sentences explaining the concept simply
   - Example: "Linear regression predicts a number based on other numbers."

3. **Add a concrete example**: Something tangible and relatable
   - Use course materials when available: (From: Week X)
   - "Predicting house prices from square footage is classic linear regression."

4. **Add depth as needed**: Technical details, nuances, connections
   - Match depth to question complexity
   - Connect to what they might already know

5. **End with engagement**: A brief check-in or follow-up offer
   - "Does this help?" or "Want me to go deeper on any part?"

## Teaching Style:
- Lead with hints, then intuition, then formality
- Use analogies to bridge unfamiliar concepts
- Cite sources naturally: (From: Week 5 notes)
- Pose reflection questions after explaining, not instead of

## Personalization:
- Reference prior topics when relevant
- Adapt depth to their apparent level
- For new students: lean toward more context

## Avoid:
- Jumping straight to full explanations without hints
- All-questions-no-explanation responses
- Jargon dumps without intuition
- Overly long responses for simple questions
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
    
    "default": """You are Course Marshal, an AI tutor for COMP 237: Introduction to AI at Centennial College.
You have access to course materials via the `retrieve_context` tool.

## Guidelines:
- Call `retrieve_context` first for AI/ML questions
- Be helpful and educational without being verbose
- Match your response depth to the question's complexity
- Cite sources with context: (From: [Week/Topic]) when available
- Be conversational and approachable

## Hint-First Approach:
When explaining concepts, give a quick hint first:
- "Here's a hint to get you thinking: [insight]"
- "Quick clue: [key connection]"
Then provide the explanation. This helps learning stick!

## Understanding Check:
Always end with a brief engagement - either:
- A follow-up invitation: "Does this help? Feel free to ask more!"
- A check: "Does that make sense?"
- An offer: "Want me to explain any part in more detail?"

## Style:
Respond naturally. Simple questions get simple answers. Complex topics deserve thorough but focused explanations.
"""
}

# Legacy prompt for compatibility
SYSTEM_PROMPT = SYSTEM_PROMPTS["default"]

def should_continue(state: AgentState) -> str:
    """
    Conditional edge function
    Determines next step based on governor approval
    """
    if not state.get("governor_approved", False):
        return "end"  # Stop if governor rejected
    return "continue"


def route_by_intent(state: AgentState) -> str:
    """
    Route to specialized agent based on detected intent
    
    Routes:
    - tutor: Pedagogical Socratic agent (full scaffolding for confused students)
    - math: Mathematical reasoning agent
    - explain/fast/syllabus_query/coder: General agent with intent-specific prompts
    """
    intent = state.get("intent", "fast")
    
    if intent == "tutor":
        return "pedagogical_tutor"
    elif intent == "math":
        return "math_agent"
    else:
        # explain, fast, syllabus_query, coder all use agent node with different prompts
        return "agent"


def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    General agent node that invokes the model with tools
    Used for: coder, syllabus_query, fast, explain intents
    
    Uses adaptive prompt builder for context-aware responses.
    Now includes mastery-aware scaffolding for personalized responses.
    Supports repair loop via repair_guidance from quality gate.
    """
    supervisor = Supervisor()
    model_name = state.get("model_selected", "gemini-flash")
    model = supervisor.get_model(model_name)
    
    # Bind tools
    model_with_tools = model.bind_tools(tutor_tools)
    
    messages = state["messages"]
    
    # Get intent
    intent = state.get("intent", "fast")
    
    # Use adaptive prompt builder for context-aware prompts
    from app.agents.prompt_builder import build_adaptive_prompt
    
    # Build context string from retrieved context
    retrieved_context = state.get("retrieved_context", [])
    context_parts = []
    for doc in retrieved_context[:5]:
        content = doc.get("content") or doc.get("text") or doc.get("page_content", "")
        source = doc.get("source_file") or doc.get("metadata", {}).get("source_file", "")
        context_parts.append(f"[From {source}]\n{content}")
    context_str = "\n\n---\n\n".join(context_parts) if context_parts else ""
    
    # Build adaptive system prompt
    system_prompt = build_adaptive_prompt(
        state=state,
        intent=intent,
        context_str=context_str,
        scaffolding_guidance=""
    )
    
    # Build mastery-aware context for personalization
    mastery_context = _build_mastery_context(state)
    if mastery_context:
        system_prompt = system_prompt + "\n\n" + mastery_context
    
    # If this is a repair loop, add repair guidance to prompt
    repair_guidance = state.get("repair_guidance")
    if repair_guidance:
        logger.info("🔧 Agent: Repair loop triggered, adding guidance")
        system_prompt = system_prompt + "\n\n" + repair_guidance
    
    # Ensure system prompt is present (use adaptive prompt)
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=system_prompt)] + messages
    else:
        # Replace existing system prompt with adaptive one
        messages = [SystemMessage(content=system_prompt)] + [m for m in messages if not isinstance(m, SystemMessage)]
    
    response = model_with_tools.invoke(messages)
    
    # Update state with response for legacy compatibility
    # Clear repair state after successful generation
    # Handle Gemini 2.5+ list content format (after tool calls)
    return {
        "messages": [response],
        "response": extract_text_from_content(response.content),
        "needs_repair": False,  # Clear repair flag
        "repair_guidance": None  # Clear guidance
    }


def _build_mastery_context(state: AgentState) -> str:
    """
    Build mastery-aware context for personalized scaffolding.
    
    This enables the agent to:
    - Reference what the student already knows
    - Connect new concepts to mastered ones
    - Adjust explanation depth based on prior knowledge
    - Reference recent conversation topics
    - Remind students of prior work and offer to review
    """
    user_id = state.get("user_id")
    conversation_history = state.get("conversation_history", []) or []
    query = state.get("effective_query", state.get("query", "")).lower()
    
    context_parts = []
    
    # NEW: Check if student history was already fetched by reasoning node
    student_history_context = state.get("student_history_context")
    if student_history_context:
        # Use pre-fetched history from reasoning node
        context_parts.append(student_history_context)
        context_parts.append("")
        context_parts.append("**Personalization Strategies:**")
        context_parts.append("- If student asks about a topic they've seen before, say: 'We covered this before - would you like to go through the steps again?'")
        context_parts.append("- Reference their strong areas when explaining: 'Since you understand [strong concept] well...'")
        context_parts.append("- If they struggled before, offer alternatives: 'Let me try a different approach this time.'")
        return "\n".join(context_parts)
    
    # Part 1: Build conversation context (what we've discussed recently)
    if conversation_history:
        recent_topics = _extract_recent_topics(conversation_history)
        if recent_topics:
            context_parts.append("## 📚 Recent Conversation Context")
            context_parts.append(f"Topics we've discussed: {', '.join(recent_topics)}")
            context_parts.append("")
            context_parts.append("**USE THIS**: Reference naturally in your response:")
            context_parts.append(f"  'Earlier we talked about {recent_topics[0]}...'")
            context_parts.append(f"  'Building on what you know about {recent_topics[0]}...'")
            context_parts.append("")
    
    # Part 2: Build mastery context (what they know overall)
    if not user_id:
        if not context_parts:
            # No user ID and no conversation history
            context_parts.append("## 👋 New Student Context")
            context_parts.append("No prior knowledge data available for this student.")
            context_parts.append("")
            context_parts.append("**Approach**:")
            context_parts.append("- Start with foundational concepts and everyday analogies")
            context_parts.append("- Don't assume prior AI/ML knowledge")
            context_parts.append("- Check understanding frequently")
        return "\n".join(context_parts)
    
    try:
        import asyncio
        from app.agents.knowledge_graph import get_student_mastery_all
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, get_student_mastery_all(user_id))
                mastery_scores = future.result(timeout=1.0)
        else:
            mastery_scores = asyncio.run(get_student_mastery_all(user_id))
        
        if not mastery_scores:
            context_parts.append("## 👋 New Student Context")
            context_parts.append("This student has no prior mastery data recorded.")
            context_parts.append("")
            context_parts.append("**Approach for new students**:")
            context_parts.append("- Start with foundational concepts and analogies")
            context_parts.append("- Use everyday examples to build intuition")
            context_parts.append("- Ask: 'Have you seen [related concept] before?' to gauge background")
            context_parts.append("- End with: 'Does this make sense so far?'")
            return "\n".join(context_parts)
        
        # Categorize mastery levels
        strong = [(k.replace("_", " ").title(), v) for k, v in mastery_scores.items() if v >= 0.6]
        moderate = [(k.replace("_", " ").title(), v) for k, v in mastery_scores.items() if 0.3 <= v < 0.6]
        weak = [(k.replace("_", " ").title(), v) for k, v in mastery_scores.items() if v < 0.3]
        
        context_parts.append("## 🎓 Student Knowledge Profile")
        context_parts.append("")
        
        # Find concepts relevant to the current query
        query_relevant = []
        for concept, score in strong + moderate + weak:
            if any(word in query for word in concept.lower().split()):
                query_relevant.append((concept, score))
        
        if query_relevant:
            context_parts.append("**Concepts relevant to this question:**")
            for concept, score in query_relevant:
                level = "strong" if score >= 0.6 else "moderate" if score >= 0.3 else "needs work"
                context_parts.append(f"  • {concept}: {level} ({int(score*100)}%)")
            context_parts.append("")
        
        if strong:
            strong_concepts = [c[0] for c in strong]
            context_parts.append(f"✅ **Strong understanding**: {', '.join(strong_concepts)}")
            context_parts.append(f"   USE THIS: 'Since you have a good grasp of {strong_concepts[0]}, think of this as...'")
            context_parts.append("")
        
        if moderate:
            moderate_concepts = [c[0] for c in moderate]
            context_parts.append(f"📈 **Building understanding**: {', '.join(moderate_concepts)}")
            context_parts.append(f"   CONNECT: 'This builds on {moderate_concepts[0]}, which you've been learning...'")
            context_parts.append("")
        
        if weak:
            weak_concepts = [c[0] for c in weak]
            context_parts.append(f"📝 **Needs reinforcement**: {', '.join(weak_concepts)}")
            context_parts.append(f"   SCAFFOLD: Provide extra context if these topics come up")
            context_parts.append("")
        
        # Adaptive depth guidance
        avg_mastery = sum([v for _, v in mastery_scores.items()]) / len(mastery_scores) if mastery_scores else 0
        context_parts.append("**Personalization guidance**:")
        if avg_mastery >= 0.6:
            context_parts.append("- This student has strong overall understanding → can use technical terms more freely")
            context_parts.append("- Focus on nuances, edge cases, and deeper implications")
            context_parts.append("- Ask challenging follow-up questions")
        elif avg_mastery >= 0.3:
            context_parts.append("- This student is building understanding → balance intuition with technical detail")
            context_parts.append("- Connect new concepts to their stronger areas")
            context_parts.append("- Use both analogies and formal definitions")
        else:
            context_parts.append("- This student needs foundational support → prioritize clarity over completeness")
            context_parts.append("- Use plenty of analogies and concrete examples")
            context_parts.append("- Break complex ideas into smaller steps")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.debug(f"Could not fetch mastery for personalization: {e}")
        return "\n".join(context_parts) if context_parts else ""


def _extract_recent_topics(conversation_history: list) -> list:
    """Extract topic keywords from recent conversation for context."""
    if not conversation_history:
        return []
    
    # Look at last 4 messages (2 exchanges)
    recent = conversation_history[-4:] if len(conversation_history) >= 4 else conversation_history
    
    # Common AI/ML topic keywords
    topic_keywords = {
        "neural network": "Neural Networks",
        "gradient descent": "Gradient Descent", 
        "backpropagation": "Backpropagation",
        "classification": "Classification",
        "regression": "Regression",
        "clustering": "Clustering",
        "loss function": "Loss Functions",
        "activation function": "Activation Functions",
        "overfitting": "Overfitting",
        "training": "Model Training",
        "layers": "Network Layers",
        "weights": "Weights & Biases",
        "learning rate": "Learning Rate",
    }
    
    found_topics = set()
    for msg in recent:
        content = msg.get("content", "").lower()
        for keyword, display_name in topic_keywords.items():
            if keyword in content:
                found_topics.add(display_name)
    
    return list(found_topics)[:3]  # Return top 3 topics

def route_agent_output(state: AgentState) -> str:
    """
    Determine next step after agent execution
    """
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "quality_gate"  # Route to quality gate for confidence check

def post_tool_processing_node(state: AgentState) -> Dict[str, Any]:
    """
    Process tool outputs and update state with retrieved context
    """
    messages = state["messages"]
    retrieved_context = state.get("retrieved_context", []) or []
    
    # Iterate backwards to find the most recent ToolMessages
    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage):
            break
            
        if msg.name == "retrieve_context":
            try:
                content = msg.content
                if isinstance(content, str):
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            retrieved_context.extend(data)
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                logger.warning(f"Error processing tool output: {e}")
    
    return {"retrieved_context": retrieved_context}


def get_expected_length_range(intent: str, is_follow_up: bool, response_length_hint: Optional[str] = None) -> tuple[int, int]:
    """
    Get expected response length range based on intent and context.
    
    UPDATED (Dec 2025): Relaxed limits to prevent over-truncation.
    Follow-ups should be shorter but not artificially clipped.
    
    Returns:
        Tuple of (min_chars, max_chars)
    """
    # Use hint from reasoning node if available
    if response_length_hint:
        if response_length_hint == "short":
            return (50, 400)  # Relaxed from 300
        elif response_length_hint == "medium":
            if is_follow_up:
                return (150, 800)  # Relaxed from 500
            return (300, 1500)  # Relaxed from 1200
        elif response_length_hint == "detailed":
            if is_follow_up:
                return (300, 1200)  # Relaxed from 800
            return (800, 2800)  # Relaxed from 2500
    
    # Intent-based defaults (relaxed to allow natural responses)
    if intent == "fast":
        return (50, 400)  # 1-4 sentences
    elif intent == "syllabus_query":
        return (100, 600)  # 2-5 sentences
    elif intent == "coder":
        return (200, 2000)  # Code + explanation (code can be long)
    elif intent == "explain":
        if is_follow_up:
            return (100, 800)  # Relaxed from 500 - allow substantive clarifications
        return (400, 1800)  # 3-6 paragraphs
    elif intent == "tutor":
        if is_follow_up:
            return (100, 900)  # Relaxed from 450 - clarifications need room
        return (300, 1600)  # Relaxed from 1200 - full scaffolding
    elif intent == "math":
        if is_follow_up:
            return (150, 1000)  # Math clarifications need room for formulas
        return (300, 2500)  # Mathematical derivations can be longer
    
    # Default
    if is_follow_up:
        return (100, 800)
    return (200, 1200)


def calculate_response_confidence(response: str, intent: str, state: Optional[AgentState] = None) -> float:
    """
    Calculate confidence score for response quality with context-aware length checking.
    
    UPDATED (Dec 2025): More lenient scoring to avoid over-repair.
    Focus on catching genuinely bad responses, not penalizing natural variation.
    
    Low confidence triggers repair loop.
    
    Returns:
        Score between 0.0 and 1.0
    """
    if not response:
        return 0.0
    
    base_score = 0.6  # Start higher - assume good until proven otherwise
    response_length = len(response)
    
    # Context-aware length checking
    is_follow_up = state.get("is_follow_up", False) if state else False
    response_length_hint = state.get("response_length_hint") if state else None
    min_chars, max_chars = get_expected_length_range(intent, is_follow_up, response_length_hint)
    
    # Length scoring - RELAXED penalties
    if response_length < min_chars:
        # Too short - penalize based on how short
        ratio = response_length / min_chars if min_chars > 0 else 0
        base_score -= 0.2 * (1 - ratio)  # Reduced from 0.3
    elif response_length > max_chars:
        # Too long - very mild penalty (let natural responses through)
        excess_ratio = (response_length - max_chars) / max_chars
        base_score -= min(0.1, excess_ratio * 0.05)  # Reduced from 0.2 cap
    else:
        # Within range - small bonus
        base_score += 0.1
    
    # Follow-up specific check - only penalize EXTREME overages
    if is_follow_up and response_length > max_chars * 2.0:  # Changed from 1.5x
        base_score -= 0.15  # Reduced from 0.2
        logger.info(f"📏 Follow-up response long ({response_length} chars) - minor penalty")
    
    # Question ratio check - only penalize if MOSTLY questions with NO substance
    sentences = [s.strip() for s in response.split('.') if s.strip()]
    if sentences:
        question_count = sum(1 for s in sentences if '?' in s)
        question_ratio = question_count / len(sentences)
        
        # Only penalize if >70% questions AND very short (likely just questions)
        if question_ratio > 0.7 and response_length < min_chars * 0.7:
            base_score -= 0.15  # Reduced from 0.25
        # Reward good question balance (10-40%) for tutor intent
        elif intent == "tutor" and 0.1 <= question_ratio <= 0.5:
            base_score += 0.05
    
    # Check for explanation markers (positive signals) - reduced bonus
    explanation_markers = [
        'means', 'is a', 'refers to', 'for example', 'in other words',
        'this is', 'essentially', 'simply put', 'think of it as',
        'works by', 'the reason', 'because'
    ]
    response_lower = response.lower()
    marker_count = sum(1 for m in explanation_markers if m in response_lower)
    base_score += min(0.1, marker_count * 0.02)  # Reduced from 0.2 max
    
    # Structure bonus - reduced to avoid rewarding verbose formatting
    if any(c in response for c in ['•', '-', '1.', '2.']):
        base_score += 0.05  # Reduced from 0.1
    
    return max(0.0, min(1.0, base_score))


def quality_gate_node(state: AgentState) -> Dict[str, Any]:
    """
    Quality gate that checks response quality and triggers repair if needed.
    
    This node runs after the agent produces a response but before the evaluator.
    If the response is low quality (mostly questions, no explanation), it
    triggers a repair loop with explicit guidance.
    
    Returns:
        State updates including needs_repair flag and guidance
    """
    response = state.get("response", "")
    intent = state.get("intent", "fast")
    retry_count = state.get("quality_retry_count", 0) or 0
    
    # Calculate confidence with context-aware length checking
    confidence = calculate_response_confidence(response, intent, state)
    
    logger.info(f"📊 Quality Gate: confidence={confidence:.2f}, retry_count={retry_count}")
    
    # Only check for repair on explain/tutor intents (not fast/syllabus)
    if intent in ["fast", "syllabus_query"]:
        return {
            "needs_repair": False,
            "response_confidence": confidence
        }
    
    # If confidence is too low and we haven't retried yet
    CONFIDENCE_THRESHOLD = 0.5
    MAX_RETRIES = 1
    
    if confidence < CONFIDENCE_THRESHOLD and retry_count < MAX_RETRIES:
        logger.warning(f"⚠️ Quality Gate: Low confidence ({confidence:.2f}), triggering repair")
        
        # CRITICAL: Adjust repair guidance based on follow-up status
        is_follow_up = state.get("is_follow_up", False)
        
        if is_follow_up:
            # Follow-up repair: Focus on being SHORT and specific
            repair_text = """
REPAIR REQUIRED: Your previous follow-up response was too long or repetitive.

For FOLLOW-UP responses, you MUST:
1. Keep it SHORT: Maximum 3-4 sentences (NOT paragraphs)
2. Address ONLY the specific confusion point
3. Do NOT repeat the full explanation from before
4. Do NOT add diagrams, quizzes, or "next topics"
5. Use a simpler analogy if the first one didn't work

Example of GOOD follow-up repair:
"The key difference is [specific point]. Think of it like [simple analogy]. Does this help?"

Example of BAD follow-up repair:
[Repeating the entire concept definition with examples, diagrams, and quizzes]
"""
        else:
            # First-turn repair: Focus on including explanation
            repair_text = """
REPAIR REQUIRED: Your previous response was too light on explanation.

You MUST include:
1. A clear DEFINITION (1-2 sentences explaining what the concept IS)
2. A concrete EXAMPLE (not just "for example..." but an actual example)
3. THEN a check-in question

Do NOT respond with only questions. The student needs an explanation first.
"""
        
        return {
            "needs_repair": True,
            "quality_retry_count": retry_count + 1,
            "response_confidence": confidence,
            "repair_guidance": repair_text
        }
    
    return {
        "needs_repair": False,
        "response_confidence": confidence
    }


def truncate_response_if_needed(state: AgentState) -> Dict[str, Any]:
    """
    Hard truncation for follow-up responses that are still too long after quality gate.
    
    This is a last-resort enforcement. If the response exceeds limits after repair,
    we truncate it gracefully at a sentence boundary.
    """
    response = state.get("response", "")
    is_follow_up = state.get("is_follow_up", False)
    intent = state.get("intent", "fast")
    
    if not is_follow_up:
        return {}  # Only enforce for follow-ups
    
    _, max_chars = get_expected_length_range(intent, is_follow_up, state.get("response_length_hint"))
    
    if len(response) <= max_chars:
        return {}  # Within limits
    
    # Find a good truncation point (end of sentence)
    truncate_at = max_chars
    
    # Look for sentence endings near the limit
    for punct in ['. ', '! ', '? ']:
        last_punct = response[:max_chars].rfind(punct)
        if last_punct > max_chars * 0.6:  # At least 60% of content
            truncate_at = last_punct + 1
            break
    
    # Truncate and add continuation message
    truncated = response[:truncate_at].strip()
    truncated += "\n\nWant me to explain any part in more detail?"
    
    logger.info(f"📏 Hard truncation: {len(response)} → {len(truncated)} chars (follow-up)")
    
    return {
        "response": truncated
    }


def route_quality_gate(state: AgentState) -> str:
    """Route based on quality gate decision."""
    if state.get("needs_repair"):
        return "repair"
    return "continue"


def create_tutor_agent() -> StateGraph:
    """
    Create and configure the tutor agent graph
    
    Graph Structure (LLM-First Architecture with Context Engineering):
    START → reasoning → governor → (approved?) → supervisor → [tutor|math|agent] → quality_gate → evaluator → END
           (context eng)          ↓
                                 END (rejected)
    
    Execution Order:
    1. reasoning: Multi-step analysis, follow-up detection, context engineering (compaction)
    2. governor: Policy check (safety, compliance)
    3. supervisor: Intelligent routing based on reasoning output
    4. [tutor|math|agent]: Specialized agent with adaptive prompts
    5. quality_gate: Response quality check, triggers repair if needed
    6. evaluator: Final evaluation, mastery tracking
    
    Key Features (2025 Refactor):
    - Reasoning node performs analysis BEFORE routing (LLM-first)
    - Context engineering: Automatic compaction for long conversations
    - Adaptive prompts: Context-aware response generation
    - Quality gate: Auto-repair for low-quality responses
    - Follow-up handling: Contextualized queries for better understanding
    
    State Flow:
    - reasoning → sets: intent, is_follow_up, contextualized_query, effective_query
    - governor → sets: governor_approved
    - supervisor → sets: model_selected, final intent
    - agent → sets: response, scaffolding_level
    - quality_gate → sets: needs_repair, repair_guidance (if needed)
    - evaluator → sets: evaluation scores, updates mastery
    
    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes (NEW: reasoning node for LLM-first architecture)
    workflow.add_node("governor", governor_node)
    workflow.add_node("reasoning", reasoning_node)  # NEW: Multi-step reasoning before routing
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("pedagogical_tutor", pedagogical_tutor_node)  # Socratic scaffolding
    workflow.add_node("math_agent", math_agent_node)  # Mathematical reasoning
    workflow.add_node("agent", agent_node)  # General agent with tools
    workflow.add_node("tools", ToolNode(tutor_tools))
    workflow.add_node("post_tools", post_tool_processing_node)
    workflow.add_node("quality_gate", quality_gate_node)  # NEW: Response quality check
    workflow.add_node("length_enforcer", truncate_response_if_needed)  # NEW: Hard length enforcement for follow-ups
    workflow.add_node("evaluator", evaluator_node)
    
    # Set entry point
    workflow.set_entry_point("reasoning")
    
    # Reasoning node always flows to governor (policy check)
    workflow.add_edge("reasoning", "governor")
    
    # Add conditional edge from governor
    workflow.add_conditional_edges(
        "governor",
        should_continue,
        {
            "continue": "supervisor",  # Changed: now goes to supervisor if approved
            "end": END,
        }
    )
    
    # Route from supervisor to specialized agents based on intent
    workflow.add_conditional_edges(
        "supervisor",
        route_by_intent,
        {
            "pedagogical_tutor": "pedagogical_tutor",
            "math_agent": "math_agent",
            "agent": "agent"
        }
    )
    
    # Pedagogical tutor goes to quality gate (instead of directly to evaluator)
    workflow.add_edge("pedagogical_tutor", "quality_gate")
    
    # Math agent goes to quality gate
    workflow.add_edge("math_agent", "quality_gate")
    
    # General agent may use tools
    workflow.add_conditional_edges(
        "agent",
        route_agent_output,
        {
            "tools": "tools",
            "quality_gate": "quality_gate"  # Changed: goes to quality_gate instead of evaluator
        }
    )
    
    # Loop back from tools to agent via post_tools
    workflow.add_edge("tools", "post_tools")
    workflow.add_edge("post_tools", "agent")
    
    # Quality gate routes to length_enforcer (for final check) or back to agent for repair
    workflow.add_conditional_edges(
        "quality_gate",
        route_quality_gate,
        {
            "continue": "length_enforcer",  # Changed: goes through length enforcer
            "repair": "agent"  # Repair loop: go back to agent with guidance
        }
    )
    
    # Length enforcer always goes to evaluator
    workflow.add_edge("length_enforcer", "evaluator")
    
    # End after evaluator
    workflow.add_edge("evaluator", END)
    
    # Compile graph
    app = workflow.compile()
    
    logger.info("Tutor agent graph created successfully (LLM-first architecture)")
    return app


# Global agent instance
_tutor_agent = None


def get_tutor_agent() -> StateGraph:
    """Get or create tutor agent instance"""
    global _tutor_agent
    if _tutor_agent is None:
        _tutor_agent = create_tutor_agent()
    return _tutor_agent


def run_agent(
    query: str, 
    user_id: str = None, 
    user_email: str = None, 
    session_id: str = None,
    conversation_history: List[Dict[str, Any]] = None
) -> Dict:
    """
    Run the tutor agent with comprehensive observability and rich metadata tracking
    
    Args:
        query: User query
        user_id: Optional user ID
        user_email: Optional user email
        session_id: Optional session ID
        conversation_history: Optional list of prior messages
        
    Returns:
        Dictionary with response and metadata
    """

    
    agent = get_tutor_agent()
    execution_start = time.time()
    request_id = str(uuid.uuid4())
    
    # Get Langfuse handler
    langfuse_handler = get_langfuse_handler()
    callbacks = [langfuse_handler] if langfuse_handler else []
    
    # Create comprehensive trace with rich metadata
    span = create_trace(
        name="tutor_agent_execution",
        user_id=user_id,
        session_id=session_id,
        environment="development",  # TODO: get from settings
        version="1.0.0",
        tags=["tutor-agent", "comp237", "educational-ai"],
        metadata={
            "query_length": len(query),
            "query_type": "student_question",  # Could be enhanced with classification
            "user_email": user_email,
            "user_role": "student",  # Could be determined from email domain
            "request_id": request_id,
            "client_type": "chrome_extension",
            "course_context": "COMP237_AI_Fundamentals",
            "history_length": len(conversation_history) if conversation_history else 0
        },
        input_data={
            "query": query,
            "user_context": {
                "user_id": user_id,
                "email": user_email,
                "role": "student"
            }
        }
    )
    
    # Use OpenTelemetry context to link LangChain execution to the span
    from opentelemetry import trace
    
    # Build message history from conversation_history
    messages = []
    if conversation_history:
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                # For assistant messages, use a simple AI message
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=content))
    
    # Add current user message
    messages.append(HumanMessage(content=query))
    
    # Initialize state with all required fields including new pedagogical state
    initial_state: AgentState = {
        # User input
        "messages": messages,
        "query": query,
        
        # User context
        "user_id": user_id,
        "user_email": user_email,
        "user_role": "student",
        "trace_id": span.trace_id if span else None,
        "parent_observation_id": span.id if span else None,  # For linking child spans
        "langfuse_root_span": span,  # Pass actual span object for proper v3 nesting
        
        # Session/history context
        "conversation_history": conversation_history,
        
        # Routing decisions
        "intent": None,
        "model_selected": None,
        
        # Reasoning node output (NEW - LLM-first architecture)
        "reasoning_complete": False,
        "reasoning_intent": None,
        "reasoning_confidence": None,
        "reasoning_strategy": None,
        "reasoning_context_needed": None,
        "reasoning_trace": None,
        
        # Context engineering (NEW)
        "curated_context": None,
        "context_budget_tokens": None,
        "context_relevance_scores": None,
        
        # RAG context
        "retrieved_context": [],
        "context_sources": [],
        
        # Policy enforcement
        "governor_approved": False,
        "governor_reason": None,
        
        # Pedagogical state
        "scaffolding_level": None,
        "student_confusion_detected": False,
        "thinking_steps": None,
        "bloom_level": None,
        "pedagogical_approach": None,
        
        # Sub-agent outputs
        "syllabus_check": None,
        "math_explanation": None,
        "math_derivation": None,
        "code_suggestion": None,
        "pedagogical_strategy": None,
        
        # Final response
        "response": None,
        "response_sources": [],
        
        # Error handling
        "error": None,
    }
    
    # Run agent
    try:
        if span and hasattr(span, "_otel_span"):
            with trace.use_span(span._otel_span, end_on_exit=False):
                final_state = agent.invoke(
                    initial_state,
                    config={"callbacks": callbacks}
                )
        else:
            final_state = agent.invoke(
                initial_state,
                config={"callbacks": callbacks}
            )
        
        # Extract response from last message if not explicitly set
        response_text = final_state.get("response")
        if not response_text and final_state["messages"]:
            last_msg = final_state["messages"][-1]
            if isinstance(last_msg, BaseMessage):
                response_text = last_msg.content
        
        # Calculate execution metrics
        execution_end = time.time()
        total_execution_time = execution_end - execution_start
        
        # Prepare comprehensive output metadata
        output_metadata = {
            "response": response_text,
            "intent_classification": final_state.get("intent"),
            "model_selection": final_state.get("model_selected"),
            "policy_compliance": {
                "governor_approved": final_state.get("governor_approved"),
                "policy_violations": final_state.get("governor_reason") if not final_state.get("governor_approved") else None
            },
            "execution_metrics": {
                "total_duration_seconds": round(total_execution_time, 3),
                "processing_times_ms": final_state.get("processing_times", {}),
                "context_analysis": {
                    "input_length_chars": len(query),
                    "response_length_chars": len(response_text) if response_text else 0,
                    "context_lengths": final_state.get("context_lengths", {})
                }
            },
            "retrieval_analysis": final_state.get("retrieval_metrics", {}),
            "cost_analysis": final_state.get("cost_tracking", {}),
            "citations_count": len(final_state.get("response_sources", [])),
            "performance_tier": "fast" if total_execution_time < 5.0 else "standard"
        }
        
        # Update trace with comprehensive observability data
        if span:
            update_observation_with_usage(
                span,
                output_data=output_metadata,
                usage_details={
                    "input": final_state.get("cost_tracking", {}).get("token_usage", {}).get("input", 0),
                    "output": final_state.get("cost_tracking", {}).get("token_usage", {}).get("output", 0),
                    "total": final_state.get("cost_tracking", {}).get("token_usage", {}).get("total", 0),
                    "unit": "TOKENS"
                },
                cost_details={
                    "total_cost": final_state.get("cost_tracking", {}).get("total_cost", 0.0)
                },
                level="DEFAULT",
                latency_seconds=total_execution_time
            )
            
            # FORCE TRACE NAME RESTORATION
            # This fixes the issue where child spans overwrite the trace name
            span.update_trace(name="tutor_agent_execution")
            
            span.end()
        
        # Flush Langfuse events
        flush_langfuse()
        
        result = {
            "response": response_text,
            "sources": final_state.get("response_sources", []),
            "intent": final_state.get("intent"),
            "model_used": final_state.get("model_selected"),
            "error": final_state.get("error"),
            # Follow-up detection (for debugging and testing)
            "is_follow_up": final_state.get("is_follow_up", False),
            "response_length_hint": final_state.get("response_length_hint"),
            # Chain-of-Thought for transparency (per CoT paper best practices)
            "thought_chain": final_state.get("thought_chain", []),
            "key_concepts": final_state.get("key_concepts_detected", []),
            # Student history for personalization tracking
            "student_history_context": final_state.get("student_history_context", ""),
            "student_mastery_scores": final_state.get("student_mastery_scores", {}),
            "student_has_prior_sessions": final_state.get("student_has_prior_sessions", False),
            # Enhanced metadata
            "execution_metrics": {
                "duration_seconds": round(total_execution_time, 3),
                "cost_usd": final_state.get("cost_tracking", {}).get("total_cost", 0.0),
                "tokens_used": final_state.get("cost_tracking", {}).get("token_usage", {}).get("total", 0),
                "performance_tier": "fast" if total_execution_time < 5.0 else "standard"
            },
            "observability": {
                "request_id": request_id,
                "trace_id": span.trace_id if span else None,
                "policy_compliant": final_state.get("governor_approved", False)
            },
            # Return messages for debugging/frontend if needed
            "messages": final_state.get("messages", [])
        }
        
        return result
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        
        # Log comprehensive error information
        execution_end = time.time()
        error_metadata = {
            "error_message": str(e),
            "error_type": type(e).__name__,
            "execution_duration": round(execution_end - execution_start, 3),
            "failed_at": "agent_execution",
            "request_id": request_id,
            "partial_state": {
                "intent_detected": initial_state.get("intent"),
                "model_selected": initial_state.get("model_selected"),
                "governor_status": initial_state.get("governor_approved")
            }
        }
        
        if span:
            update_observation_with_usage(
                span,
                output_data=error_metadata,
                level="ERROR",
                latency_seconds=execution_end - execution_start
            )
            span.end()
        
        flush_langfuse()
        
        return {
            "response": "I apologize, but I encountered an error processing your query.",
            "sources": [],
            "error": str(e),
            "execution_metrics": {
                "duration_seconds": round(execution_end - execution_start, 3),
                "cost_usd": 0.0,
                "tokens_used": 0,
                "performance_tier": "error"
            },
            "observability": {
                "request_id": request_id,
                "trace_id": span.trace_id if span else None,
                "error_type": type(e).__name__
            }
        }


def _get_intelligent_queue_steps(query: str) -> List[dict]:
    """
    Intelligently select which pipeline steps to show based on query complexity.
    
    For an educational AI tutor, we want to show chain of thought for most queries
    to provide transparency and show the student the AI is "working".
    
    Pipeline stages:
    - reasoning: Multi-step analysis (perception, analysis, planning, decision)
    - policy-check: Governor node validates query is in-scope
    - intent-routing: Supervisor routes to appropriate agent
    - response-gen: Agent generates response (may use tools)
    
    Only skip chain of thought for truly trivial interactions (greetings, thanks).
    
    Returns:
        List of queue step dicts, or empty list to show no steps
    """
    query_lower = query.lower().strip()
    query_words = len(query.split())
    
    # Very short queries or greetings - no steps needed
    greeting_patterns = ["hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "bye", "goodbye", "yes", "no", "sure", "yep", "nope"]
    if query_words <= 2 and any(query_lower.startswith(g) for g in greeting_patterns):
        return []  # No chain of thought for simple greetings
    
    # Single word queries that aren't educational
    if query_words == 1:
        return []
    
    # Full pipeline for educational queries - show all relevant stages
    # This provides transparency into the AI's reasoning process
    
    # Confusion/tutoring queries - show full pipeline with more detail
    confusion_patterns = ["don't understand", "confused", "help me understand", "struggling", 
                         "can you explain", "i'm stuck", "need help", "lost", "unclear"]
    if any(p in query_lower for p in confusion_patterns):
        return [
            {"id": "reasoning", "label": "Understanding Your Question", "status": "waiting"},
            {"id": "policy-check", "label": "Checking Topic Scope", "status": "waiting"},
            {"id": "intent-routing", "label": "Selecting Tutoring Approach", "status": "waiting"},
            {"id": "response-gen", "label": "Crafting Explanation", "status": "waiting"},
        ]
    
    # Math queries - specialized steps
    math_patterns = ["calculate", "derive", "proof", "formula", "solve", "equation", "math"]
    if any(p in query_lower for p in math_patterns):
        return [
            {"id": "reasoning", "label": "Analyzing Problem", "status": "waiting"},
            {"id": "policy-check", "label": "Validating Request", "status": "waiting"},
            {"id": "intent-routing", "label": "Selecting Math Solver", "status": "waiting"},
            {"id": "response-gen", "label": "Solving", "status": "waiting"},
        ]
    
    # Code queries - specialized steps
    code_patterns = ["code", "python", "implement", "debug", "function", "program"]
    if any(p in query_lower for p in code_patterns):
        return [
            {"id": "reasoning", "label": "Understanding Request", "status": "waiting"},
            {"id": "policy-check", "label": "Checking Guidelines", "status": "waiting"},
            {"id": "intent-routing", "label": "Selecting Code Helper", "status": "waiting"},
            {"id": "response-gen", "label": "Writing Code", "status": "waiting"},
        ]
    
    # Syllabus/course logistics queries - still show pipeline
    syllabus_patterns = ["syllabus", "schedule", "due date", "exam date", "assignment due", "office hours"]
    if any(p in query_lower for p in syllabus_patterns):
        return [
            {"id": "reasoning", "label": "Understanding Query", "status": "waiting"},
            {"id": "intent-routing", "label": "Routing to Course Info", "status": "waiting"},
            {"id": "response-gen", "label": "Finding Information", "status": "waiting"},
        ]
    
    # Quick factual questions - still show reasoning
    quick_patterns = ["briefly", "quick", "short", "one sentence"]
    if any(p in query_lower for p in quick_patterns):
        return [
            {"id": "reasoning", "label": "Analyzing Request", "status": "waiting"},
            {"id": "response-gen", "label": "Answering", "status": "waiting"},
        ]
    
    # Educational "what is X" questions - show full chain of thought
    educational_patterns = ["what is", "what are", "what's", "how does", "how do", "why does", "why do", 
                           "explain", "describe", "tell me about", "define"]
    if any(p in query_lower for p in educational_patterns):
        return [
            {"id": "reasoning", "label": "Understanding Question", "status": "waiting"},
            {"id": "policy-check", "label": "Validating Topic", "status": "waiting"},
            {"id": "intent-routing", "label": "Selecting Approach", "status": "waiting"},
            {"id": "response-gen", "label": "Generating Explanation", "status": "waiting"},
        ]
    
    # Default for any other query - show full pipeline for transparency
    return [
        {"id": "reasoning", "label": "Analyzing Query", "status": "waiting"},
        {"id": "policy-check", "label": "Checking Guidelines", "status": "waiting"},
        {"id": "intent-routing", "label": "Routing Request", "status": "waiting"},
        {"id": "response-gen", "label": "Generating Response", "status": "waiting"},
    ]


async def astream_agent(
    query: str, 
    user_id: str = None, 
    user_email: str = None, 
    session_id: str = None,
    chat_id: str = None,
    conversation_history: List[Dict[str, Any]] = None,
    model: str = None
):
    """
    Async generator that streams agent events using astream_events (v2)
    
    Args:
        query: User query
        user_id: Optional user ID
        user_email: Optional user email
        session_id: Optional session ID for Langfuse session grouping
        chat_id: Optional chat ID for persistence
        conversation_history: Optional list of prior messages [{role, content, created_at}]
        model: Optional model to use (e.g., 'gemini-2.0-flash', 'gpt-4.1-mini')
    """
    agent = get_tutor_agent()
    
    # Get Langfuse handler
    langfuse_handler = get_langfuse_handler()
    callbacks = [langfuse_handler] if langfuse_handler else []
    
    # Create Langfuse trace for observability with session grouping
    span = create_trace(
        name="tutor_agent_stream",
        user_id=user_id,
        session_id=session_id,
        metadata={
            "user_email": user_email,
            "chat_id": chat_id,
            "history_length": len(conversation_history) if conversation_history else 0,
            "model_override": model,
        },
        input_data={
            "query": query,
            "user_email": user_email,
            "chat_id": chat_id,
            "history_length": len(conversation_history) if conversation_history else 0,
            "model_override": model,
        }
    )
    
    trace_id = span.trace_id if span else None
    
    # Track accumulated response for final output
    accumulated_response = ""
    
    # Use OpenTelemetry context
    from opentelemetry import trace
    
    # Build message history from conversation_history
    messages = []
    if conversation_history:
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                # For assistant messages, use a simple AI message
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=content))
    
    # Add current user message
    messages.append(HumanMessage(content=query))
    
    # Initialize state with all required fields including new pedagogical state
    initial_state: AgentState = {
        # User input
        "messages": messages,
        "query": query,
        
        # User context
        "user_id": user_id,
        "user_email": user_email,
        "user_role": "student",
        "trace_id": trace_id,
        "parent_observation_id": span.id if span else None,  # For linking child spans
        
        # Session/history context (NEW)
        "session_id": session_id,
        "chat_id": chat_id,
        "conversation_history": conversation_history,
        
        # Routing decisions
        "intent": None,
        "model_selected": model,  # User-specified model override (or None to auto-select)
        "model_override": model,  # Track if user overrode model selection
        
        # Reasoning node output (NEW - LLM-first architecture)
        "reasoning_complete": False,
        "reasoning_intent": None,
        "reasoning_confidence": None,
        "reasoning_strategy": None,
        "reasoning_context_needed": None,
        "reasoning_trace": None,
        
        # Context engineering (NEW)
        "curated_context": None,
        "context_budget_tokens": None,
        "context_relevance_scores": None,
        
        # RAG context
        "retrieved_context": [],
        "context_sources": [],
        
        # Policy enforcement
        "governor_approved": False,
        "governor_reason": None,
        
        # Pedagogical state
        "scaffolding_level": None,
        "student_confusion_detected": False,
        "thinking_steps": None,
        "bloom_level": None,
        "pedagogical_approach": None,
        
        # Sub-agent outputs
        "syllabus_check": None,
        "math_explanation": None,
        "math_derivation": None,
        "code_suggestion": None,
        "pedagogical_strategy": None,
        
        # Final response
        "response": None,
        "response_sources": [],
        
        # Error handling
        "error": None,
    }
    
    # Emit trace_id first so client can reference it
    if trace_id:
        yield {"type": "trace-id", "traceId": trace_id}
    
    # Intelligently select queue steps based on query complexity
    # This provides a better UX by showing relevant steps only
    queue_steps = _get_intelligent_queue_steps(query)
    
    if queue_steps:
        yield {"type": "queue-init", "queue": queue_steps}
    
    # Thinking block filter state (tracks if we're inside <thinking>...</thinking>)
    thinking_filter = {"inside_thinking": False, "buffer": ""}
    
    # Stream events
    try:
        # Define the iterator
        iterator = agent.astream_events(initial_state, version="v2", config={"callbacks": callbacks})
        
        # Wrap iteration with OTel span if available
        if span and hasattr(span, "_otel_span"):
            with trace.use_span(span._otel_span, end_on_exit=False):
                async for event in iterator:
                    # Dynamic Trace Naming: Update trace name with detected intent
                    if event["event"] == "on_chain_end" and event.get("name") == "supervisor":
                        output = event["data"].get("output", {})
                        intent = output.get("intent")
                        if intent and span:
                            span.update_trace(name=f"tutor_agent_stream_{intent}")
                            
                    result = await _process_event(event, thinking_filter)
                    # Track accumulated response for trace output
                    if isinstance(result, dict) and result.get("type") == "text-delta":
                        accumulated_response += result.get("textDelta", "")
                    # Handle cases where _process_event returns multiple events
                    if isinstance(result, list):
                        for r in result:
                            if isinstance(r, dict) and r.get("type") == "text-delta":
                                accumulated_response += r.get("textDelta", "")
                            yield r
                    else:
                        yield result
        else:
            async for event in iterator:
                # Dynamic Trace Naming: Update trace name with detected intent
                if event["event"] == "on_chain_end" and event.get("name") == "supervisor":
                    output = event["data"].get("output", {})
                    intent = output.get("intent")
                    if intent and span:
                        span.update_trace(name=f"tutor_agent_stream_{intent}")
                        
                result = await _process_event(event, thinking_filter)
                # Track accumulated response for trace output
                if isinstance(result, dict) and result.get("type") == "text-delta":
                    accumulated_response += result.get("textDelta", "")
                if isinstance(result, list):
                    for r in result:
                        if isinstance(r, dict) and r.get("type") == "text-delta":
                            accumulated_response += r.get("textDelta", "")
                        yield r
                else:
                    yield result
                
        if span:
            # Update trace with final output before ending
            span.update(output={
                "response": accumulated_response[:500] if accumulated_response else None,  # Truncate for storage
                "response_length": len(accumulated_response),
                "completed": True
            })
            span.end()
            # Flush Langfuse to ensure data is sent
            flush_langfuse()
            
    except Exception as e:
        logger.error(f"Error in stream agent: {e}")
        if span:
            span.update(output={"error": str(e), "response": accumulated_response[:500] if accumulated_response else None}, level="ERROR")
            span.end()
            flush_langfuse()
        yield {"type": "error", "error": str(e)}

def _filter_thinking_blocks(content: str, state: dict) -> str:
    """
    Filter out <thinking>...</thinking> blocks from streamed content.
    
    Handles tags that span multiple chunks by using a buffer.
    
    Args:
        content: The new content chunk
        state: Dict with 'inside_thinking' (bool) and 'buffer' (str)
        
    Returns:
        Filtered content (empty string if inside thinking block)
    """
    # Combine buffer with new content
    text = state.get("buffer", "") + content
    state["buffer"] = ""
    
    result = []
    i = 0
    
    while i < len(text):
        if state["inside_thinking"]:
            # Look for </thinking>
            end_tag = "</thinking>"
            end_pos = text.find(end_tag, i)
            if end_pos != -1:
                # Found end tag, skip everything up to and including it
                i = end_pos + len(end_tag)
                state["inside_thinking"] = False
            else:
                # Check for partial end tag at the end
                for j in range(1, len(end_tag)):
                    if text.endswith(end_tag[:j]):
                        state["buffer"] = text[-j:]
                        return "".join(result).strip()
                # Still inside thinking block, skip rest
                return "".join(result).strip()
        else:
            # Look for <thinking>
            start_tag = "<thinking>"
            start_pos = text.find(start_tag, i)
            if start_pos != -1:
                # Found start tag, emit content before it
                if start_pos > i:
                    result.append(text[i:start_pos])
                i = start_pos + len(start_tag)
                state["inside_thinking"] = True
            else:
                # Check for partial start tag at the end
                for j in range(1, len(start_tag)):
                    if text[i:].endswith(start_tag[:j]):
                        # Buffer the partial tag, emit content before it
                        result.append(text[i:-j])
                        state["buffer"] = text[-j:]
                        return "".join(result).strip()
                # No thinking tag, emit remaining content
                result.append(text[i:])
                break
    
    return "".join(result).strip()


async def _process_event(event, thinking_filter=None):
    """Helper to process events and emit structured AI SDK format
    
    Args:
        event: The LangGraph event
        thinking_filter: Optional dict with keys 'inside_thinking' and 'buffer' for tracking <thinking> blocks
    """
    kind = event["event"]
    
    if kind == "on_chat_model_stream":
        # Get context about this event
        tags = event.get("tags", []) or []
        run_name = event.get("name", "")
        metadata = event.get("metadata", {}) or {}
        parent_ids = event.get("parent_ids", []) or []
        
        # Convert tags to lowercase for matching
        tags_lower = [t.lower() if isinstance(t, str) else str(t).lower() for t in tags]
        parent_str = str(parent_ids).lower()
        
        # Skip streaming from internal components (reasoning node, etc.)
        # The reasoning node uses an LLM for analysis but output shouldn't stream to user
        is_internal_output = (
            # Check tags for internal markers
            "reasoning_internal" in tags_lower or
            "no_stream" in tags_lower or
            # Check parent chain
            "reasoning" in parent_str or
            "multi_step_reasoning" in parent_str or
            # Check run name
            "reasoningengine" in run_name.lower() or
            # Check metadata
            metadata.get("langgraph_node") == "reasoning" or
            metadata.get("internal") is True or
            metadata.get("component") == "reasoning_engine"
        )
        
        if is_internal_output:
            return {"type": "ping"}  # Skip internal output
        
        # Get the content chunk - handle Gemini 2.5+ list format
        chunk = event["data"]["chunk"]
        raw_content = chunk.content if chunk.content else ""
        
        # Handle list content format from Gemini 2.5+
        if isinstance(raw_content, list):
            text_parts = []
            for block in raw_content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = ''.join(text_parts)
        else:
            content = raw_content if isinstance(raw_content, str) else str(raw_content) if raw_content else ""
        
        # Additional content-based filtering for any leaked internal content
        if content and content.strip():
            content_stripped = content.strip()
            # Filter out JSON analysis blocks that look like reasoning output
            if (content_stripped.startswith('{"perception"') or 
                content_stripped.startswith('{"analysis"') or
                (content_stripped.startswith('```') and 'perception' in content_stripped.lower()) or
                ('"query_type"' in content and '"topic_domain"' in content)):
                return {"type": "ping"}  # Skip reasoning JSON leakage
        
        # Handle <thinking> block filtering with streaming support
        if thinking_filter is not None:
            content = _filter_thinking_blocks(content, thinking_filter)
            if not content:
                return {"type": "ping"}
        
        if content:
            return {"type": "text-delta", "textDelta": content}
    
    elif kind == "on_chain_start":
        # Emit queue-update for major pipeline stages
        name = event.get("name", "")
        
        # Map node names to queue IDs (updated for reasoning node)
        queue_mapping = {
            "governor": "policy-check",
            "reasoning": "reasoning",  # NEW
            "supervisor": "intent-routing",
            "pedagogical_tutor": "response-gen",
            "math_agent": "response-gen",
            "agent": "response-gen",
            "evaluator": "quality-check",
        }
        
        if name in queue_mapping:
            return {
                "type": "queue-update",
                "queueItemId": queue_mapping[name],
                "status": "processing"
            }
    
    elif kind == "on_chain_end":
        # Emit queue-update for major pipeline stages
        name = event.get("name", "")
        
        queue_mapping = {
            "governor": "policy-check",
            "reasoning": "reasoning",  # NEW
            "supervisor": "intent-routing", 
            "pedagogical_tutor": "response-gen",
            "math_agent": "response-gen",
            "agent": "response-gen",
            "evaluator": "quality-check",
        }
        
        if name in queue_mapping:
            result = [{
                "type": "queue-update",
                "queueItemId": queue_mapping[name],
                "status": "completed"
            }]
            
            # === NEW: Emit Chain-of-Thought from reasoning node ===
            # Based on "Chain-of-Thought Prompting Elicits Reasoning" paper
            # This shows the actual reasoning steps to users for transparency
            if name == "reasoning":
                output = event["data"].get("output", {})
                if output and isinstance(output, dict):
                    thought_chain = output.get("thought_chain", [])
                    if thought_chain:
                        logger.info(f"🧠 Emitting {len(thought_chain)} chain-of-thought steps")
                        result.append({
                            "type": "chain-of-thought",
                            "thoughts": thought_chain
                        })
                    # Also emit key concepts detected for context
                    key_concepts = output.get("key_concepts_detected", [])
                    if key_concepts:
                        result.append({
                            "type": "concepts-detected",
                            "concepts": key_concepts
                        })
            
            # Special handling for pedagogical_tutor and math_agent
            # These nodes use model.invoke() (not streaming) so we need to emit
            # their response as text-delta events here
            if name in ["pedagogical_tutor", "math_agent"]:
                output = event["data"].get("output", {})
                if output and isinstance(output, dict):
                    response = output.get("response", "")
                    if response:
                        # Filter out <thinking> blocks from non-streaming responses
                        import re
                        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
                        response = response.strip()
                        if response:
                            logger.info(f"📤 Emitting response from {name}: {len(response)} chars")
                            result.append({
                                "type": "text-delta",
                                "textDelta": response
                            })
                        # Also emit sources if available
                        sources = output.get("response_sources") or []
                        if sources:
                            result.append({
                                "type": "sources",
                                "sources": sources
                            })
            
            # Special handling for evaluator output (scores)
            if name == "evaluator":
                output = event["data"].get("output", {})
                logger.debug(f"Evaluator output keys: {output.keys() if isinstance(output, dict) else type(output)}")
                if output and isinstance(output, dict):
                    evaluation = output.get("evaluation")
                    if evaluation:
                        logger.info(f"📤 Emitting evaluation: agent={evaluation.get('agent_used')}")
                        result.append({"type": "evaluation", "evaluation": evaluation})
                    else:
                        logger.warning("Evaluator output missing 'evaluation' key")
            
            return result if len(result) > 1 else result[0]
    
    elif kind == "on_tool_start":
        # Emit both tool-call and queue-add for tools
        tool_name = event["name"]
        tool_input = event["data"].get("input")
        tool_id = f"tool-{event.get('run_id', tool_name)[:8]}"
        
        return {
            "type": "tool-call",
            "toolId": tool_id,
            "toolName": tool_name,
            "toolInput": tool_input,
            "timestamp": event.get("metadata", {}).get("start_time", None)
        }
        
    elif kind == "on_tool_end":
        tool_name = event["name"]
        tool_id = f"tool-{event.get('run_id', tool_name)[:8]}"
        output = event["data"].get("output")
        
        # Generic tool result
        result = {
            "type": "tool-result",
            "toolId": tool_id,
            "toolName": tool_name,
            "toolOutput": str(output) if output else None,
            "timestamp": event.get("metadata", {}).get("end_time", None)
        }
        
        # Special handling for sources from retrieval
        if tool_name == "retrieve_context":
            # Handle ToolMessage or other wrappers
            if hasattr(output, "artifact") and isinstance(output.artifact, list):
                output = output.artifact
            elif hasattr(output, "content"):
                try:
                    output = json.loads(output.content)
                except:
                    pass
            
            if isinstance(output, list):
                # Use standardized source extraction
                extracted_sources = extract_sources(output)
                
                # Format for frontend
                sources = []
                for i, src in enumerate(extracted_sources):
                    if src.filename != "Unknown":
                        sources.append({
                            "id": f"src-{i+1}",
                            "source_file": src.filename,
                            "title": src.filename.replace("_", " ").replace(".pdf", ""),
                            "page": src.page_number or src.chunk_index,
                            "content": src.content_preview + "..." if src.content_preview else "",
                            "description": src.content_preview[:100] if src.content_preview else "",
                            "url": src.url  # Include the deep link URL
                        })
                
                if sources:
                    # Emit separate sources event
                    return [
                        result,
                        {"type": "sources", "sources": sources}
                    ]
        
        return result
    
    elif kind == "on_retriever_start":
        return {
            "type": "queue-add",
            "queueItem": {
                "id": "retrieval",
                "label": "Searching course materials",
                "status": "processing"
            }
        }
    
    elif kind == "on_retriever_end":
        return {
            "type": "queue-update",
            "queueItemId": "retrieval",
            "status": "completed"
        }
        
    return {"type": "ping"} # Keepalive/ignored


