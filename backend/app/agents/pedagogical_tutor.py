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
from app.config import settings

logger = logging.getLogger(__name__)


# Concept detection patterns (shared with evaluator)
CONCEPT_PATTERNS = {
    "backpropagation": r"\b(backprop\w*|back.?propagation|chain.?rule|error.?propagation)\b",
    "gradient_descent": r"\b(gradient.?descent|learning.?rate|optimization|minimize|converge)\b",
    "neural_networks": r"\b(neural.?network\w*|perceptron|hidden.?layer|deep.?learning|ann)\b",
    "classification": r"\b(classification|classify|classifier|decision.?tree|knn|k-nearest|svm|support.?vector|naive.?bayes)\b",
    "regression": r"\b(regression|regress\w*|linear.?model|polynomial|predict.*(continuous|number|value))\b",
    "clustering": r"\b(cluster\w*|k-?means|hierarchical|unsupervised|grouping)\b",
    "probability": r"\b(bayes|probability|prior|posterior|conditional|likelihood)\b",
    "supervised_learning": r"\b(supervised|labeled.?data|training.?labels|target.?variable)\b",
    "unsupervised_learning": r"\b(unsupervised|unlabeled|clustering|dimensionality)\b",
    "model_evaluation": r"\b(accuracy|precision|recall|f1|confusion.?matrix|cross.?validation|overfit\w*)\b",
}


async def get_student_mastery(user_id: str, concept_tag: str) -> Optional[float]:
    """
    Fetch student's mastery score for a concept from Supabase
    
    Args:
        user_id: Student's user ID (UUID)
        concept_tag: The concept to check mastery for
        
    Returns:
        Mastery score (0.0-1.0) or None if not found
    """
    if not user_id or not concept_tag:
        return None
        
    try:
        from supabase import create_client
        
        if not settings.supabase_url or not settings.supabase_service_role_key:
            logger.debug("Supabase not configured, skipping mastery lookup")
            return None
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        result = supabase.table("student_mastery").select("mastery_score").eq(
            "user_id", user_id
        ).eq(
            "concept_tag", concept_tag
        ).execute()
        
        if result.data and len(result.data) > 0:
            mastery = result.data[0].get("mastery_score", 0.0)
            logger.info(f"📊 Fetched mastery for {concept_tag}: {mastery:.2f}")
            return mastery
        
        return None
        
    except Exception as e:
        logger.debug(f"Could not fetch mastery (non-blocking): {e}")
        return None


def detect_concept_from_query(query: str) -> Optional[str]:
    """Detect AI/ML concept from query text"""
    query_lower = query.lower()
    for concept, pattern in CONCEPT_PATTERNS.items():
        if re.search(pattern, query_lower, re.IGNORECASE):
            return concept
    return None


# Confusion detection patterns
CONFUSION_SIGNALS = [
    r"\bconfused?\b",
    r"\bdon'?t (understand|get|know)\b",
    r"\b(need|want) help\b",
    r"\bstuck\b",
    r"\blost\b",
    r"\bstruggling?\b",
    r"\bcan'?t (figure|work|get)\b",
    r"\bhaving trouble\b",
    r"\bnot (sure|clear)\b",
    r"\bwhat.*(wrong|missing)\b",
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


# Patterns to detect user's depth preference from their response
QUICK_ANSWER_PATTERNS = [
    r"\bquick(ly)?\b",
    r"\bbrief(ly)?\b",
    r"\bshort\b",
    r"\bjust (the )?answer\b",
    r"\bone (sentence|line|word)\b",
    r"\btl;?dr\b",
    r"\bsimple\b",
    r"\bin a nutshell\b",
]

DETAILED_ANSWER_PATTERNS = [
    r"\bdetail(ed|s)?\b",
    r"\bexplain (in depth|fully|completely)\b",
    r"\bdeep(er)?\s*(dive|breakdown|explanation)?\b",
    r"\bwalk me through\b",
    r"\bstep by step\b",
    r"\bthoroughly\b",
    r"\bunderstand (it )?better\b",
    r"\bmore (about|info|information)\b",
    r"\bin depth\b",
]


def strip_thinking_blocks(text: str) -> str:
    """
    Remove <thinking>...</thinking> blocks from response text.
    
    These blocks are internal reasoning from the LLM and should NOT
    be shown to users. They also cause Markdown parser errors in the frontend.
    
    Args:
        text: Raw response from LLM
        
    Returns:
        Cleaned text with thinking blocks removed
    """
    if not text:
        return text
    
    # Pattern matches <thinking>...</thinking> including newlines
    pattern = r'<thinking>.*?</thinking>\s*'
    cleaned = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Also strip any leftover standalone tags
    cleaned = re.sub(r'</?thinking>\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Strip leading whitespace that may remain
    return cleaned.strip()


def strip_scaffolding_labels(text: str) -> str:
    """
    Remove visible scaffolding labels from response text.
    
    Labels like **Activation:**, **Exploration:**, **Guidance:** are internal
    pedagogical structure and make responses feel robotic when visible.
    
    UPDATED (Dec 2025): These are internal framework labels, not user-facing.
    
    Args:
        text: Response text potentially containing scaffolding labels
        
    Returns:
        Cleaned text with scaffolding labels removed
    """
    if not text:
        return text
    
    # Remove common scaffolding labels (with or without markdown bold)
    scaffolding_patterns = [
        r'\*\*Activation:\*\*\s*',
        r'\*\*Exploration:\*\*\s*',
        r'\*\*Guidance:\*\*\s*',
        r'\*\*Challenge:\*\*\s*',
        r'\*\*Verification:\*\*\s*',
        r'\*\*Connection:\*\*\s*',
        r'\*\*Understanding:\*\*\s*',
        r'Activation:\s*',
        r'Exploration:\s*',
        r'Guidance:\s*',
        r'Challenge:\s*',
        r'Verification:\s*',
        r'Connection:\s*',
        r'Understanding:\s*',
    ]
    
    cleaned = text
    for pattern in scaffolding_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up any resulting double newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()


def detect_depth_preference(query: str) -> Optional[str]:
    """
    Detect if user has indicated a preference for quick vs detailed answer.
    
    Returns:
        "quick" - user wants a brief answer
        "detailed" - user wants an in-depth explanation
        None - no clear preference detected
    """
    query_lower = query.lower()
    
    # Check for quick patterns
    for pattern in QUICK_ANSWER_PATTERNS:
        if re.search(pattern, query_lower):
            return "quick"
    
    # Check for detailed patterns
    for pattern in DETAILED_ANSWER_PATTERNS:
        if re.search(pattern, query_lower):
            return "detailed"
    
    return None


def should_ask_diagnostic(
    state: AgentState,
    query: str,
    confusion_score: float
) -> tuple[bool, Optional[str]]:
    """
    Determine if we should ask a diagnostic question before teaching.
    
    Returns:
        Tuple of (should_ask, diagnostic_question)
    """
    # Don't ask diagnostic if already asked in this conversation
    if state.get("diagnostic_asked", False):
        return False, None
    
    # CRITICAL: Don't ask diagnostic for follow-ups - they need immediate help
    if state.get("is_follow_up", False):
        return False, None
    
    # Don't ask if user already expressed a preference
    if state.get("user_depth_preference"):
        return False, None
    
    # Check if query already contains depth preference
    depth_pref = detect_depth_preference(query)
    if depth_pref:
        return False, None
    
    # Don't ask diagnostic for very short queries (likely follow-ups)
    if len(query.split()) < 4:
        return False, None
    
    # Don't ask if moderate-to-high confusion - user needs immediate help
    # Threshold lowered to 0.5 to be more responsive to confusion signals
    if confusion_score >= 0.5:
        return False, None
    
    # Check conversation history length - don't ask on follow-ups
    conversation_history = state.get("conversation_history", []) or []
    if len(conversation_history) > 2:
        return False, None
    
    # Generate appropriate diagnostic question
    if "what is" in query.lower() or "explain" in query.lower():
        diagnostic = "Do you want a **quick answer** (1-2 sentences) or a **deeper breakdown** with examples?"
    else:
        diagnostic = "Before I explain, would you prefer a **brief overview** or should I **walk you through it step-by-step**?"
    
    return True, diagnostic


# Legacy prompt kept for Langfuse fallback compatibility
# New code uses PromptBuilder for adaptive prompting
SOCRATIC_TUTOR_PROMPT = """You are a Socratic AI tutor for COMP 237: Introduction to AI at Centennial College.
Your role is to guide students toward understanding through thoughtful scaffolding.

{response_guidance}

## Adaptive Scaffolding:

**Student shows CONFUSION:**
1. Acknowledge: "That's a common point of confusion"
2. Give clearer explanation with simpler analogy
3. Provide step-by-step breakdown
4. Check: "Does this help clarify?"

**Student has BASELINE understanding:**
1. Affirm and build: "Good foundation! Now let's see..."
2. Add complexity with guiding questions
3. Challenge with edge cases

**NEW student (no mastery data):**
1. Assume novice - give full explanations
2. Use everyday analogies
3. Build confidence before challenging

## DO:
- Lead with clarity, follow with curiosity
- Cite sources: (From: Week X)
- Make complex ideas accessible
- Be warm and encouraging

## Context:
{context}

## Student's Question:
{query}

{scaffolding_guidance}
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
    
    # Calculate base confusion score (0-1)
    confidence = min(1.0, confusion_count / 3.0)
    
    # Boost score for intensifiers (signals strong confusion)
    intensifiers = ["at all", "totally", "completely", "really", "so", "very", "absolutely"]
    for intensifier in intensifiers:
        if intensifier in query_lower:
            confidence = min(1.0, confidence + 0.25)
            break
    
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
    previous_mastery: Optional[float] = None,
    depth_preference: Optional[str] = None
) -> ScaffoldingLevel:
    """
    Select appropriate scaffolding level based on student signals
    
    Implements Zone of Proximal Development (ZPD) theory
    """
    # If user explicitly requested quick answer, use minimal scaffolding
    if depth_preference == "quick":
        return "hint"
    
    # If user explicitly requested detailed answer, use more scaffolding
    if depth_preference == "detailed":
        return "explained"
    
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
    
    Implements Socratic scaffolding with stochastic exploration.
    For follow-ups, uses lighter scaffolding to avoid verbose responses.
    """
    logger.info("📚 Pedagogical Tutor: Analyzing student query")
    start_time = time.time()
    
    # Use effective_query (contextualized) if available, otherwise original query
    query = state.get("effective_query") or state.get("query", "")
    query_lower = query.lower()
    retrieved_context = state.get("retrieved_context", [])
    conversation_history = state.get("conversation_history", []) or []
    
    # CRITICAL: Check if this is a follow-up to avoid verbose responses
    is_follow_up = state.get("is_follow_up", False)
    response_length_hint = state.get("response_length_hint", "standard")
    
    if is_follow_up:
        logger.info(f"📚 Tutor: FOLLOW-UP detected (length_hint={response_length_hint}) - using lighter scaffolding")
    
    # CRITICAL: Fetch RAG context if not already present
    # The pedagogical tutor needs course materials to provide accurate information
    if not retrieved_context:
        logger.info("📚 Tutor: No context available - fetching from RAG")
        from app.agents.sub_agents import RAGAgent
        rag_agent = RAGAgent()
        retrieved_context = rag_agent.retrieve_context(query, state=state)  # Pass state for Langfuse tracing
        logger.info(f"📚 Tutor: Retrieved {len(retrieved_context)} documents")
    
    # Early check: Practice problem requested without context
    practice_keywords = ["practice", "problem", "quiz", "test", "exercise", "try"]
    is_practice_request = any(kw in query_lower for kw in practice_keywords)
    has_no_context = not retrieved_context and len(conversation_history) < 2
    
    if is_practice_request and has_no_context:
        # Return helpful prompt asking what topic to practice
        logger.info("📚 Tutor: Practice problem requested but no context - asking for topic")
        practice_prompt = """I'd be happy to give you a practice problem! To make sure it's relevant, could you tell me which topic you'd like to practice?

**Suggestions from the course:**
- Neural Networks (perceptrons, activation functions, backpropagation)
- Search Algorithms (BFS, DFS, A*)
- Machine Learning (classification, regression, clustering)
- Gradient Descent (learning rate, convergence)
- Natural Language Processing (text processing, sentiment analysis)

Which area interests you?"""
        
        return {
            "response": practice_prompt,
            "response_sources": [],
            "scaffolding_level": "guided",
            "processing_times": {"pedagogical_tutor": (time.time() - start_time) * 1000}
        }
    
    # Create observation as child of root trace (v3 pattern)
    from app.observability.langfuse_client import create_child_span_from_state
    observation = create_child_span_from_state(
        state=state,
        name="pedagogical_tutor_agent",
        input_data={"query": query},
        metadata={
            "component": "pedagogical_tutor",
            "educational_framework": "socratic_scaffolding"
        }
    )
    
    # Step 1: Detect confusion and cognitive level
    confusion_detected, confusion_score = detect_confusion_level(query)
    bloom_level = detect_bloom_level(query)
    
    # Step 1.5: Check for depth preference from query
    depth_preference = detect_depth_preference(query) or state.get("user_depth_preference")
    
    # Step 1.6: Check if we should ask a diagnostic question first
    should_ask, diagnostic_question = should_ask_diagnostic(state, query, confusion_score)
    
    if should_ask and diagnostic_question:
        # Return diagnostic question instead of full answer
        logger.info("📚 Tutor: Asking diagnostic question before teaching")
        
        processing_time = (time.time() - start_time) * 1000
        if observation:
            update_observation_with_usage(
                observation,
                output_data={
                    "action": "diagnostic_question",
                    "diagnostic": diagnostic_question
                },
                level="DEFAULT",
                latency_seconds=processing_time / 1000.0
            )
            observation.end()
        
        return {
            "response": diagnostic_question,
            "diagnostic_asked": True,
            "scaffolding_level": None,
            "student_confusion_detected": confusion_detected,
            "bloom_level": bloom_level,
            "pedagogical_approach": None,
            "processing_times": {**(state.get("processing_times", {}) or {}), "pedagogical_tutor": processing_time}
        }
    
    # Step 2: Detect concept and fetch student mastery
    detected_concept = detect_concept_from_query(query)
    previous_mastery = None
    user_id = state.get("user_id")
    
    if detected_concept and user_id:
        import asyncio
        try:
            # Try to fetch mastery asynchronously
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new task but don't await (fire-and-forget style, get from cache)
                # For now, run synchronously since we need the result
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, get_student_mastery(user_id, detected_concept))
                    previous_mastery = future.result(timeout=1.0)
            else:
                previous_mastery = asyncio.run(get_student_mastery(user_id, detected_concept))
        except Exception as e:
            logger.debug(f"Could not fetch mastery (using defaults): {e}")
    
    # Step 3: Select scaffolding level (ZPD-based with mastery)
    scaffolding_level = select_scaffolding_level(
        confusion_detected,
        confusion_score,
        bloom_level,
        previous_mastery=previous_mastery,
        depth_preference=depth_preference
    )
    
    # Log mastery-driven decision for debugging
    if previous_mastery is not None:
        logger.info(f"🎯 Mastery-driven scaffolding: {detected_concept}={previous_mastery:.2f} → {scaffolding_level}")
    
    # Step 4: Select pedagogical approach
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
    
    # Step 6: Generate response using adaptive prompt builder
    supervisor = Supervisor()
    model = supervisor.get_model("gemini-flash")  # Use fast model but with high temperature for exploration
    
    # Detect frustrated/negation follow-ups (e.g., "no", "still don't get it")
    # These require ULTRA-SHORT clarification mode
    is_frustrated_followup = False
    if is_follow_up:
        frustrated_patterns = [
            r"^no\.?!?$", r"^nope\.?!?$", r"^not\s+really\.?$",
            r"^(i\s+)?still\s+(don'?t|can'?t)\s+(get|understand)",
            r"^(that|it|this)\s+(doesn'?t|don'?t)\s+make\s+sense",
            r"^(i'?m\s+)?(still\s+)?confused\.?!?$", r"^huh\??$", r"^what\??$",
        ]
        is_frustrated_followup = any(re.search(p, query_lower, re.IGNORECASE) for p in frustrated_patterns)
    
    # Add scaffolding guidance to prompt - LIGHTER for follow-ups, ULTRA-LIGHT for frustrated follow-ups
    if is_frustrated_followup:
        # FRUSTRATED FOLLOW-UP: Ultra-short clarification mode
        logger.info("📚 Tutor: FRUSTRATED FOLLOW-UP detected - using ultra-short clarification mode")
        scaffolding_guidance = f"""
## CRITICAL: FRUSTRATED STUDENT - ULTRA-SHORT CLARIFICATION MODE
The student said "{query}" after your previous explanation. They are frustrated or still confused.
This is NOT a request for a new lesson. This is a cry for help.

## YOUR RESPONSE MUST BE:
- **MAXIMUM 3-4 sentences** (not paragraphs - SENTENCES)
- **PINPOINT the likely confusion**: What ONE thing might they be stuck on?
- **ONE simpler analogy** or **ONE key clarification**
- **ONE specific question** to identify exactly what's confusing

## Example of GOOD response:
"I hear you. Let me try a different angle: [1-sentence simpler explanation]. Is it the [specific aspect A] or the [specific aspect B] that's tripping you up?"

## Example of BAD response:
[Any response longer than 4 sentences, or one that repeats the full explanation, or adds diagrams/quizzes]

## DO NOT:
- Start a new lesson
- Repeat what you already said
- Add diagrams, quizzes, or "next topics"
- Use any scaffolding labels (Activation/Exploration/Guidance)
"""
    elif is_follow_up:
        # Standard follow-up: Use shorter, focused scaffolding
        scaffolding_guidance = f"""
## CRITICAL: This is a FOLLOW-UP question.
The student is asking for clarification or more detail on something you ALREADY explained.
DO NOT repeat the full explanation. DO NOT start from scratch.

## Response Requirements:
- **LENGTH**: Maximum 3-4 sentences (2-3 short paragraphs)
- **FOCUS**: Address ONLY the specific point of confusion
- **NO EXTRAS**: Skip diagrams, quizzes, and "what to learn next" suggestions
- **REFERENCE**: Briefly connect to what was explained before

## Style:
- Support Level: {scaffolding_level.upper()}
- Cognitive Level: {bloom_level}
- Student Confusion: {"High - provide clearer explanation" if confusion_score > 0.5 else "Moderate - clarify specific point"}

Example of GOOD follow-up response:
"The key point is [specific clarification]. Think of it like [simpler analogy]. Does this help?"

Example of BAD follow-up response:
[Starting over with full definition, examples, diagrams, quizzes - this is what we're avoiding]
"""
    else:
        # First turn: Use full scaffolding
        scaffolding_guidance = f"""
## Adaptation Cues for This Response:
- Support Level: **{scaffolding_level.upper()}**
- Approach: **{pedagogical_approach}**
- Cognitive Level: **{bloom_level}**
- Student Confusion: {"Strong - provide more support" if confusion_score > 0.5 else "Moderate - guide with questions" if confusion_score > 0.2 else "Low - can challenge more"}

## CRITICAL: Natural Response Style
DO NOT use visible labels like "Activation:", "Exploration:", "Guidance:" in your response.
These are internal pedagogical phases - the student should NOT see them.

Instead, flow naturally:
1. Start with a hook or connection to what they know
2. **GIVE 1-2 HINTS** before full explanation (see below)
3. Build understanding progressively  
4. Include guiding questions woven into the explanation
5. End with a check-in or challenge question

## CRITICAL: ALWAYS PROVIDE HINTS FIRST
Before giving a full explanation, you MUST offer hints to help the student think:
- "Here's a hint: Think about what happens when..."
- "Consider this: How would X relate to Y?"
- "Quick hint: The key insight is related to [concept]..."
- "Let me give you a clue: What if you tried thinking about it as..."

Then pause and ask: "Want to try working it out, or should I explain further?"
This gives students a chance to discover the answer themselves.

Adjust depth based on support level:
- **HINT**: Minimal intervention. Give 2-3 guiding hints/questions. Let them discover. Example: "Here's a hint: gradient descent is like rolling a ball downhill. What do you think 'downhill' means in terms of a function?"
- **GUIDED**: Moderate support. Give 1-2 hints, then explain with questions. Example: "Quick hint: think about how errors flow backward through the network. Now, backpropagation uses the chain rule to..."
- **EXPLAINED**: Give 1 hint first, then clear explanation. Example: "Hint: classification is about categories. [Then full explanation with examples]"
- **DEMONSTRATED**: Briefly hint at the approach, then walk through example step-by-step.

Remember: Match your tone and depth to the student's needs. Sound like a helpful human tutor who FIRST gives hints to encourage thinking, not just answers.
"""

    # Use adaptive prompt builder for context-aware prompts
    from app.agents.prompt_builder import build_adaptive_prompt
    
    # Try to fetch prompt from Langfuse first (if available)
    full_prompt = ""
    try:
        from app.observability.langfuse_client import get_langfuse_client
        client = get_langfuse_client()
        if client:
            # Fetch production prompt
            langfuse_prompt = client.get_prompt("socratic-tutor-prompt")
            
            # Compile with variables
            full_prompt = langfuse_prompt.compile(
                context=context_str,
                query=query,
                scaffolding_guidance=scaffolding_guidance
            )
            logger.info("📚 Tutor: Using managed prompt 'socratic-tutor-prompt' from Langfuse")
            
            # Link generation to prompt if observation exists
            if observation:
                # Note: In a real LangChain integration, we'd pass this to the callback
                # For now, we just log that we used it
                pass
    except Exception as e:
        logger.warning(f"Failed to fetch prompt from Langfuse: {e}. Using adaptive prompt builder.")
    
    # Use adaptive prompt builder if Langfuse failed
    if not full_prompt:
        full_prompt = build_adaptive_prompt(
            state=state,
            intent="tutor",
            context_str=context_str,
            scaffolding_guidance=scaffolding_guidance
        )
        logger.info("📚 Tutor: Using adaptive prompt builder for context-aware response")
    
    try:
        # Use higher temperature for stochastic exploration
        response = model.invoke(full_prompt)
        
        # Handle Gemini 2.5+ list content format (after tool calls)
        # Content can be a list of blocks: [{'type': 'text', 'text': '...'}]
        raw_content = response.content if hasattr(response, 'content') else str(response)
        if isinstance(raw_content, list):
            text_parts = []
            for block in raw_content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif isinstance(block, str):
                    text_parts.append(block)
            response_text = ''.join(text_parts)
        else:
            response_text = raw_content if isinstance(raw_content, str) else str(raw_content)
        
        # CRITICAL: Strip <thinking> blocks from response - these are for internal reasoning
        # and should NOT be shown to the user (causes Markdown parser errors in frontend)
        response_text = strip_thinking_blocks(response_text)
        
        # CRITICAL: Strip visible scaffolding labels (Activation/Exploration/Guidance)
        # These are internal pedagogical structure and make responses feel robotic
        response_text = strip_scaffolding_labels(response_text)
        
        logger.info(f"📚 Tutor: Using {scaffolding_level} scaffolding, {pedagogical_approach} approach")
        
        # Step 8: Add "next concepts" suggestions from knowledge graph
        # SKIP for follow-ups to keep responses focused
        if detected_concept and user_id and not is_follow_up:
            try:
                from app.agents.knowledge_graph import (
                    get_next_concepts, 
                    format_next_concepts_message,
                    get_student_mastery_all
                )
                import asyncio
                
                # Get all mastery scores
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            future = pool.submit(asyncio.run, get_student_mastery_all(user_id))
                            mastery_scores = future.result(timeout=1.0)
                    else:
                        mastery_scores = asyncio.run(get_student_mastery_all(user_id))
                except Exception:
                    mastery_scores = {}
                
                # Get next concept suggestions
                next_concepts = get_next_concepts(detected_concept, mastery_scores, max_suggestions=2)
                if next_concepts:
                    next_concepts_msg = format_next_concepts_message(next_concepts)
                    response_text += next_concepts_msg
                    logger.info(f"📚 Tutor: Added {len(next_concepts)} next concept suggestions")
            except Exception as e:
                logger.debug(f"Could not add next concepts: {e}")
        
        # Step 9: Add visual diagram for the concept (if available and detailed response)
        # SKIP for follow-ups to keep responses focused
        if detected_concept and depth_preference != "quick" and scaffolding_level in ["explained", "demonstrated"] and not is_follow_up:
            try:
                from app.agents.visual_diagrams import get_diagram_for_detected_concept, format_diagram_for_response
                diagram = get_diagram_for_detected_concept(detected_concept)
                if diagram:
                    diagram_text = format_diagram_for_response(diagram, title=f"{detected_concept.replace('_', ' ').title()} Visualization")
                    response_text += diagram_text
                    logger.info(f"📚 Tutor: Added visual diagram for {detected_concept}")
            except Exception as e:
                logger.debug(f"Could not add visual diagram: {e}")
        
        # Step 10: Add quiz question for the concept (if detailed response)
        # SKIP for follow-ups to keep responses focused
        if detected_concept and depth_preference != "quick" and scaffolding_level in ["explained", "demonstrated"] and not is_follow_up:
            try:
                from app.agents.quiz_generator import get_quiz_for_concept, format_quiz_for_response
                quiz_questions = get_quiz_for_concept(detected_concept, count=1)
                if quiz_questions:
                    quiz_text = format_quiz_for_response(quiz_questions)
                    response_text += quiz_text
                    logger.info(f"📚 Tutor: Added quiz question for {detected_concept}")
            except Exception as e:
                logger.debug(f"Could not add quiz: {e}")
        
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
    
    # Build response_sources from retrieved_context
    response_sources = []
    for doc in retrieved_context[:5]:
        source_file = doc.get("source_file") or doc.get("source_filename") or doc.get("metadata", {}).get("source_file", "Unknown")
        if source_file and source_file != "Unknown":
            response_sources.append({
                "title": source_file,
                "url": doc.get("public_url", ""),
                "description": doc.get("preview", doc.get("content", "")[:100] if doc.get("content") else ""),
                "relevance_score": doc.get("relevance_score", 0.0)
            })
    
    return {
        "response": response_text,
        "response_sources": response_sources,  # Include sources for frontend
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
