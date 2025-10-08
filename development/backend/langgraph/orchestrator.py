"""
Parent Orchestrator Agent - Mode Switcher
Routes student queries to Navigate mode or Educate mode based on intent.

Navigate Mode (gemini-2.0-flash):
- Information retrieval
- External resources (YouTube, Wikipedia, OER Commons)
- Quick answers
- Scope detection

Educate Mode (gemini-2.5-flash):
- Conceptual explanations with Math Translation
- Problem-solving with scaffolded hints
- Algorithm visualization (DFS, BFS, A*, etc.)
- Code-theory bridge (formula → sklearn)
- Misconception detection
- Socratic dialogue
- Quiz generation
"""

import os
import hashlib
from functools import lru_cache
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()

# Simple in-memory cache for query classifications (avoids redundant LLM calls)
_classification_cache = {}

class OrchestratorState(TypedDict):
    """State for orchestrator agent."""
    # Input
    query: str
    student_id: str
    session_id: str
    conversation_history: list  # List of {"role": "user/assistant", "content": str, "mode": str, "timestamp": str}
    
    # Intent Analysis
    mode: Literal["navigate", "educate"]  # Determined by orchestrator
    confidence: float  # Confidence in mode selection (0-1)
    reasoning: str  # Why this mode was selected
    
    # Routing
    next_graph: Literal["navigate_graph", "educate_graph"]  # Which graph to invoke
    
    # Conversation Context (NEW)
    last_mode: str  # Previous mode used
    mode_switch_count: int  # Number of mode switches in session
    conversation_turns: int  # Total conversation turns
    is_follow_up: bool  # Is this a follow-up question?
    should_confirm: bool  # Should we ask user to confirm mode selection?
    
    # Student Context (from Supabase)
    student_context: dict  # Mastery levels, misconceptions, week number


# Mode classification keywords/patterns
NAVIGATE_INDICATORS = {
    # Explicit requests
    "find", "search", "look up", "get", "fetch", "locate",
    "show me", "give me", "what is", "who is", "when is", "where is",
    
    # Course materials
    "materials", "slides", "notes", "lecture", "content",
    "assignment", "lab", "week", "module",
    
    # External resources
    "video", "youtube", "tutorial", "article", "resource",
    "example", "documentation", "reference",
    
    # Quick info
    "definition", "overview", "summary", "introduction",
    
    # Scope-specific
    "outside", "not in course", "beyond", "unrelated"
}

EDUCATE_INDICATORS = {
    # Learning/understanding (strong signals)
    "explain", "understand", "learn", "teach", "why", "how does",
    "confused", "don't get", "struggling", "help me",
    
    # Math translation
    "formula", "equation", "math", "calculation", "derive",
    "what does this mean", "break down", "simplify",
    
    # Problem-solving (active engagement)
    "solve", "implement", "code it", "write code", "step by step",
    "walk me through", "trace", "debug",
    
    # Assessment
    "quiz me", "test me", "practice", "check my understanding",
    
    # Socratic
    "am I right", "is this correct", "does this make sense",
    
    # Study planning (personalized scheduling)
    "study plan", "create a plan", "plan my", "schedule my",
    "organize my study", "what should i study", "study schedule",
    "plan for this week", "plan for next week", "exam prep",
    "prepare for exam", "help me prepare"
}

# Follow-up indicators
FOLLOW_UP_PATTERNS = {
    "what about", "tell me more", "can you explain", "also", "additionally",
    "and", "but", "however", "more detail", "elaborate", "continue",
    "go on", "keep going", "next", "another", "anything else",
    "what if", "suppose", "imagine", "let's say"
}

# COMP-237 specific topics (always educate mode)
COMP237_CORE_TOPICS = {
    # Week 1-2
    "intelligent agent", "agent environment", "peas", "task environment",
    
    # Week 3-5
    "dfs", "bfs", "depth first search", "breadth first search",
    "uniform cost search", "ucs", "greedy search", "a* search", "a star",
    "heuristic", "admissible", "consistent",
    
    # Week 6-8
    "linear regression", "logistic regression", "gradient descent",
    "loss function", "mean squared error", "cross entropy",
    "overfitting", "underfitting", "regularization",
    "confusion matrix", "precision", "recall", "f1 score",
    
    # Week 9
    "neural network", "perceptron", "backpropagation",
    "activation function", "relu", "sigmoid", "tanh",
    
    # Week 10-11
    "naive bayes", "bayes theorem", "tf-idf", "bag of words",
    "text classification", "n-gram", "language model",
    
    # Week 12
    "computer vision", "clustering", "k-means", "mean shift",
    "rgb", "hsv", "image processing",
    
    # Week 13
    "ai ethics", "bias", "fairness"
}


def detect_follow_up(state: OrchestratorState) -> bool:
    """
    Detect if current query is a follow-up to previous conversation.
    
    Returns:
        True if this appears to be a follow-up question
    """
    import re
    
    query = state["query"].lower()
    conv_history = state.get("conversation_history", [])
    
    # No history = not a follow-up
    if not conv_history:
        return False
    
    # Check for follow-up patterns
    for pattern in FOLLOW_UP_PATTERNS:
        if pattern in query:
            return True
    
    # Check for pronouns referring to previous context (it, that, this, they, these, those)
    pronoun_pattern = r'\b(it|that|this|they|these|those|them)\b'
    if re.search(pronoun_pattern, query) and len(conv_history) > 0:
        return True
    
    # Very short queries (< 5 words) after conversation likely follow-ups
    if len(query.split()) < 5 and len(conv_history) >= 2:
        return True
    
    return False


def classify_mode(state: OrchestratorState) -> OrchestratorState:
    """
    Classify whether query should go to Navigate or Educate mode.
    
    Decision Logic:
    1. Check cache for identical queries (fast path)
    2. Check conversation context (follow-ups stay in same mode)
    3. Check for explicit navigate/educate keywords (HIGH priority)
    4. Check if query is about COMP-237 topics + educate intent
    5. Analyze query complexity and intent
    6. Use LLM for ambiguous cases with conversation history
    7. Apply confidence threshold (< 0.7 = ask for confirmation)
    
    Returns:
        Updated state with mode, confidence, reasoning
    """
    from llm_config import get_llm
    import re
    
    query = state["query"].lower()
    
    # PHASE 0: Check cache for identical queries (performance optimization)
    query_hash = hashlib.md5(query.encode()).hexdigest()
    if query_hash in _classification_cache:
        cached = _classification_cache[query_hash]
        state["mode"] = cached["mode"]
        state["confidence"] = cached["confidence"]
        state["reasoning"] = f"[CACHED] {cached['reasoning']}"
        state["next_graph"] = "navigate_graph" if state["mode"] == "navigate" else "educate_graph"
        print(f"⚡ Cache hit for query: {query[:50]}...")
        return state
    
    # Initialize conversation context tracking
    state["conversation_turns"] = len(state.get("conversation_history", []))
    state["is_follow_up"] = detect_follow_up(state)
    state["should_confirm"] = False
    
    # Get last mode from conversation history
    conv_history = state.get("conversation_history", [])
    state["last_mode"] = conv_history[-1].get("mode", "") if conv_history else ""
    
    # Count mode switches in session
    mode_switches = 0
    for i in range(1, len(conv_history)):
        if conv_history[i].get("mode") != conv_history[i-1].get("mode"):
            mode_switches += 1
    state["mode_switch_count"] = mode_switches
    
    # PHASE 1: Conversation Context - Follow-ups stay in same mode unless strong signal
    if state["is_follow_up"] and state["last_mode"]:
        # Check if there's a STRONG signal to override (navigate_score >= 2 or educate_score >= 2)
        def count_keywords(keywords, text):
            count = 0
            for keyword in keywords:
                if ' ' in keyword:
                    if keyword in text:
                        count += 1
                else:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, text):
                        count += 1
            return count
        
        navigate_score = count_keywords(NAVIGATE_INDICATORS, query)
        educate_score = count_keywords(EDUCATE_INDICATORS, query)
        
        # Strong override signal detected
        if navigate_score >= 2 or educate_score >= 2:
            pass  # Continue to keyword analysis
        else:
            # Stick with last mode for follow-ups
            state["mode"] = state["last_mode"]
            state["confidence"] = 0.85
            state["reasoning"] = f"Follow-up question, continuing in {state['last_mode'].upper()} mode"
            state["next_graph"] = "navigate_graph" if state["mode"] == "navigate" else "educate_graph"
            
            print(f"🎯 Orchestrator: {state['mode'].upper()} mode (confidence={state['confidence']:.2f})")
            print(f"   Reasoning: {state['reasoning']}")
            
            return state
    
    # PHASE 2: Continue with keyword analysis
    
    # More precise keyword matching with word boundaries
    def count_keywords(keywords, text):
        count = 0
        for keyword in keywords:
            # Use word boundaries for single words, exact match for phrases
            if ' ' in keyword:
                if keyword in text:
                    count += 1
            else:
                # Word boundary matching for single words
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text):
                    count += 1
        return count
    
    navigate_score = count_keywords(NAVIGATE_INDICATORS, query)
    educate_score = count_keywords(EDUCATE_INDICATORS, query)
    comp237_score = count_keywords(COMP237_CORE_TOPICS, query)
    
    # PRIORITY 1: Strong navigate keywords override everything
    if navigate_score >= 2:
        # "find materials", "search for slides", "show me resources"
        state["mode"] = "navigate"
        state["confidence"] = 0.9
        state["reasoning"] = f"Information retrieval request (navigate_score={navigate_score})"
    
    # PRIORITY 2: Strong educate keywords (learning intent)
    elif educate_score >= 2:
        # "explain how", "help me understand", "walk me through"
        state["mode"] = "educate"
        state["confidence"] = 0.9
        state["reasoning"] = f"Learning/tutoring request (educate_score={educate_score})"
    
    # PRIORITY 3: COMP-237 topic + educate context
    elif comp237_score > 0 and educate_score > 0:
        # "explain DFS", "how does gradient descent work"
        state["mode"] = "educate"
        state["confidence"] = 0.95
        state["reasoning"] = f"COMP-237 topic with learning intent (topic_matches={comp237_score}, educate_keywords={educate_score})"
    
    # PRIORITY 4: COMP-237 topic + navigate context
    elif comp237_score > 0 and navigate_score > 0:
        # "find DFS slides", "search for gradient descent materials"
        state["mode"] = "navigate"
        state["confidence"] = 0.9
        state["reasoning"] = f"Course material search (topic_matches={comp237_score}, navigate_keywords={navigate_score})"
    
    # PRIORITY 5: COMP-237 topic alone → use LLM to disambiguate
    elif comp237_score > 0:
        state = _llm_classify_mode(state)
    
    # PRIORITY 6: Single keyword hints
    elif navigate_score > educate_score:
        state["mode"] = "navigate"
        state["confidence"] = 0.75
        state["reasoning"] = f"Information retrieval (navigate_score={navigate_score} > educate_score={educate_score})"
    
    elif educate_score > navigate_score:
        state["mode"] = "educate"
        state["confidence"] = 0.75
        state["reasoning"] = f"Learning request (educate_score={educate_score} > navigate_score={navigate_score})"
    
    else:
        # Ambiguous - use LLM for classification
        state = _llm_classify_mode(state)
    
    # Set next graph based on mode
    state["next_graph"] = "navigate_graph" if state["mode"] == "navigate" else "educate_graph"
    
    # PHASE 4: Confidence threshold check
    if state["confidence"] < 0.7:
        state["should_confirm"] = True
        print(f"⚠️  Low confidence ({state['confidence']:.2f}) - user confirmation recommended")
    
    # Cache the result for future identical queries (max 1000 entries)
    if len(_classification_cache) < 1000:
        _classification_cache[query_hash] = {
            "mode": state["mode"],
            "confidence": state["confidence"],
            "reasoning": state["reasoning"]
        }
    
    print(f"🎯 Orchestrator: {state['mode'].upper()} mode (confidence={state['confidence']:.2f})")
    print(f"   Reasoning: {state['reasoning']}")
    print(f"   Follow-up: {state['is_follow_up']}, Mode switches: {state['mode_switch_count']}")
    
    return state


def _llm_classify_mode(state: OrchestratorState) -> OrchestratorState:
    """Use LLM to classify ambiguous queries with conversation context."""
    from llm_config import get_llm
    import json
    
    # Use fast Navigate mode model for quick classification
    llm = get_llm(temperature=0.0, mode="navigate")  # Zero temp for consistent classification
    
    # Format conversation history for context
    conv_context = ""
    recent_history = state.get('conversation_history', [])[-3:]
    if recent_history:
        conv_context = "\n\nRecent Conversation:\n"
        for msg in recent_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:100]  # Limit to first 100 chars
            mode = msg.get("mode", "")
            conv_context += f"- [{role.upper()}] ({mode} mode): {content}...\n"
    
    prompt = f"""You are a mode classifier for a COMP-237 (Artificial Intelligence) AI tutor.

**NAVIGATE MODE** - Fast retrieval (gemini-2.0-flash):
- Find course materials, slides, assignments
- External resources (YouTube videos, Wikipedia)
- Quick definitions or overviews
- Topics outside COMP-237 scope

**EDUCATE MODE** - Deep learning (gemini-2.5-flash):
- Conceptual explanations with formulas/math
- Problem-solving with step-by-step guidance
- Algorithm visualization (DFS, BFS, A*)
- Code implementation help
- Quiz generation
- COMP-237 core topics: search algorithms, ML, neural networks, NLP, computer vision, AI ethics
{conv_context}
Current Query: "{state['query']}"

Classify this query. Return ONLY valid JSON:
{{"mode": "navigate", "confidence": 0.85, "reasoning": "explanation"}}"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Try to extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        
        state["mode"] = result.get("mode", "navigate")
        state["confidence"] = float(result.get("confidence", 0.7))
        state["reasoning"] = result.get("reasoning", "LLM classification")
        
        # Validate mode value
        if state["mode"] not in ["navigate", "educate"]:
            raise ValueError(f"Invalid mode: {state['mode']}")
    
    except Exception as e:
        print(f"⚠️  LLM classification failed: {e}")
        print(f"   Response content: {response.content[:200] if 'response' in locals() else 'N/A'}")
        # Deterministic fallback when LLM fails:
        # - If the query contains COMP-237 topics or strong educate indicators, prefer Educate
        # - Otherwise prefer Navigate for retrieval
        fallback_mode = "navigate"
        # Recompute heuristics locally (avoid calling LLM)
        import re
        def _has_keyword_set(keyset, text):
            for k in keyset:
                if ' ' in k:
                    if k in text:
                        return True
                else:
                    if re.search(r'\b' + re.escape(k) + r'\b', text):
                        return True
            return False

        q = state['query'].lower()
        if _has_keyword_set(COMP237_CORE_TOPICS, q) or _has_keyword_set(EDUCATE_INDICATORS, q):
            fallback_mode = 'educate'

        state["mode"] = fallback_mode
        # Conservative confidence for fallback
        state["confidence"] = 0.65 if fallback_mode == 'educate' else 0.6
        state["reasoning"] = f"LLM classification failed; deterministic fallback → {state['mode'].upper()} mode (heuristics triggered)"
    
    return state


def orchestrator_agent(state: OrchestratorState) -> OrchestratorState:
    """
    Main orchestrator agent.
    Determines whether to route to Navigate or Educate mode.
    """
    print("\n" + "=" * 70)
    print("🎭 PARENT ORCHESTRATOR AGENT")
    print("=" * 70)
    print(f"Query: {state['query']}")
    
    # Classify mode
    state = classify_mode(state)
    
    # TODO: Load student context from Supabase
    # - Get mastery levels
    # - Get unresolved misconceptions
    # - Determine current course week
    # This will inform Educate mode agents
    
    print("=" * 70)
    print()
    
    return state


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    # Test queries
    test_queries = [
        # Navigate mode
        "Find me a video about neural networks",
        "What is the definition of reinforcement learning?",
        "Show me resources about transformers",
        
        # Educate mode
        "Explain how backpropagation works step by step",
        "I don't understand the gradient descent formula",
        "Walk me through the A* algorithm on this graph",
        "Quiz me on Week 6 topics",
        "Is linear regression for classification?",
        
        # COMP-237 core topics (always educate)
        "How does BFS work?",
        "What is the Naive Bayes formula?",
        "Implement K-means clustering"
    ]
    
    print("\n🧪 Testing Orchestrator with sample queries:\n")
    
    for i, query in enumerate(test_queries, 1):
        state = OrchestratorState(
            query=query,
            student_id="test-123",
            session_id=f"session-{i}",
            conversation_history=[],
            mode="navigate",  # Will be updated
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={}
        )
        
        result = orchestrator_agent(state)
        print()
