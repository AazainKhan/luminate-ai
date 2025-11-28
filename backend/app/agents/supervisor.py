"""
Supervisor (Router) for Course Marshal
Routes queries to appropriate models and sub-agents

Routing Strategy:
- tutor: Socratic scaffolding for conceptual understanding
- math: Step-by-step mathematical derivations
- coder: Code generation and debugging
- syllabus_query: Course logistics and schedule
- fast: Quick answers for simple queries
"""

from typing import Dict
import logging
import time
import re
from app.agents.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.config import settings
from app.observability import get_langfuse_handler
from app.observability.langfuse_client import (
    create_observation,
    update_observation_with_usage
)

logger = logging.getLogger(__name__)


# Intent detection patterns
INTENT_PATTERNS = {
    "math": [
        r"\bderive\b", r"\bderivative\b", r"\bintegral\b",
        r"\bformula\b", r"\bequation\b", r"\bproof\b", r"\bprove\b",
        r"\bbackprop", r"\bcalculat",
        r"\bcost\s*function\b", r"\bloss\s*function\b", r"\bactivation\s*function\b",
        r"\bchain\s*rule\b", r"\bpartial\b", r"\bbayes\b",
        r"\bprobability\b", r"\bstatistic", r"\bmath\s+behind\b",
        r"\bstep[\-\s]by[\-\s]step\b", r"\bgradient\s+of\b"
    ],
    "tutor": [
        r"\bexplain\b", r"\bunderstand\b", r"\bhelp\s*me\b", r"\bconfused\b",
        r"\bdon'?t\s*(get|understand)\b", r"\bwhat\s+is\b", r"\bhow\s+does\b",
        r"\bwhy\b", r"\bteach\s*me\b", r"\blearn\b", r"\bconcept\b",
        r"\bmeaning\b", r"\bdefinition\b", r"\bwhat\s+are\b",
        r"\bin\s+simple\s+terms\b", r"\bsimplify\b",
        r"\bstruggling\b", r"\bhaving\s+trouble\b", r"\bneed\s+help\b"
    ],
    # Coder patterns - explicit code keywords only
    "coder": [
        r"\bpython\b", r"\bscript\b", r"\bprogram\b",
        r"\bimplement\b", r"\bwrite\s*code\b", r"\bdebug\b", r"\bsyntax\b",
        r"\berror\b", r"\balgorithm\b", r"\bcode\b(?!.*course\s*code)",
        r"\bclass\b(?!.*classification)", r"\bdef\b", r"\bimport\b"
    ],
    "syllabus_query": [
        r"\bwhen\b", r"\bdue\s*date\b", r"\bdeadline\b", r"\bschedule\b",
        r"\bsyllabus\b", r"\boverview\b", r"\bchapter\b", r"\bmodule\b",
        r"\bweek\b", r"\bassignment\b", r"\bgrade\b", r"\bmark\b",
        r"\bexam\b", r"\bquiz\b", r"\btest\b"
    ],
    # Strong tutor signals that override math patterns
    "tutor_override": [
        r"\bdon'?t\s*(get|understand)\b", r"\bconfused\b", r"\bstruggling\b",
        r"\bhaving\s+trouble\b", r"\bneed\s+help\b", r"\bhelp\s*me\s+understand\b"
    ]
}


class Supervisor:
    """
    Router that selects appropriate model and strategy:
    - Tutor Mode: Gemini Flash with Socratic prompting
    - Math Mode: Gemini Flash with step-by-step derivation
    - Coder Mode: Groq (Llama 3.3 70B) for fast code generation
    - Syllabus Mode: Gemini Flash for logistics
    - Fast Mode: Gemini Flash (default)
    """

    def __init__(self):
        # Get Langfuse callback handler
        langfuse_handler = get_langfuse_handler()
        callbacks = [langfuse_handler] if langfuse_handler else []
        
        # Initialize Gemini (Primary/Fallback)
        self.gemini_flash = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.7,
            callbacks=callbacks,
        )
        
        # Higher temperature for Socratic tutoring (stochastic exploration)
        self.gemini_tutor = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.9,  # Higher for creative, exploratory responses
            callbacks=callbacks,
        )
        
        # Initialize Groq (Performance/Coder)
        if settings.groq_api_key:
            self.groq_coder = ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=settings.groq_api_key,
                temperature=0.5, # Lower temperature for code
                callbacks=callbacks,
            )
            self.groq_fast = ChatGroq(
                model_name="llama-3.3-70b-versatile", # Upgrading fast to 70b as it is very fast on Groq
                groq_api_key=settings.groq_api_key,
                temperature=0.7,
                callbacks=callbacks,
            )
        else:
            logger.warning("GROQ_API_KEY not found. Falling back to Gemini for all tasks.")
            self.groq_coder = None
            self.groq_fast = None

    def route_intent(self, query: str) -> Dict[str, str]:
        """
        Determine intent and select appropriate model
        
        Priority order (specialized first):
        1. Coder (code-specific)
        2. Syllabus (logistics-specific)
        3. Math (if derivation/calculation/formula focus)
        4. Tutor (conceptual understanding)
        5. Fast (default)
        
        Args:
            query: User query
            
        Returns:
            Dictionary with intent, model_selected, and routing metadata
        """
        query_lower = query.lower()
        
        # Score each intent
        intent_scores = {}
        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            matched_patterns = []
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
                    matched_patterns.append(pattern)
            if score > 0:
                intent_scores[intent] = {
                    "score": score,
                    "patterns": matched_patterns
                }
        
        # Priority 1: Coder (very specific signals)
        if "coder" in intent_scores and intent_scores["coder"]["score"] >= 1:
            return {
                "intent": "coder",
                "model_selected": "groq-llama-70b" if self.groq_coder else "gemini-flash",
                "confidence": min(1.0, intent_scores["coder"]["score"] / 2),
                "reason": f"Code patterns detected: {intent_scores['coder']['patterns'][:3]}"
            }
        
        # Priority 2: Syllabus (very specific signals)
        if "syllabus_query" in intent_scores and intent_scores["syllabus_query"]["score"] >= 1:
            return {
                "intent": "syllabus_query",
                "model_selected": "gemini-flash",
                "confidence": min(1.0, intent_scores["syllabus_query"]["score"] / 2),
                "reason": f"Syllabus patterns detected: {intent_scores['syllabus_query']['patterns'][:3]}"
            }
        
        # Priority 3: Math vs Tutor - disambiguate based on specificity
        has_math = "math" in intent_scores
        has_tutor = "tutor" in intent_scores
        
        # Check for tutor override patterns (confusion signals)
        has_tutor_override = any(
            re.search(pattern, query_lower) 
            for pattern in INTENT_PATTERNS.get("tutor_override", [])
        )
        
        if has_math and has_tutor:
            # Both matched - check for override first
            if has_tutor_override:
                # Student is confused/struggling - prioritize tutor regardless
                return {
                    "intent": "tutor",
                    "model_selected": "gemini-tutor",
                    "confidence": 0.9,
                    "reason": f"Tutor override (confusion signal detected): {intent_scores['tutor']['patterns'][:3]}"
                }
            
            # Use score comparison and content hints
            math_score = intent_scores["math"]["score"]
            tutor_score = intent_scores["tutor"]["score"]
            
            # Math wins if: higher score OR specific math action terms
            math_action_terms = ["derive", "calculat", "formula", "equation", "proof", "prove", "step-by-step"]
            is_math_action = any(term in query_lower for term in math_action_terms)
            
            if is_math_action or math_score > tutor_score:
                return {
                    "intent": "math",
                    "model_selected": "gemini-flash",
                    "confidence": min(1.0, math_score / 2),
                    "reason": f"Math patterns won over tutor: {intent_scores['math']['patterns'][:3]}"
                }
            else:
                return {
                    "intent": "tutor",
                    "model_selected": "gemini-tutor",
                    "confidence": min(1.0, tutor_score / 2),
                    "reason": f"Tutor patterns won: {intent_scores['tutor']['patterns'][:3]}"
                }
        
        # Priority 3a: Math only (but check override first)
        if has_math:
            if has_tutor_override:
                return {
                    "intent": "tutor",
                    "model_selected": "gemini-tutor",
                    "confidence": 0.9,
                    "reason": "Tutor override (confusion signal) even with math topic"
                }
            return {
                "intent": "math",
                "model_selected": "gemini-flash",
                "confidence": min(1.0, intent_scores["math"]["score"] / 2),
                "reason": f"Math patterns detected: {intent_scores['math']['patterns'][:3]}"
            }
        
        # Priority 3b: Tutor only
        if has_tutor:
            return {
                "intent": "tutor",
                "model_selected": "gemini-tutor",
                "confidence": min(1.0, intent_scores["tutor"]["score"] / 2),
                "reason": f"Tutor patterns detected: {intent_scores['tutor']['patterns'][:3]}"
            }
        
        # Default to fast mode
        return {
            "intent": "fast",
            "model_selected": "gemini-flash",
            "confidence": 0.5,
            "reason": "No specific patterns detected, using fast mode"
        }

    def get_model(self, model_name: str):
        """Get model instance by name"""
        if model_name == "gemini-flash":
            return self.gemini_flash
        elif model_name == "gemini-tutor":
            return self.gemini_tutor
        elif model_name == "groq-llama-70b":
            return self.groq_coder or self.gemini_flash
        elif model_name == "groq-llama-8b":
            return self.groq_fast or self.gemini_flash
        else:
            return self.gemini_flash  # Default fallback


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node for LangGraph with comprehensive routing observability
    
    Routes to specialized agents:
    - tutor: Pedagogical Socratic tutor
    - math: Mathematical reasoning agent
    - coder: Code generation/debugging
    - syllabus_query: Course logistics
    - fast: Quick general responses
    """
    logger.info("🎯 Supervisor: Analyzing query for optimal routing")
    start_time = time.time()
    
    # Create agent observation for routing decisions
    observation = None
    trace_id = state.get("trace_id")
    if trace_id:
        from app.observability.langfuse_client import get_langfuse_client
        client = get_langfuse_client()
        if client:
            try:
                observation = client.start_span(
                    trace_context={"trace_id": trace_id},
                    name="intelligent_routing_agent",
                    input={
                        "query": state.get("query"),
                        "query_length": len(state.get("query", "")),
                        "user_context": state.get("user_role")
                    },
                    metadata={
                        "component": "supervisor",
                        "routing_strategy": "intent_classification",
                        "available_intents": ["tutor", "math", "coder", "syllabus_query", "fast"]
                    }
                )
            except Exception as e:
                logger.warning(f"Could not create supervisor observation: {e}")
    
    supervisor = Supervisor()
    routing = supervisor.route_intent(state.get("query", ""))
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000  # milliseconds
    
    # Update processing times tracking
    processing_times = state.get("processing_times", {}) or {}
    processing_times["supervisor"] = processing_time
    
    # Store routing decision in model parameters for cost tracking
    model_parameters = state.get("model_parameters", {}) or {}
    model_parameters["routing_decision"] = {
        "intent": routing["intent"],
        "model_selected": routing["model_selected"],
        "confidence": routing.get("confidence", 0.8),
        "selection_reason": routing.get("reason", "Default routing logic")
    }
    
    # Determine if we should use specialized agent nodes
    # Tutor and Math intents route to specialized nodes
    use_specialized_agent = routing["intent"] in ["tutor", "math"]
    
    # Log routing decision with emoji
    intent_emoji = {
        "tutor": "📚",
        "math": "🔢", 
        "coder": "💻",
        "syllabus_query": "📅",
        "fast": "⚡"
    }
    emoji = intent_emoji.get(routing["intent"], "🎯")
    
    logger.info(f"{emoji} Supervisor: → {routing['intent']} via {routing['model_selected']} "
                f"(confidence: {routing.get('confidence', 0):.2f}, {processing_time:.1f}ms)")
    
    # Update observation with routing analytics
    if observation:
        update_observation_with_usage(
            observation,
            output_data={
                "routing_decision": routing,
                "use_specialized_agent": use_specialized_agent,
                "processing_metrics": {
                    "analysis_time_ms": processing_time,
                    "intent_classification": routing["intent"],
                    "model_selection": routing["model_selected"]
                },
                "routing_analytics": {
                    "query_complexity": "high" if routing["intent"] in ["math", "tutor"] else "standard",
                    "expected_performance": "optimized" if "groq" in routing["model_selected"] else "standard",
                    "pedagogical_mode": routing["intent"] in ["tutor", "math"]
                }
            },
            level="DEFAULT",
            latency_seconds=processing_time / 1000.0
        )
        observation.end()
    
    # Return updated state
    return {
        "intent": routing["intent"],
        "model_selected": routing["model_selected"],
        "processing_times": processing_times,
        "model_parameters": model_parameters
    }
