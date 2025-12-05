"""
Supervisor (Router) for Course Marshal
Routes queries to appropriate models and sub-agents

ARCHITECTURE UPDATE (2025):
This module has been refactored from regex-first to LLM-first classification.

Previous (BAD): Regex patterns → LLM fallback when confidence < 0.6
Current (GOOD): LLM reasoning → Regex only for obvious fast-path cases

Based on research:
- "The Router/Planner: An LLM node that decides intent" (agentic_tutor_info.md)
- "Agents perceive, reason, plan, act" (agent-info.md)

Routing Strategy:
- tutor: Socratic scaffolding for conceptual understanding (confused students)
- math: Step-by-step mathematical derivations
- coder: Code generation and debugging
- syllabus_query: Course logistics and schedule
- explain: Medium-length explanations (not full scaffolding)
- fast: Quick answers for simple queries
"""

from typing import Dict, Optional, List, Any
import logging
import time
import re
import json
import traceback
import os
from app.agents.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.observability import get_langfuse_handler
from app.observability.langfuse_client import (
    create_observation,
    update_observation_with_usage
)

logger = logging.getLogger(__name__)


# ============================================================================
# FAST-PATH PATTERNS (Only for obvious, high-confidence cases)
# ============================================================================
# These are used ONLY as a fast-path optimization when patterns have > 95% confidence.
# The LLM reasoning node handles all nuanced classification.

FAST_PATH_PATTERNS = {
    # Very obvious code requests (Python keywords, syntax)
    "coder": [
        r"^\s*(?:def|class|import|from|print)\s",  # Python syntax at start
        r"\bsyntax\s*error\b",
        r"\bTraceback\b",
        r"\bpip\s+install\b",
    ],
    # Very obvious logistics (dates, deadlines)
    "syllabus_query": [
        r"\b(?:when|what)\s+(?:is|are)\s+(?:the\s+)?(?:due|deadline|exam|quiz|test)\b",
        r"\bwhat\s+(?:is|does)\s+this\s+course\s+(?:about|cover)\b",
        r"\bsyllabus\b",
    ],
    # Explicit quick answer requests
    "fast": [
        r"\b(?:briefly|quick|short)\s+(?:answer|tell|explain)\b",
        r"\bin\s+one\s+(?:sentence|word)\b",
        r"^(?:just\s+)?tell\s+me\b",
    ],
}

# These patterns indicate the user NEEDS pedagogical support (override fast-path)
CONFUSION_OVERRIDE_PATTERNS = [
    r"\bdon'?t\s*(?:get|understand)\b",
    r"\bconfused\b",
    r"\bstruggling\b",
    r"\bhaving\s+trouble\b",
    r"\bneed\s+help\b",
    r"\bhelp\s*me\s+understand\b",
]

# Legacy: Kept for fallback if reasoning node fails
LEGACY_INTENT_PATTERNS = {
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
        r"\bdon'?t\s*(get|understand)\b", r"\bconfused\b", r"\bstruggling\b",
        r"\bhaving\s+trouble\b", r"\bneed\s+help\b", r"\bhelp\s*me\s+understand\b",
        r"\bteach\s*me\b", r"\bwalk\s*me\s*through\b", r"\bstep\s*by\s*step\s*explanation\b",
        r"\bin\s+simple\s+terms\b", r"\bsimplify\b",
        r"\bhow\s+does\s+.*\s+work\b", r"\bwhy\s+does\s+.*\s+(happen|work|fail)\b"
    ],
    "explain": [
        r"\bexplain\b(?!.*step\s*by\s*step)", 
        r"\bwhat\s+is\s+(a|an|the)\s+\w+",
        r"\bwhat\s+is\s+(?!this\s+course|this\b).+",
        r"\bwhat\s+are\s+(the\s+)?\w+s?\b", r"\bdefinition\b", r"\bmeaning\b",
        r"\bhow\s+do\b", r"\bhow\s+does\b", r"\bwhat\s+does\b"
    ],
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
        r"\bexam\b", r"\bquiz\b", r"\btest\b",
        r"\bwhat\s+(is|does)\s+this\s+course\b",
        r"\bcourse\s+(about|cover|include|content)\b",
        r"\babout\s+(the|this)\s+course\b",
        r"\bwhat\s+will\s+(we|i)\s+(learn|cover|study)\b",
        r"\bcourse\s+description\b", r"\bcourse\s+objectives?\b",
        r"\btopics?\s+(covered|included|taught)\b",
        r"\btopics?\s+(are|in)\s+(covered|this)\b",
        r"\bwhat.*topics\b",
        r"\bcomp\s*237\b",
        r"\bcourse\s+material\b", r"\bcourse\s+outline\b"
    ],
}


# Confidence threshold for triggering LLM fallback (legacy, kept for compatibility)
LLM_FALLBACK_THRESHOLD = 0.6

# LLM intent classification prompt (legacy fallback)
INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for an AI tutoring system for COMP 237 (Introduction to AI).

Classify the student's query into ONE of these intents:
- tutor: Student wants conceptual explanation, is confused, needs help understanding
- math: Student wants mathematical derivation, formula, calculation, proof
- coder: Student wants code, implementation, debugging help
- syllabus_query: Student asks about schedule, due dates, assignments, grades
- explain: Student wants a concept explained (not confused, just curious)
- fast: Simple factual question, quick answer needed

Respond with JSON only: {"intent": "<intent>", "confidence": <0.0-1.0>, "reason": "<brief explanation>"}

Student query: {query}"""


# ============================================================================
# AVAILABLE MODELS REGISTRY
# ============================================================================
# All available models with metadata for frontend model selector

AVAILABLE_MODELS = {
    # Google Models (Dec 2025: gemini-2.5-flash is stable, best price-performance)
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash",
        "provider": "google",
        "description": "Best price-performance, 1M context (recommended)",
        "speed": "fast",
        "quality": "very_high",
        "cost": "low",
        "requires_key": "google_api_key",
        "default": True,
    },
    "gemini-2.5-flash-lite": {
        "name": "Gemini 2.5 Flash-Lite",
        "provider": "google",
        "description": "Ultra-fast, cost-efficient for simple tasks",
        "speed": "very_fast",
        "quality": "high",
        "cost": "low",
        "requires_key": "google_api_key",
    },
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "provider": "google",
        "description": "Previous gen workhorse, stable",
        "speed": "fast",
        "quality": "high",
        "cost": "low",
        "requires_key": "google_api_key",
    },
    # GitHub Models (Azure OpenAI)
    "gpt-4.1-mini": {
        "name": "GPT-4.1 Mini",
        "provider": "github",
        "description": "Best for tutoring, excellent routing",
        "speed": "medium",
        "quality": "very_high",
        "cost": "low",
        "requires_key": "github_token",
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "provider": "github",
        "description": "Top-tier reasoning (higher latency)",
        "speed": "slow",
        "quality": "excellent",
        "cost": "medium",
        "requires_key": "github_token",
    },
    "o3-mini": {
        "name": "o3-mini",
        "provider": "github",
        "description": "Advanced reasoning (rate limited)",
        "speed": "slow",
        "quality": "excellent",
        "cost": "low",
        "requires_key": "github_token",
    },
    # Groq Models (Fast inference)
    "groq-llama-70b": {
        "name": "Llama 3.3 70B (Groq)",
        "provider": "groq",
        "description": "Ultra-fast, great for code",
        "speed": "very_fast",
        "quality": "high",
        "cost": "low",
        "requires_key": "groq_api_key",
    },
    # Local Models (Ollama)
    "ollama-mistral-7b": {
        "name": "Mistral 7B (Local)",
        "provider": "ollama",
        "description": "Free, runs locally (slower)",
        "speed": "slow",
        "quality": "medium",
        "cost": "free",
        "requires_key": None,
        "local": True,
    },
    "ollama-qwen2-7b": {
        "name": "Qwen2 7B (Local)",
        "provider": "ollama",
        "description": "Free, multilingual local model",
        "speed": "slow",
        "quality": "medium",
        "cost": "free",
        "requires_key": None,
        "local": True,
    },
}


def get_available_models() -> List[Dict[str, Any]]:
    """
    Return list of available models based on configured API keys.
    Used by the /api/models endpoint for frontend model selector.
    """
    available = []
    
    for model_id, info in AVAILABLE_MODELS.items():
        model_info = {
            "id": model_id,
            "name": info["name"],
            "provider": info["provider"],
            "description": info["description"],
            "speed": info.get("speed", "medium"),
            "quality": info.get("quality", "high"),
            "cost": info.get("cost", "low"),
            "available": False,
            "default": info.get("default", False),
            "local": info.get("local", False),
        }
        
        # Check if required API key is configured
        required_key = info.get("requires_key")
        if required_key is None:
            # Local models - check if Ollama is available
            if info.get("local"):
                ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
                model_info["available"] = bool(ollama_url)
            else:
                model_info["available"] = True
        elif required_key == "google_api_key":
            model_info["available"] = bool(settings.google_api_key)
        elif required_key == "github_token":
            model_info["available"] = bool(os.environ.get("GITHUB_TOKEN"))
        elif required_key == "groq_api_key":
            model_info["available"] = bool(settings.groq_api_key)
        
        available.append(model_info)
    
    return available


class Supervisor:
    """
    Router that selects appropriate model and strategy.
    
    ARCHITECTURE UPDATE (2025): Now uses LLM-first classification.
    
    Routing flow:
    1. Check if reasoning node already provided intent (preferred path)
    2. If not, check fast-path patterns for obvious cases (> 95% confidence)
    3. If still ambiguous, use LLM classification
    4. Map intent to appropriate model
    
    Supported Models (all streaming + Langfuse traced):
    - Google: gemini-2.0-flash, gemini-2.5-flash
    - GitHub: gpt-4.1-mini, gpt-4o, o3-mini
    - Groq: llama-3.3-70b-versatile
    - Ollama: mistral:7b-instruct, qwen2:7b-instruct
    """

    def __init__(self):
        # Get Langfuse callback handler
        langfuse_handler = get_langfuse_handler()
        callbacks = [langfuse_handler] if langfuse_handler else []
        
        # Store callbacks for model initialization
        self._callbacks = callbacks
        
        # Initialize Gemini (Primary/Fallback) - Using gemini-2.5-flash (stable, best price-performance)
        self.gemini_flash = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Stable: best price-performance model
            google_api_key=settings.google_api_key,
            temperature=0.7,
            callbacks=callbacks,
        )
        
        # Gemini 2.5 Flash (latest) - stable model
        self.gemini_25_flash = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Stable: best price-performance model
            google_api_key=settings.google_api_key,
            temperature=0.7,
            callbacks=callbacks,
        )
        
        # Higher temperature for Socratic tutoring (stochastic exploration)
        self.gemini_tutor = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Stable: best price-performance model
            google_api_key=settings.google_api_key,
            temperature=0.9,  # Higher for creative, exploratory responses
            callbacks=callbacks,
        )
        
        # Fast classifier (low temperature for deterministic classification)
        self.gemini_classifier = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Stable: best price-performance model
            google_api_key=settings.google_api_key,
            temperature=0.1,  # Low temperature for consistent classification
            callbacks=[],  # No callbacks for classifier to reduce overhead
        )
        
        # Initialize GitHub Models (Azure OpenAI)
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            self.gpt_41_mini = ChatOpenAI(
                model="gpt-4.1-mini",
                api_key=github_token,
                base_url="https://models.github.ai/inference/v1",
                temperature=0.7,
                callbacks=callbacks,
            )
            self.gpt_4o = ChatOpenAI(
                model="gpt-4o",
                api_key=github_token,
                base_url="https://models.github.ai/inference/v1",
                temperature=0.7,
                callbacks=callbacks,
            )
            self.o3_mini = ChatOpenAI(
                model="o3-mini",
                api_key=github_token,
                base_url="https://models.github.ai/inference/v1",
                temperature=1.0,  # o3 models work best with higher temperature
                callbacks=callbacks,
            )
        else:
            logger.info("GITHUB_TOKEN not found. GitHub models unavailable.")
            self.gpt_41_mini = None
            self.gpt_4o = None
            self.o3_mini = None
        
        # Initialize Groq (Performance/Coder)
        if settings.groq_api_key:
            self.groq_coder = ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=settings.groq_api_key,
                temperature=0.5, # Lower temperature for code
                callbacks=callbacks,
            )
            self.groq_fast = ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=settings.groq_api_key,
                temperature=0.7,
                callbacks=callbacks,
            )
        else:
            logger.warning("GROQ_API_KEY not found. Falling back to Gemini for all tasks.")
            self.groq_coder = None
            self.groq_fast = None
        
        # Initialize Ollama (Local models)
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            self.ollama_mistral = ChatOllama(
                model="mistral:7b-instruct",
                base_url=ollama_url,
                temperature=0.7,
                callbacks=callbacks,
            )
            self.ollama_qwen = ChatOllama(
                model="qwen2:7b-instruct",
                base_url=ollama_url,
                temperature=0.7,
                callbacks=callbacks,
            )
        except Exception as e:
            logger.info(f"Ollama not available: {e}")
            self.ollama_mistral = None
            self.ollama_qwen = None

    def route_from_reasoning(self, state: AgentState) -> Optional[Dict[str, Any]]:
        """
        Use reasoning node output if available (preferred path).
        
        The reasoning node performs multi-step analysis and provides:
        - reasoning_intent: Classified intent
        - reasoning_confidence: Classification confidence
        - reasoning_strategy: Teaching strategy recommendation
        
        This is the NEW primary routing path.
        
        UPDATED (Dec 2025): Raised threshold from 0.5 to 0.65 to reduce
        borderline misclassifications that lead to wrong intent/model.
        """
        reasoning_intent = state.get("reasoning_intent")
        reasoning_confidence = state.get("reasoning_confidence", 0)
        
        # Require higher confidence (0.65) to trust reasoning node
        # This prevents borderline cases from getting stuck in wrong intent
        if reasoning_intent and reasoning_confidence >= 0.65:
            # Use reasoning node's decision with intelligent model selection
            model = self._intent_to_model(reasoning_intent, state)
            
            return {
                "intent": reasoning_intent,
                "model_selected": model,
                "confidence": reasoning_confidence,
                "reason": f"From reasoning node: {state.get('reasoning_strategy', 'analyzed')}",
                "routing_method": "reasoning_node"
            }
        
        # If confidence is between 0.5 and 0.65, log for debugging
        if reasoning_intent and 0.5 <= reasoning_confidence < 0.65:
            logger.debug(f"Reasoning node borderline ({reasoning_confidence:.2f}), using fallback routing")
        
        return None

    def check_fast_path(self, query: str) -> Optional[Dict[str, str]]:
        """
        Check for obvious fast-path patterns (> 95% confidence).
        
        This is a performance optimization for queries that don't need
        LLM analysis. Only triggers for very obvious patterns.
        
        Returns None if no fast-path match found.
        """
        query_lower = query.lower()
        
        # First check for confusion override (always route to tutor)
        for pattern in CONFUSION_OVERRIDE_PATTERNS:
            if re.search(pattern, query_lower):
                return {
                    "intent": "tutor",
                    "model_selected": "gemini-tutor",
                    "confidence": 0.95,
                    "reason": "Confusion signal detected - requires pedagogical support",
                    "routing_method": "fast_path_confusion"
                }
        
        # Check fast-path patterns
        for intent, patterns in FAST_PATH_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    # Fast-path queries are typically simple, use base model
                    model = self._intent_to_model(intent, None)
                    return {
                        "intent": intent,
                        "model_selected": model,
                        "confidence": 0.95,
                        "reason": f"Fast-path pattern match: {pattern}",
                        "routing_method": "fast_path"
                    }
        
        return None

    def _intent_to_model(self, intent: str, state: Optional[AgentState] = None) -> str:
        """
        Map intent to appropriate model with intelligent selection.
        
        Selection strategy:
        - Fast queries → gemini-flash (speed)
        - Complex reasoning → gpt-4.1-mini or gemini-2.5-flash (quality)
        - Code tasks → groq-llama-70b (speed + code)
        - Math derivations → gpt-4.1-mini (reasoning)
        - Tutor (confused students) → gemini-tutor or gpt-4.1-mini (pedagogy)
        - Explain (complex) → gemini-2.5-flash or gpt-4.1-mini (quality)
        """
        # Check query complexity from state if available
        query_complexity = None
        if state:
            response_length_hint = state.get("response_length_hint")
            if response_length_hint == "detailed":
                query_complexity = "complex"
            elif response_length_hint == "medium":
                query_complexity = "moderate"
            else:
                query_complexity = "simple"
        
        # Base model mapping
        base_models = {
            "tutor": "gemini-tutor",
            "math": "gemini-flash",
            "coder": "groq-llama-70b" if self.groq_coder else "gemini-flash",
            "syllabus_query": "gemini-flash",
            "explain": "gemini-flash",
            "fast": "gemini-flash",
        }
        
        base_model = base_models.get(intent, "gemini-flash")
        
        # Upgrade model for complex queries
        if query_complexity == "complex":
            if intent == "explain" and self.gemini_25_flash:
                return "gemini-2.5-flash"
            elif intent == "tutor" and self.gpt_41_mini:
                return "gpt-4.1-mini"  # Better pedagogy for complex confusion
            elif intent == "math" and self.gpt_41_mini:
                return "gpt-4.1-mini"  # Better reasoning for complex math
            elif intent == "coder" and self.groq_coder:
                return "groq-llama-70b"  # Already optimal for code
        
        # For moderate complexity, prefer newer models if available
        elif query_complexity == "moderate":
            if intent == "explain" and self.gemini_25_flash:
                return "gemini-2.5-flash"
            elif intent == "tutor" and self.gemini_tutor:
                return "gemini-tutor"
        
        return base_model

    def route_intent(self, query: str) -> Dict[str, str]:
        """
        LEGACY: Regex-based intent classification (fallback only).
        
        This method is kept for backward compatibility but should NOT be the
        primary routing path. The reasoning node + fast_path should handle
        most cases.
        
        Use route_with_reasoning() instead for the new architecture.
        """
        query_lower = query.lower()
        
        # Score each intent using legacy patterns
        intent_scores = {}
        for intent, patterns in LEGACY_INTENT_PATTERNS.items():
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
        
        # Check for confusion override
        has_confusion = any(
            re.search(pattern, query_lower) 
            for pattern in CONFUSION_OVERRIDE_PATTERNS
        )
        
        if has_confusion:
            return {
                "intent": "tutor",
                "model_selected": "gemini-tutor",
                "confidence": 0.9,
                "reason": "Confusion signals detected - using full Socratic scaffolding",
                "routing_method": "legacy_regex"
            }
        
        # Priority-based selection from scored intents
        priority_order = ["coder", "syllabus_query", "math", "tutor", "explain", "fast"]
        
        for intent in priority_order:
            if intent in intent_scores and intent_scores[intent]["score"] >= 1:
                # Legacy routing typically handles simple cases
                model = self._intent_to_model(intent, None)
                return {
                    "intent": intent,
                    "model_selected": model,
                    "confidence": min(1.0, intent_scores[intent]["score"] / 2),
                    "reason": f"Legacy patterns: {intent_scores[intent]['patterns'][:3]}",
                    "routing_method": "legacy_regex"
                }
        
        # Default to fast
        return {
            "intent": "fast",
            "model_selected": "gemini-flash",
            "confidence": 0.4,
            "reason": "No patterns matched, using fast mode",
            "routing_method": "legacy_regex"
        }

    def route_with_reasoning(self, state: AgentState) -> Dict[str, Any]:
        """
        NEW PRIMARY ROUTING METHOD: Uses reasoning node output.
        
        Routing priority:
        1. Use reasoning node output if available (highest quality)
        2. Check fast-path for obvious patterns (performance optimization)
        3. Use LLM classification for ambiguous cases
        4. Fall back to legacy regex as last resort
        
        Args:
            state: Agent state with potential reasoning node output
            
        Returns:
            Routing decision with intent, model, confidence
        """
        query = state.get("query", "")
        
        # Priority 1: Use reasoning node output (best quality)
        reasoning_result = self.route_from_reasoning(state)
        if reasoning_result:
            logger.debug(f"Routing from reasoning node: {reasoning_result['intent']}")
            return reasoning_result
        
        # Priority 2: Check fast-path for obvious cases
        fast_result = self.check_fast_path(query)
        if fast_result:
            logger.debug(f"Routing from fast-path: {fast_result['intent']}")
            return fast_result
        
        # Priority 3: Use LLM classification for ambiguous cases
        llm_result = self.classify_with_llm(query)
        if llm_result and llm_result.get("confidence", 0) >= 0.6:
            logger.debug(f"Routing from LLM: {llm_result['intent']}")
            return llm_result
        
        # Priority 4: Fall back to legacy regex
        legacy_result = self.route_intent(query)
        legacy_result["routing_method"] = "legacy_fallback"
        logger.debug(f"Routing from legacy: {legacy_result['intent']}")
        return legacy_result

    def classify_with_llm(self, query: str) -> Optional[Dict[str, str]]:
        """
        Use LLM to classify intent when regex patterns have low confidence.
        This is the fallback for ambiguous queries.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with intent, model_selected, confidence, reason or None on error
        """
        try:
            prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)
            response = self.gemini_classifier.invoke([
                HumanMessage(content=prompt)
            ])
            
            # Handle Gemini 2.5+ list content format
            raw_content = response.content
            if isinstance(raw_content, list):
                text_parts = []
                for block in raw_content:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = ''.join(text_parts).strip()
            else:
                content = raw_content.strip() if isinstance(raw_content, str) else str(raw_content).strip()
            logger.debug(f"LLM classification raw response: {content}")
            # Handle markdown code blocks
            if "```" in content:
                # Extract content between first and last ```
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: try to find JSON-like structure with regex
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(0))
                    except:
                        logger.warning(f"Failed to parse JSON from LLM response: {content[:100]}...")
                        return None
                else:
                    logger.warning(f"No JSON found in LLM response: {content[:100]}...")
                    return None
            
            if not isinstance(result, dict):
                logger.warning(f"LLM returned non-dict JSON: {result}")
                return None

            intent = result.get("intent", "fast")
            confidence = float(result.get("confidence", 0.7))
            reason = result.get("reason", "LLM classification")
            
            # Use intelligent model selection
            # Create minimal state for model selection
            minimal_state = {"response_length_hint": "medium" if confidence > 0.7 else "short"}
            model = self._intent_to_model(intent, minimal_state)
            
            return {
                "intent": intent,
                "model_selected": model,
                "confidence": confidence,
                "reason": f"LLM classification: {reason}",
                "routing_method": "llm_fallback"
            }
            
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            logger.debug(traceback.format_exc())
            return None

    def route_with_hybrid(self, query: str) -> Dict[str, str]:
        """
        Hybrid routing: regex first, LLM fallback when confidence < threshold.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with intent, model_selected, confidence, reason
        """
        # First try regex-based routing
        regex_result = self.route_intent(query)
        regex_result["routing_method"] = "regex"
        
        # If confidence is high enough, use regex result
        if regex_result.get("confidence", 0) >= LLM_FALLBACK_THRESHOLD:
            logger.debug(f"Regex routing confident: {regex_result['confidence']:.2f}")
            return regex_result
        
        # Low confidence - try LLM classification
        logger.info(f"Low regex confidence ({regex_result['confidence']:.2f}), using LLM fallback")
        llm_result = self.classify_with_llm(query)
        
        if llm_result:
            # LLM succeeded - use its result but note we tried regex first
            llm_result["regex_fallback"] = regex_result
            return llm_result
        
        # LLM failed - fall back to regex result anyway
        logger.warning("LLM fallback failed, using regex result")
        return regex_result

    def get_model(self, model_name: str):
        """
        Get model instance by name.
        
        Supports all registered models with fallback to Gemini Flash.
        All models are configured with Langfuse callbacks for tracing.
        
        Args:
            model_name: Model identifier (e.g., "gemini-2.0-flash", "gpt-4.1-mini")
            
        Returns:
            LangChain chat model instance
        """
        # Core Gemini models
        if model_name == "gemini-flash" or model_name == "gemini-2.0-flash":
            return self.gemini_flash
        elif model_name == "gemini-2.5-flash":
            return self.gemini_25_flash
        elif model_name == "gemini-tutor":
            return self.gemini_tutor
            
        # GitHub Models (Azure OpenAI)
        elif model_name == "gpt-4.1-mini":
            if self.gpt_41_mini:
                return self.gpt_41_mini
            logger.warning(f"Model {model_name} not available, falling back to gemini-flash")
            return self.gemini_flash
        elif model_name == "gpt-4o":
            if self.gpt_4o:
                return self.gpt_4o
            logger.warning(f"Model {model_name} not available, falling back to gemini-flash")
            return self.gemini_flash
        elif model_name == "o3-mini":
            if self.o3_mini:
                return self.o3_mini
            logger.warning(f"Model {model_name} not available, falling back to gemini-flash")
            return self.gemini_flash
            
        # Groq models
        elif model_name == "groq-llama-70b":
            return self.groq_coder or self.gemini_flash
        elif model_name == "groq-llama-8b":
            return self.groq_fast or self.gemini_flash
            
        # Ollama local models
        elif model_name == "ollama-mistral-7b":
            if self.ollama_mistral:
                return self.ollama_mistral
            logger.warning(f"Model {model_name} not available, falling back to gemini-flash")
            return self.gemini_flash
        elif model_name == "ollama-qwen2-7b":
            if self.ollama_qwen:
                return self.ollama_qwen
            logger.warning(f"Model {model_name} not available, falling back to gemini-flash")
            return self.gemini_flash
            
        else:
            logger.debug(f"Unknown model {model_name}, using gemini-flash")
            return self.gemini_flash  # Default fallback


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node for LangGraph with LLM-first routing.
    
    ARCHITECTURE UPDATE (2025):
    Now uses reasoning node output when available, with fast-path
    and LLM classification as fallbacks.
    
    Supports user model override via state["model_override"].
    
    Routes to specialized agents:
    - tutor: Pedagogical Socratic tutor (confused students)
    - math: Mathematical reasoning agent
    - coder: Code generation/debugging
    - syllabus_query: Course logistics
    - explain: Medium-length explanations
    - fast: Quick general responses
    """
    logger.info("🎯 Supervisor: Routing query to appropriate agent")
    start_time = time.time()
    
    # Check for user model override
    model_override = state.get("model_override")
    
    # Create agent observation as child of root trace (v3 pattern)
    from app.observability.langfuse_client import create_child_span_from_state
    observation = create_child_span_from_state(
        state=state,
        name="intelligent_routing_agent",
        input_data={
            "query": state.get("query"),
            "query_length": len(state.get("query", "")),
            "has_reasoning": state.get("reasoning_complete", False),
            "model_override": model_override
        },
        metadata={
            "component": "supervisor",
            "routing_strategy": "llm_first" if not model_override else "user_override",
            "available_intents": ["tutor", "math", "coder", "syllabus_query", "explain", "fast"]
        }
    )
    
    supervisor = Supervisor()
    
    # If user specified a model, use it but still determine intent
    if model_override:
        # Still run routing to determine intent, but override model selection
        routing = supervisor.route_with_reasoning(state)
        routing["model_selected"] = model_override
        routing["routing_method"] = "user_override"
        routing["reason"] = f"User selected model: {model_override}"
        logger.info(f"🔧 Model override active: {model_override}")
    else:
        # Use new LLM-first routing method
        routing = supervisor.route_with_reasoning(state)
    
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
        "selection_reason": routing.get("reason", "Default routing logic"),
        "routing_method": routing.get("routing_method", "unknown")
    }
    
    # Determine if we should use specialized agent nodes
    use_specialized_agent = routing["intent"] in ["tutor", "math"]
    
    # Log routing decision with emoji
    intent_emoji = {
        "tutor": "📚",
        "math": "🔢", 
        "coder": "💻",
        "syllabus_query": "📅",
        "explain": "💡",
        "fast": "⚡"
    }
    emoji = intent_emoji.get(routing["intent"], "🎯")
    
    routing_method = routing.get("routing_method", "unknown")
    logger.info(f"{emoji} Supervisor: → {routing['intent']} via {routing['model_selected']} "
                f"(conf={routing.get('confidence', 0):.2f}, method={routing_method}) [{processing_time:.1f}ms]")
    
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
                    "model_selection": routing["model_selected"],
                    "routing_method": routing_method
                },
                "routing_analytics": {
                    "query_complexity": "high" if routing["intent"] in ["math", "tutor"] else "standard",
                    "expected_performance": "optimized" if "groq" in routing["model_selected"] else "standard",
                    "pedagogical_mode": routing["intent"] in ["tutor", "math", "explain"],
                    "used_reasoning_node": routing_method == "reasoning_node",
                    "used_fast_path": "fast_path" in routing_method,
                    "used_llm_classification": routing_method == "llm_fallback"
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
