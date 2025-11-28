"""
Pedagogical Tutor Agent
Implements Socratic scaffolding, stochastic thinking, and research-backed educational techniques

Based on:
- Zone of Proximal Development (ZPD) - Vygotsky
- Adaptive Pedagogical Scaffolding (APS) framework
- Bloom's Taxonomy for cognitive levels
- Socratic questioning methodology
"""

from typing import Dict, List, Optional
import logging
import time
import re
from app.agents.state import AgentState, ThinkingStep, ScaffoldingLevel, PedagogicalApproach
from app.agents.supervisor import Supervisor
from app.observability.langfuse_client import update_observation_with_usage

logger = logging.getLogger(__name__)


# Confusion detection patterns
CONFUSION_SIGNALS = [
    r"\bconfused?\b",
    r"\bdon'?t (understand|get|know)\b",
    r"\bhelp\b",
    r"\bwhat (is|are|does)\b",
    r"\bhow (do|does|can)\b",
    r"\bwhy\b",
    r"\bexplain\b",
    r"\bstuck\b",
    r"\blost\b",
    r"\bstruggling?\b",
    r"\?\s*$",  # Ends with question mark
]

# Bloom's Taxonomy keyword indicators
BLOOM_INDICATORS = {
    "remember": ["define", "list", "name", "recall", "what is"],
    "understand": ["explain", "describe", "summarize", "interpret", "how does"],
    "apply": ["apply", "use", "implement", "solve", "calculate"],
    "analyze": ["analyze", "compare", "contrast", "why", "examine"],
    "evaluate": ["evaluate", "judge", "critique", "assess", "which is better"],
    "create": ["create", "design", "develop", "propose", "build"],
}


SOCRATIC_TUTOR_PROMPT = """You are a Socratic AI tutor for COMP 237: Introduction to AI at Centennial College.
You employ research-backed pedagogical techniques to guide students toward understanding.

## Your Core Principles:

### 1. Scaffolding (Zone of Proximal Development)
- Meet students exactly where they are
- Provide just enough support to help them reach the next level
- Follow the "I do → We do → You do" progression
- Gradually reduce support as understanding grows

### 2. Socratic Questioning
- Ask probing questions rather than lecturing
- Help students discover knowledge themselves
- Challenge assumptions gently but firmly
- Use questions to reveal gaps in understanding

### 3. Stochastic Exploration
- Consider multiple explanations and angles
- Adapt dynamically based on student responses
- Try different approaches if one doesn't resonate
- Make learning feel like a discovery, not a lecture

## Your Scaffolding Strategy:

You MUST select exactly ONE scaffolding level based on the student's apparent understanding:

### HINT (Minimal support - student seems capable)
- Ask a single guiding question
- Point toward the answer without revealing it
- Trust the student to make the connection
- Example: "What happens to the gradient when we're at a local minimum?"

### GUIDED (Moderate support - student is developing)
- Provide a partial solution or framework
- Ask the student to complete the next logical step
- Walk alongside them, not ahead
- Example: "The cost function measures error. If we want LESS error, should we move WITH or AGAINST the gradient?"

### EXPLAINED (High support - student is struggling)
- Break the concept into digestible chunks
- Use analogies and visual descriptions
- Check understanding after each chunk
- Example: "Think of gradient descent like a hiker in fog trying to find a valley..."

### DEMONSTRATED (Maximum support - student is very confused)
- Show a complete worked example first
- Walk through every step with clear reasoning
- Then present a similar problem for them to try
- Example: "Let me derive backpropagation step by step, then you'll try layer 2..."

## Response Format:

<thinking>
[Assess: What's the student's current level? What signals indicate confusion or capability?]
[Explore: Consider 2-3 different ways to approach this explanation]
[Select: Choose the best pedagogical approach for THIS student at THIS moment]
</thinking>

[Your Socratic response using the selected scaffolding level]
[Use markdown formatting, code blocks for examples, and LaTeX for math: $formula$]

<follow_up>
[A probing question to verify understanding OR a practice exercise at the appropriate level]
</follow_up>

## Important Rules:
1. NEVER give complete solutions to graded assignments
2. ALWAYS cite course materials when relevant
3. PREFER questions over statements
4. CELEBRATE small victories and correct insights
5. Be warm and encouraging, but intellectually rigorous

## Context:
{context}

## Student's Question:
{query}
"""


def detect_confusion_level(query: str) -> tuple[bool, float]:
    """
    Analyze query for confusion signals
    
    Returns:
        Tuple of (confusion_detected, confidence_score)
    """
    query_lower = query.lower()
    confusion_count = 0
    
    for pattern in CONFUSION_SIGNALS:
        if re.search(pattern, query_lower):
            confusion_count += 1
    
    # Calculate confusion score (0-1)
    confidence = min(1.0, confusion_count / 3.0)
    detected = confusion_count >= 1
    
    return detected, confidence


def detect_bloom_level(query: str) -> str:
    """
    Detect the Bloom's Taxonomy level from the query
    
    Returns:
        One of: remember, understand, apply, analyze, evaluate, create
    """
    query_lower = query.lower()
    
    # Check from highest to lowest (prefer higher levels)
    for level in ["create", "evaluate", "analyze", "apply", "understand", "remember"]:
        indicators = BLOOM_INDICATORS[level]
        for indicator in indicators:
            if indicator in query_lower:
                return level
    
    # Default to "understand" for general questions
    return "understand"


def select_scaffolding_level(
    confusion_detected: bool,
    confusion_score: float,
    bloom_level: str,
    previous_mastery: Optional[float] = None
) -> ScaffoldingLevel:
    """
    Select appropriate scaffolding level based on student signals
    
    Implements Zone of Proximal Development (ZPD) theory
    """
    # If we have mastery data, use it
    if previous_mastery is not None:
        if previous_mastery > 0.8:
            return "hint"
        elif previous_mastery > 0.5:
            return "guided"
        elif previous_mastery > 0.3:
            return "explained"
        else:
            return "demonstrated"
    
    # Otherwise, use confusion signals and Bloom's level
    if confusion_score > 0.7:
        return "demonstrated"
    elif confusion_score > 0.4 or bloom_level in ["remember", "understand"]:
        return "explained"
    elif confusion_score > 0.2 or bloom_level in ["apply"]:
        return "guided"
    else:
        return "hint"


def select_pedagogical_approach(
    scaffolding_level: ScaffoldingLevel,
    bloom_level: str
) -> PedagogicalApproach:
    """
    Select pedagogical approach based on scaffolding and Bloom's level
    """
    if scaffolding_level == "hint":
        return "socratic"  # Ask probing questions
    elif scaffolding_level == "guided":
        return "scaffolded"  # Provide partial support
    elif scaffolding_level == "explained":
        return "direct"  # Explain clearly
    else:
        return "exploratory"  # Walk through with examples


def generate_thinking_steps(query: str, context: List[dict]) -> List[ThinkingStep]:
    """
    Generate stochastic thinking steps for the tutor's exploration
    
    This creates multiple potential paths the tutor could take
    """
    steps = []
    
    # Step 1: Analyze the question
    steps.append(ThinkingStep(
        step_number=1,
        thought=f"Analyzing query: '{query[:100]}...'",
        alternatives_considered=["Direct answer", "Socratic questioning", "Example-based"],
        confidence=0.8,
        selected=True
    ))
    
    # Step 2: Consider student's level
    confusion_detected, confusion_score = detect_confusion_level(query)
    steps.append(ThinkingStep(
        step_number=2,
        thought=f"Confusion detected: {confusion_detected} (score: {confusion_score:.2f})",
        alternatives_considered=None,
        confidence=confusion_score if confusion_detected else 0.7,
        selected=True
    ))
    
    # Step 3: Select approach
    bloom_level = detect_bloom_level(query)
    steps.append(ThinkingStep(
        step_number=3,
        thought=f"Bloom's level: {bloom_level}",
        alternatives_considered=list(BLOOM_INDICATORS.keys()),
        confidence=0.75,
        selected=True
    ))
    
    return steps


def pedagogical_tutor_node(state: AgentState) -> Dict:
    """
    Pedagogical Tutor node for LangGraph
    
    Implements Socratic scaffolding with stochastic exploration
    """
    logger.info("📚 Pedagogical Tutor: Analyzing student query")
    start_time = time.time()
    
    query = state.get("query", "")
    retrieved_context = state.get("retrieved_context", [])
    
    # Create observation for tracing
    observation = None
    trace_id = state.get("trace_id")
    if trace_id:
        from app.observability.langfuse_client import get_langfuse_client
        client = get_langfuse_client()
        if client:
            try:
                observation = client.start_span(
                    trace_context={"trace_id": trace_id},
                    name="pedagogical_tutor_agent",
                    input={"query": query},
                    metadata={
                        "component": "pedagogical_tutor",
                        "educational_framework": "socratic_scaffolding"
                    }
                )
            except Exception as e:
                logger.warning(f"Could not create tutor observation: {e}")
    
    # Step 1: Detect confusion and cognitive level
    confusion_detected, confusion_score = detect_confusion_level(query)
    bloom_level = detect_bloom_level(query)
    
    # Step 2: Select scaffolding level (ZPD-based)
    # TODO: Integrate with student mastery table for personalization
    scaffolding_level = select_scaffolding_level(
        confusion_detected,
        confusion_score,
        bloom_level,
        previous_mastery=None  # Would come from database
    )
    
    # Step 3: Select pedagogical approach
    pedagogical_approach = select_pedagogical_approach(scaffolding_level, bloom_level)
    
    # Step 4: Generate thinking steps (stochastic exploration)
    thinking_steps = generate_thinking_steps(query, retrieved_context)
    
    # Step 5: Build context string from RAG results
    context_parts = []
    for doc in retrieved_context[:5]:
        content = doc.get("content") or doc.get("text") or doc.get("page_content", "")
        source = doc.get("source_file") or doc.get("metadata", {}).get("source_file", "")
        context_parts.append(f"[From {source}]\n{content}")
    
    context_str = "\n\n---\n\n".join(context_parts) if context_parts else "No course materials found."
    
    # Step 6: Generate response using Socratic prompt
    supervisor = Supervisor()
    model = supervisor.get_model("gemini-flash")  # Use fast model but with high temperature for exploration
    
    prompt = SOCRATIC_TUTOR_PROMPT.format(
        context=context_str,
        query=query
    )
    
    # Add scaffolding guidance to prompt
    scaffolding_guidance = f"""
## Selected Strategy for This Response:
- Scaffolding Level: **{scaffolding_level.upper()}**
- Pedagogical Approach: **{pedagogical_approach}**
- Bloom's Level Detected: **{bloom_level}**
- Confusion Signals: {"Strong" if confusion_score > 0.5 else "Moderate" if confusion_score > 0.2 else "Low"}

Apply the {scaffolding_level.upper()} scaffolding approach as defined above.
"""
    
    full_prompt = prompt + scaffolding_guidance
    
    try:
        # Use higher temperature for stochastic exploration
        response = model.invoke(full_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"📚 Tutor: Using {scaffolding_level} scaffolding, {pedagogical_approach} approach")
        
    except Exception as e:
        logger.error(f"Error in pedagogical tutor: {e}")
        response_text = "I'd love to help you understand this concept. Could you tell me more about what's confusing you?"
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000
    
    # Update observation
    if observation:
        update_observation_with_usage(
            observation,
            output_data={
                "scaffolding_level": scaffolding_level,
                "pedagogical_approach": pedagogical_approach,
                "bloom_level": bloom_level,
                "confusion_score": confusion_score,
                "response_preview": response_text[:200] + "..."
            },
            level="DEFAULT",
            latency_seconds=processing_time / 1000.0
        )
        observation.end()
    
    # Update processing times
    processing_times = state.get("processing_times", {}) or {}
    processing_times["pedagogical_tutor"] = processing_time
    
    logger.info(f"📚 Pedagogical Tutor: Completed in {processing_time:.1f}ms")
    
    return {
        "response": response_text,
        "scaffolding_level": scaffolding_level,
        "student_confusion_detected": confusion_detected,
        "thinking_steps": thinking_steps,
        "bloom_level": bloom_level,
        "pedagogical_approach": pedagogical_approach,
        "pedagogical_strategy": f"{scaffolding_level}_{pedagogical_approach}",
        "processing_times": processing_times
    }


class PedagogicalTutor:
    """
    Class-based Pedagogical Tutor for external use
    """
    
    def __init__(self):
        self.supervisor = Supervisor()
    
    def analyze_student(self, query: str) -> dict:
        """
        Analyze student's query for pedagogical indicators
        """
        confusion_detected, confusion_score = detect_confusion_level(query)
        bloom_level = detect_bloom_level(query)
        scaffolding_level = select_scaffolding_level(
            confusion_detected, confusion_score, bloom_level
        )
        
        return {
            "confusion_detected": confusion_detected,
            "confusion_score": confusion_score,
            "bloom_level": bloom_level,
            "scaffolding_level": scaffolding_level,
            "recommended_approach": select_pedagogical_approach(scaffolding_level, bloom_level)
        }
    
    def generate_socratic_question(self, topic: str, level: str = "understand") -> str:
        """
        Generate a Socratic question for a given topic
        """
        question_templates = {
            "remember": f"Can you recall what {topic} means in the context of AI?",
            "understand": f"In your own words, how would you explain {topic}?",
            "apply": f"How would you apply {topic} to solve a real problem?",
            "analyze": f"Why do you think {topic} works the way it does?",
            "evaluate": f"What are the trade-offs of using {topic}?",
            "create": f"How might you design a new approach using {topic}?",
        }
        return question_templates.get(level, question_templates["understand"])
