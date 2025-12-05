"""
Reasoning Node for Agentic AI Tutor
Implements multi-step thinking before action selection

Based on research:
- "Agents perceive, reason, plan, act, and then observe the result" (agent-info.md)
- "The Router/Planner decides intent" (agentic_tutor_info.md)
- Sequential thinking with Chain-of-Thought reasoning

This node sits between Governor and Supervisor, adding a "thinking" phase
that analyzes the query, student context, and determines optimal strategy.
"""

from typing import Dict, List, Optional, Any
import logging
import time
import json
from dataclasses import dataclass, field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState, ScaffoldingLevel, BloomLevel, PedagogicalApproach
from app.config import settings
from app.observability.langfuse_client import create_child_span_from_state, update_observation_with_usage

logger = logging.getLogger(__name__)


@dataclass
class ReasoningOutput:
    """Structured output from the reasoning phase"""
    
    # Perception Phase
    query_type: str  # question, request, clarification, follow_up
    topic_domain: str  # ml_concepts, math, code, logistics, general
    key_concepts: List[str] = field(default_factory=list)
    is_follow_up: bool = False  # NEW: Is this a follow-up question?
    contextualized_query: Optional[str] = None  # NEW: Full query with context
    
    # Analysis Phase
    confusion_signals: List[str] = field(default_factory=list)
    prior_knowledge_level: str = "unknown"  # novice, intermediate, advanced
    bloom_level: BloomLevel = "understand"
    requires_retrieval: bool = True
    
    # Planning Phase
    teaching_strategy: PedagogicalApproach = "scaffolded"
    scaffolding_level: ScaffoldingLevel = "explained"
    response_length: str = "medium"  # short, medium, detailed
    
    # Decision Phase
    recommended_intent: str = "tutor"
    confidence: float = 0.8
    reasoning: str = ""
    
    # Additional context
    follow_up_needed: bool = False
    diagnostic_question: Optional[str] = None


# System prompt for the reasoning LLM
REASONING_SYSTEM_PROMPT = """You are a pedagogical reasoning engine for an AI tutoring system (COMP 237: Introduction to AI).
Your job is to ANALYZE the student's query and determine the optimal teaching strategy.

You will output a structured JSON analysis. Do NOT provide the actual answer to the student's question.

## CRITICAL: Follow-up Question Handling

When the student query contains anaphoric references (that, it, this, them, etc.) or is very short:
- Look at the conversation history to understand what they're referring to
- Infer the full meaning from context
- Identify the actual topic they're asking about
- Set `requires_context` to true and include `contextualized_query` in your analysis

Examples of follow-up patterns that need contextualization:
- "what does that mean" → needs context from previous message
- "can you explain more" → needs to know what topic was discussed
- "how does it work" → "it" refers to something mentioned before
- "why?" → asking about something just explained
- "example?" → wants an example of the concept just discussed
- "got it, but what about X" → continuation of previous topic

## Your Analysis Framework:

### 1. PERCEPTION: What is the student asking?
- Query Type: question | request | clarification | follow_up
- Topic Domain: ml_concepts | math | code | logistics | general
- Key Concepts: List the AI/ML concepts mentioned or implied
- Is Follow-up: true/false (is this a follow-up to previous message?)
- Contextualized Query: If follow-up, rewrite the query with full context

### 2. ANALYSIS: What is the student's current state?
- Confusion Signals: List any signs of confusion ("don't understand", "confused", "stuck", etc.)
- Prior Knowledge Level: novice | intermediate | advanced (infer from language)
- Bloom's Taxonomy Level: remember | understand | apply | analyze | evaluate | create
- Requires Retrieval: true if we need course materials, false for simple answers

### 3. PLANNING: How should we teach this?
- Teaching Strategy: socratic (questions) | direct (explain) | scaffolded (guided) | exploratory (discovery)
- Scaffolding Level: hint (minimal help) | guided (some support) | explained (full explanation) | demonstrated (worked example)
- Response Length: short (1-3 sentences) | medium (3-5 paragraphs) | detailed (comprehensive)

### 4. DECISION: Where should this query go?
- Recommended Intent: tutor | math | coder | syllabus_query | explain | fast
- Confidence: 0.0 to 1.0
- Reasoning: Brief explanation of your decision

## Intent Definitions (CRITICAL - read carefully):
- **fast**: Quick factual answers, 1-3 sentences. Use when: "briefly", "quick", "one sentence", simple definitions
- **explain**: Medium-length explanations (3-5 paragraphs). Use when: "explain X", "what is X" WITHOUT confusion signals
- **tutor**: Full Socratic scaffolding. Use ONLY when: confusion signals present ("don't understand", "confused", "struggling", "need help understanding")
- **math**: Mathematical derivations, formulas, step-by-step calculations. Use when: "derive", "proof", "formula", "step-by-step"
- **coder**: Python code, implementation, debugging. Use when: "python", "code", "implement", "debug"
- **syllabus_query**: Course logistics, dates, policies. Use when: "what is this course", "topics covered", "due dates"

## KEY ROUTING RULES:
1. "explain backpropagation" → **explain** (no confusion, just wants explanation)
2. "I don't understand backpropagation" → **tutor** (confusion signal present)
3. "what is gradient descent" → **explain** (definitional question, no confusion)
4. "I'm confused about gradient descent" → **tutor** (confusion signal present)
5. "briefly, what is a neural network" → **fast** (wants quick answer)
6. "derive the loss function" → **math** (mathematical derivation)
7. "what topics does this course cover" → **syllabus_query** (course logistics)
8. "what does that mean" (after explaining loss functions) → **explain** (follow-up about loss functions)

## Response Format (JSON only):
```json
{
  "perception": {
    "query_type": "question",
    "topic_domain": "ml_concepts",
    "key_concepts": ["backpropagation", "gradient descent"],
    "is_follow_up": false,
    "contextualized_query": null
  },
  "analysis": {
    "confusion_signals": ["don't understand"],
    "prior_knowledge_level": "novice",
    "bloom_level": "understand",
    "requires_retrieval": true
  },
  "planning": {
    "teaching_strategy": "scaffolded",
    "scaffolding_level": "explained",
    "response_length": "medium"
  },
  "decision": {
    "recommended_intent": "tutor",
    "confidence": 0.85,
    "reasoning": "Student shows confusion signals about a core ML concept"
  }
}
```

## Follow-up Example (JSON):
```json
{
  "perception": {
    "query_type": "follow_up",
    "topic_domain": "ml_concepts",
    "key_concepts": ["loss function"],
    "is_follow_up": true,
    "contextualized_query": "What does the loss function mean in neural networks?"
  },
  "analysis": {
    "confusion_signals": [],
    "prior_knowledge_level": "novice",
    "bloom_level": "understand",
    "requires_retrieval": true
  },
  "planning": {
    "teaching_strategy": "direct",
    "scaffolding_level": "explained",
    "response_length": "medium"
  },
  "decision": {
    "recommended_intent": "explain",
    "confidence": 0.9,
    "reasoning": "Follow-up question asking for clarification on loss function"
  }
}
```
"""


class ReasoningEngine:
    """
    Multi-step reasoning engine that analyzes queries before routing.
    
    This replaces the brittle regex-first approach with LLM-based understanding.
    The reasoning happens BEFORE supervisor routing, informing better decisions.
    """
    
    def __init__(self):
        """Initialize with a fast, low-temperature model for consistent reasoning"""
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.1,  # Low temperature for consistent analysis
            max_output_tokens=1024,
        ).with_config(
            # Tag for event filtering - prevents output from streaming to user
            tags=["reasoning_internal", "no_stream"],
            metadata={"component": "reasoning_engine", "internal": True}
        )
    
    def _detect_follow_up_heuristic(self, query: str, conversation_history: List[dict]) -> tuple[bool, Optional[str], bool]:
        """
        Heuristic-based follow-up detection before LLM reasoning.
        
        Returns:
            Tuple of (is_follow_up, contextualized_query, is_frustrated_followup)
            - is_frustrated_followup: True for "no", "still don't get it" etc. → triggers SHORT responses
        """
        if not conversation_history or len(conversation_history) < 2:
            return False, None, False
        
        query_lower = query.lower().strip()
        
        # FRUSTRATED FOLLOW-UP PATTERNS (require SHORT responses)
        # These are single-word rejections or continued confusion after previous explanation
        frustrated_patterns = [
            r"^no\.?!?$",  # Just "no"
            r"^nope\.?!?$",  # Just "nope"
            r"^(i\s+)?still\s+(don'?t|can'?t)\s+(get|understand)",
            r"^(that|it|this)\s+(doesn'?t|don'?t)\s+make\s+sense",
            r"^not\s+really\.?$",
            r"^(i'?m\s+)?(still\s+)?confused\.?!?$",
            r"^huh\??$",
            r"^what\??$",  # Just "what?" as confusion
        ]
        
        import re
        is_frustrated = any(re.search(p, query_lower, re.IGNORECASE) for p in frustrated_patterns)
        
        # Strong follow-up signals
        follow_up_patterns = [
            r"^(what|how|why|when|where)\s+(does|do|is|are|was|were)\s+(that|it|this|they|those)\s+",
            r"^(what|how|why)\s+(does|do|is|are)\s+(that|it|this|they)\s+",
            r"^(i\s+)?don'?t\s+(get|understand|know)\s+(it|that|this)?",
            r"^(can\s+you\s+)?(explain|clarify)\s+(more|further|that|it|this)",
            r"^(what|how)\s+(about|do\s+you\s+mean)\s+",
            r"^(okay|ok|alright|got\s+it),\s+(what|how|why)",
            r"^(i\s+)?(still\s+)?(don'?t|can'?t)\s+(get|understand|see|grasp)",
            r"^(that|it|this)\s+(doesn'?t|don'?t)\s+make\s+sense",
            r"^(i'?m\s+)?(still\s+)?(confused|lost|stuck)",
            r"^(can\s+you\s+)?(give|show|provide)\s+(me\s+)?(an\s+)?example",
            r"^(what|how)\s+(does|do)\s+(that|it|this)\s+work",
        ]
        
        for pattern in follow_up_patterns:
            if re.search(pattern, query_lower):
                # Try to contextualize from last assistant message
                last_assistant_msg = None
                for msg in reversed(conversation_history):
                    if msg.get("role") == "assistant":
                        last_assistant_msg = msg.get("content", "")
                        break
                
                if last_assistant_msg:
                    # Extract topic from last response (simple heuristic)
                    # Look for concepts mentioned
                    contextualized = query
                    # If query is very short, try to infer from context
                    if len(query.split()) < 5:
                        # Try to extract topic from last assistant message
                        # This is a simple heuristic - LLM will do better
                        contextualized = f"{query} (referring to previous explanation about the topic)"
                    return True, contextualized, is_frustrated
                return True, query, is_frustrated
        
        # Very short queries MAY be follow-ups, but only if they contain anaphoric references
        # or are incomplete phrases. Short standalone questions like "What is SVM?" should NOT
        # be classified as follow-ups just because conversation history exists.
        if len(query.split()) < 4 and len(conversation_history) >= 2:
            # Check for anaphoric references (pronouns referring to previous context)
            anaphoric_words = {"it", "that", "this", "they", "them", "those", "these", "here", "there"}
            # Strip punctuation from words for matching
            query_words = [w.strip("?.,!:;'\"") for w in query_lower.split()]
            has_anaphoric = any(word in anaphoric_words for word in query_words)
            
            # Check for incomplete phrases that need context
            incomplete_patterns = [
                r"^(yes|no|yeah|yep|nope|sure|okay|ok|right|exactly|correct)\b",
                r"^(and|but|so|also|too)\s+",
                r"^(why|how|what|huh)\s*\??!?$",  # Just "why?", "how?", "what?", "huh?"
                r"^(really|seriously|actually)\s*\??$",
                r"^\?\s*$",  # Just a question mark
                r"\bmore\b",  # Contains "more" (e.g., "tell me more", "explain more")
                r"^go\s+on\b",  # "go on"
                r"^continue\b",  # "continue"
            ]
            is_incomplete = any(re.search(p, query_lower) for p in incomplete_patterns)
            
            # Only classify as follow-up if it has anaphoric references or is incomplete
            if has_anaphoric or is_incomplete:
                return True, query, is_frustrated
        
        return False, None, False
    
    def _build_context_summary(self, conversation_history: List[dict]) -> str:
        """Summarize conversation history for context, with emphasis on recent content for follow-ups"""
        if not conversation_history:
            return "No prior conversation."
        
        # Take last 4 exchanges (8 messages) for better context
        recent = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
        
        summary_parts = []
        for i, msg in enumerate(recent):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # Show more content for recent messages (last 2 exchanges)
            if i >= len(recent) - 4:
                # Last 2 exchanges: show up to 400 chars for better context
                truncated = content[:400] + ("..." if len(content) > 400 else "")
            else:
                # Earlier messages: show up to 150 chars
                truncated = content[:150] + ("..." if len(content) > 150 else "")
            
            summary_parts.append(f"- {role.upper()}: {truncated}")
        
        return "\n".join(summary_parts) if summary_parts else "No prior conversation."
    
    def _build_student_context(self, state: AgentState) -> str:
        """Build student context summary from state"""
        parts = []
        
        # User info
        if state.get("user_email"):
            parts.append(f"Student email: {state['user_email']}")
        
        # Depth preference
        if state.get("user_depth_preference"):
            parts.append(f"Stated preference: {state['user_depth_preference']} explanations")
        
        # Prior diagnostic
        if state.get("diagnostic_asked"):
            parts.append("Already asked diagnostic question")
        
        return "\n".join(parts) if parts else "No student context available."
    
    def reason(
        self,
        query: str,
        conversation_history: List[dict] = None,
        student_context: Optional[Dict] = None
    ) -> ReasoningOutput:
        """
        Perform multi-step reasoning on the query.
        
        Args:
            query: The student's query
            conversation_history: Prior messages in conversation
            student_context: Additional context (mastery scores, etc.)
            
        Returns:
            ReasoningOutput with structured analysis
        """
        # Pre-detect follow-up using heuristics (faster than LLM)
        is_follow_up_heuristic, contextualized_heuristic, is_frustrated_heuristic = self._detect_follow_up_heuristic(
            query, conversation_history or []
        )
        
        # Build the analysis prompt
        history_summary = self._build_context_summary(conversation_history or [])
        
        # Add heuristic detection to prompt for LLM to validate/improve
        follow_up_hint = ""
        if is_follow_up_heuristic:
            follow_up_hint = f"""
## FOLLOW-UP DETECTION HINT:
This query appears to be a follow-up based on heuristics. The query "{query}" likely refers to something in the conversation history above.
Please:
1. Identify what topic/concept the student is asking about from the conversation history
2. Set is_follow_up to true
3. Provide a contextualized_query that makes the question explicit
Example: If query is "what does that mean" and last topic was "backpropagation", contextualized_query should be "What does backpropagation mean?"
"""
        
        user_prompt = f"""Analyze this student query and provide your reasoning in JSON format.

## Student Query:
{query}
{follow_up_hint}

## Conversation History:
{history_summary}

## Additional Context:
{json.dumps(student_context) if student_context else "None"}

Provide your analysis as a JSON object following the format specified in the system prompt."""

        try:
            response = self.model.invoke([
                SystemMessage(content=REASONING_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
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
            
            # Handle markdown code blocks
            if "```" in content:
                parts = content.split("```")
                if len(parts) >= 2:
                    json_part = parts[1]
                    if json_part.startswith("json"):
                        json_part = json_part[4:]
                    content = json_part.strip()
            
            result = json.loads(content)
            
            # Convert to ReasoningOutput
            perception = result.get("perception", {})
            analysis = result.get("analysis", {})
            planning = result.get("planning", {})
            decision = result.get("decision", {})
            
            # Use heuristic detection if LLM didn't detect follow-up but heuristic did
            is_follow_up = perception.get("is_follow_up", False) or is_follow_up_heuristic
            contextualized_query = perception.get("contextualized_query") or contextualized_heuristic
            
            # CRITICAL: Force SHORT response for frustrated follow-ups ("no", "still don't get it")
            # This prevents verbose re-explanations when student is frustrated
            response_length = planning.get("response_length", "medium")
            if is_frustrated_heuristic and is_follow_up:
                response_length = "short"
                logger.info(f"⚠️ Frustrated follow-up detected: forcing short response")
            
            return ReasoningOutput(
                # Perception
                query_type=perception.get("query_type", "question"),
                topic_domain=perception.get("topic_domain", "general"),
                key_concepts=perception.get("key_concepts", []),
                is_follow_up=is_follow_up,
                contextualized_query=contextualized_query,
                
                # Analysis
                confusion_signals=analysis.get("confusion_signals", []),
                prior_knowledge_level=analysis.get("prior_knowledge_level", "unknown"),
                bloom_level=analysis.get("bloom_level", "understand"),
                requires_retrieval=analysis.get("requires_retrieval", True),
                
                # Planning
                teaching_strategy=planning.get("teaching_strategy", "scaffolded"),
                scaffolding_level=planning.get("scaffolding_level", "explained"),
                response_length=response_length,  # May be overridden to "short" for frustrated follow-ups
                
                # Decision
                recommended_intent=decision.get("recommended_intent", "tutor"),
                confidence=decision.get("confidence", 0.7),
                reasoning=decision.get("reasoning", ""),
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse reasoning JSON: {e}")
            # Return default reasoning on parse failure
            return self._default_reasoning(query)
            
        except Exception as e:
            logger.error(f"Reasoning engine error: {e}")
            return self._default_reasoning(query)
    
    def _default_reasoning(self, query: str) -> ReasoningOutput:
        """Fallback reasoning when LLM fails"""
        # Use simple heuristics as fallback
        query_lower = query.lower()
        
        # Detect obvious patterns for fallback
        if any(kw in query_lower for kw in ["code", "python", "implement", "debug"]):
            intent = "coder"
        elif any(kw in query_lower for kw in ["when", "due", "exam", "schedule", "syllabus"]):
            intent = "syllabus_query"
        elif any(kw in query_lower for kw in ["derive", "formula", "calculate", "proof"]):
            intent = "math"
        elif any(kw in query_lower for kw in ["confused", "don't understand", "help"]):
            intent = "tutor"
        else:
            intent = "fast"
        
        return ReasoningOutput(
            query_type="question",
            topic_domain="general",
            key_concepts=[],
            recommended_intent=intent,
            confidence=0.5,
            reasoning="Fallback heuristic due to reasoning engine failure"
        )


def reasoning_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node that performs multi-step reasoning before routing.
    
    This node analyzes the query and produces structured reasoning that
    informs the supervisor's routing decision and the agent's response strategy.
    
    Chain-of-Thought (CoT) reasoning steps are added to state for visibility.
    Based on "Chain-of-Thought Prompting Elicits Reasoning" (Wei et al., 2022)
    """
    logger.info("🧠 Reasoning Node: Analyzing query with multi-step thinking")
    start_time = time.time()
    
    # Initialize chain of thought steps for frontend visibility
    # These will be sent to the frontend as actual reasoning, not just status labels
    thought_chain = []
    
    # Create observation as child of root trace
    observation = create_child_span_from_state(
        state=state,
        name="multi_step_reasoning",
        input_data={
            "query": state.get("query"),
            "history_length": len(state.get("conversation_history", []) or [])
        },
        metadata={
            "component": "reasoning_node",
            "framework": "chain_of_thought"
        }
    )
    
    # Build student context from state
    student_context = {}
    if state.get("user_id"):
        student_context["user_id"] = state.get("user_id")
    if state.get("user_depth_preference"):
        student_context["depth_preference"] = state.get("user_depth_preference")
    if state.get("diagnostic_asked"):
        student_context["diagnostic_asked"] = True
    
    # NEW: Fetch student mastery and recent interactions for personalization
    student_history_context = ""
    mastery_scores = {}
    recent_interactions = []
    has_prior_sessions = False
    
    if state.get("user_id"):
        try:
            from app.agents.knowledge_graph import (
                get_recent_student_interactions,
                get_student_mastery_scores,
                format_student_history,
                get_student_context_summary
            )
            
            user_id = state.get("user_id")
            
            # Use synchronous functions (no async needed)
            try:
                context_summary = get_student_context_summary(user_id)
                
                if context_summary:
                    mastery_scores = context_summary.get("mastery_scores", {})
                    recent_interactions = context_summary.get("interactions", [])
                    student_history_context = context_summary.get("formatted_history", "")
                    has_prior_sessions = context_summary.get("has_prior_sessions", False)
                    
                    if student_history_context:
                        student_context["learning_history"] = student_history_context
                        student_context["mastery_scores"] = mastery_scores
                        student_context["has_prior_sessions"] = has_prior_sessions
                        student_context["struggling_topics"] = context_summary.get("struggling_topics", [])
                        student_context["strong_topics"] = context_summary.get("strong_topics", [])
                        logger.info(f"📚 Loaded student history: {len(mastery_scores)} mastery scores, {len(recent_interactions)} recent interactions")
                    else:
                        logger.debug("No student history formatted (empty result)")
                else:
                    logger.debug(f"No context summary found for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch student context: {e}")
        except ImportError as e:
            logger.warning(f"Could not import student history functions: {e}")
    
    # Check if context engineering is needed (compaction for long conversations)
    from app.agents.context_engineer import engineer_context
    context_updates = engineer_context(state)
    if context_updates:
        # Update state with compacted context
        state.update(context_updates)
        logger.info("📦 Context engineered: conversation compacted")
    
    # Run reasoning engine
    engine = ReasoningEngine()
    reasoning = engine.reason(
        query=state.get("query", ""),
        conversation_history=state.get("conversation_history"),
        student_context=student_context if student_context else None
    )
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000
    
    # === BUILD VISIBLE CHAIN-OF-THOUGHT ===
    # These are the actual reasoning steps shown to users, per CoT paper best practices
    query = state.get("query", "")
    
    # Step 1: Perception - What is being asked?
    thought_chain.append({
        "step": 1,
        "phase": "perception",
        "thought": f"Query type: {reasoning.query_type} | Domain: {reasoning.topic_domain}",
        "detail": f"Key concepts: {', '.join(reasoning.key_concepts) if reasoning.key_concepts else 'general question'}"
    })
    
    # Step 2: Context - Is this a follow-up?
    if reasoning.is_follow_up:
        thought_chain.append({
            "step": 2,
            "phase": "context",
            "thought": "This is a follow-up question referring to previous conversation",
            "detail": f"Interpreted as: \"{reasoning.contextualized_query}\""
        })
    else:
        thought_chain.append({
            "step": 2,
            "phase": "context",
            "thought": "New topic - no prior context needed",
            "detail": None
        })
    
    # Step 3: Analysis - What is the student's state?
    confusion_note = f"Confusion signals: {', '.join(reasoning.confusion_signals)}" if reasoning.confusion_signals else "No confusion detected"
    thought_chain.append({
        "step": 3,
        "phase": "analysis",
        "thought": f"Student level: {reasoning.prior_knowledge_level} | Bloom's: {reasoning.bloom_level}",
        "detail": confusion_note
    })
    
    # Step 4: Strategy - How should we teach this?
    thought_chain.append({
        "step": 4,
        "phase": "planning",
        "thought": f"Strategy: {reasoning.teaching_strategy} | Scaffolding: {reasoning.scaffolding_level}",
        "detail": f"Response length: {reasoning.response_length}" + (" | Need course materials" if reasoning.requires_retrieval else "")
    })
    
    # Step 5: Decision - Where to route?
    thought_chain.append({
        "step": 5,
        "phase": "decision",
        "thought": f"Routing to: {reasoning.recommended_intent} (confidence: {reasoning.confidence:.0%})",
        "detail": reasoning.reasoning if reasoning.reasoning else None
    })
    
    # Update processing times
    processing_times = state.get("processing_times", {}) or {}
    processing_times["reasoning"] = processing_time
    
    # Handle follow-up queries: use contextualized query for downstream processing
    effective_query = state.get("query", "")
    if reasoning.is_follow_up and reasoning.contextualized_query:
        effective_query = reasoning.contextualized_query
        logger.info(f"🔄 Follow-up detected: '{state.get('query')}' → '{effective_query}'")
    
    # Update state with follow-up information
    state_updates = {
        "reasoning_complete": True,
        "reasoning_intent": reasoning.recommended_intent,
        "reasoning_confidence": reasoning.confidence,
        "reasoning_strategy": reasoning.teaching_strategy,
        "reasoning_context_needed": ["retrieved_context"] if reasoning.requires_retrieval else [],
        "is_follow_up": reasoning.is_follow_up,
        "contextualized_query": reasoning.contextualized_query,
        "effective_query": effective_query,
        "intent": reasoning.recommended_intent,  # Set intent from reasoning
        "processing_times": processing_times,
        # NEW: Chain-of-thought for frontend visibility
        "thought_chain": thought_chain,
        # NEW: Student history for personalization
        "student_history_context": student_history_context if student_history_context else None,
        "student_mastery_scores": mastery_scores if mastery_scores else {},
        "student_has_prior_sessions": has_prior_sessions,
    }
    
    # Update observation
    if observation:
        update_observation_with_usage(
            observation,
            output_data={
                "reasoning_output": {
                    "recommended_intent": reasoning.recommended_intent,
                    "confidence": reasoning.confidence,
                    "teaching_strategy": reasoning.teaching_strategy,
                    "scaffolding_level": reasoning.scaffolding_level,
                    "key_concepts": reasoning.key_concepts,
                    "confusion_signals": reasoning.confusion_signals,
                    "is_follow_up": reasoning.is_follow_up,
                    "contextualized_query": reasoning.contextualized_query,
                },
                "processing_time_ms": processing_time
            },
            level="DEFAULT",
            latency_seconds=processing_time / 1000.0
        )
        observation.end()
    
    logger.info(f"🧠 Reasoning: → {reasoning.recommended_intent} "
                f"(conf={reasoning.confidence:.2f}, strategy={reasoning.teaching_strategy}, follow_up={reasoning.is_follow_up}) "
                f"[{processing_time:.1f}ms]")
    
    # Merge state updates with additional fields
    state_updates.update({
        # Pedagogical planning
        "scaffolding_level": reasoning.scaffolding_level,
        "bloom_level": reasoning.bloom_level,
        "pedagogical_approach": reasoning.teaching_strategy,
        
        # Analysis results
        "key_concepts_detected": reasoning.key_concepts,
        "student_confusion_detected": len(reasoning.confusion_signals) > 0,
        "requires_retrieval": reasoning.requires_retrieval,
        "response_length_hint": reasoning.response_length,
    })
    
    # Return state updates
    return state_updates


# Convenience function for testing
def analyze_query(query: str) -> dict:
    """
    Standalone function to analyze a query without full state.
    Useful for testing and debugging.
    """
    engine = ReasoningEngine()
    result = engine.reason(query)
    return {
        "intent": result.recommended_intent,
        "confidence": result.confidence,
        "strategy": result.teaching_strategy,
        "scaffolding": result.scaffolding_level,
        "concepts": result.key_concepts,
        "confusion": result.confusion_signals,
        "reasoning": result.reasoning,
    }
