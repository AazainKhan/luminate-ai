"""
Planner Node - LLM-first routing with heuristic safety

Based on Adarsh's PlannerAgent pattern:
- Always runs heuristics first for fast-path cases
- Uses Gemini for nuanced classification
- Falls back gracefully if LLM fails

Also handles policy enforcement (3 Laws from former Governor):
- Law 1 (Scope): Only COMP 237 topics
- Law 2 (Integrity): No complete assignment solutions
- Law 3 (Mastery): Verify understanding (deferred to Evaluator)

Includes proper Langfuse v3 tracing with nested spans.
"""

import logging
import json
import re
import time
from typing import Dict, Any, List, Optional, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.state import AgentState
from app.agent.schemas import TaskType, PlannerPlan, Subtask, ExplainPayload, SolvePayload, CodePayload, RejectPayload
from app.agent.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT
from app.agent.tools.rag import get_rag_retriever
from app.config import settings
from app.observability import get_langfuse_client

logger = logging.getLogger(__name__)


# =============================================================================
# Policy Enforcement Patterns (formerly Governor)
# =============================================================================

# Academic Integrity Violations
INTEGRITY_VIOLATION_PATTERNS = [
    r"\bdo\s+my\s+(?:assignment|homework|project|lab|quiz|exam|test)\b",
    r"\bcomplete\s+(?:solution|answer|code|assignment)\s+(?:for|to)\b",
    r"\bsolve\s+(?:this|my)\s+(?:entire|whole|full|complete)\b",
    r"\bwrite\s+(?:my|the)\s+(?:entire|whole|full|complete)\s+(?:essay|report|code|assignment|lab)\b",
    r"\bgive\s+me\s+(?:the|all)\s+(?:answers?|solutions?)\b",
    r"\bjust\s+give\s+me\s+the\s+(?:answer|solution|code)\b",
    r"\b(?:write|do|complete)\s+(?:my\s+)?(?:entire\s+)?lab\s*\d*\s*(?:code|assignment)?\b",
    r"\b(?:finish|complete)\s+(?:my\s+)?(?:code|lab|project)\s+for\s+me\b",
    r"\bdon'?t\s+explain\s*,?\s*just\s+(?:solve|answer|give)\b",
    r"\bsubmit\s+(?:this|it)\s+(?:for|as)\s+me\b",
    r"\bexam\s+(?:answers?|solutions?|help)\b",
    r"\bquiz\s+(?:answers?|solutions?)\b",
]
INTEGRITY_RE = re.compile("|".join(INTEGRITY_VIOLATION_PATTERNS), re.IGNORECASE)

# Off-Topic Detection
OFF_TOPIC_PATTERNS = [
    r'\bpizza\b', r'\bcoffee\b', r'\brecipe\b', r'\bcook(?:ing)?\b', r'\bfood\b', r'\brestaurant\b',
    r'\bweather\b', r'\btemperature\b', r'\brain(?:ing)?\b', r'\bforecast\b',
    r'\bsports?\b', r'\bfootball\b', r'\bbasketball\b', r'\bsoccer\b', r'\bnba\b', r'\bnfl\b',
    r'\bmovies?\b', r'\bnetflix\b', r'\bdisney\b', r'\bcelebrit(?:y|ies)\b', r'\bhollywood\b',
    r'\btaylor swift\b', r'\bbeyonce\b', r'\bbts\b', r'\bkpop\b', r'\bmusic\b', r'\bsong\b',
    r'\binstagram\b', r'\btwitter\b', r'\btiktok\b', r'\bfacebook\b', r'\byoutube\b',
    r'\bshop(?:ping)?\b', r'\bamazon\b', r'\bbuy\b',
    r'\bvideo\s*games?\b', r'\bgaming\b', r'\bplaystation\b', r'\bxbox\b', r'\bfortnite\b',
    r'\bhow\s+old\s+are\s+you\b', r'\bwho\s+(?:made|created)\s+you\b', r'\btell\s+(?:me\s+)?a\s+joke\b',
    r'\bdating\b', r'\brelationship\b', r'\bboyfriend\b', r'\bgirlfriend\b',
    r'\btravel\b', r'\bvacation\b', r'\bhotel\b', r'\bflight\b',
    r'\bdoctor\b', r'\bmedicine\b', r'\bhospital\b',
    r'\bpolitics\b', r'\belection\b', r'\bpresident\b',
]
OFF_TOPIC_RE = re.compile("|".join(OFF_TOPIC_PATTERNS), re.IGNORECASE)

# COMP237 In-Scope Keywords (positive signal)
COMP237_KEYWORDS = [
    r'\bartificial\s*intelligence\b', r'\bmachine\s*learning\b', r'\bdeep\s*learning\b',
    r'\bneural\s*network\b', r'\bperceptron\b', r'\bbackpropagation\b',
    r'\bgradient\s*descent\b', r'\blearning\s*rate\b', r'\bactivation\s*function\b',
    r'\bsearch\s*algorithm\b', r'\ba\*\b', r'\bbfs\b', r'\bdfs\b', r'\bheuristic\b',
    r'\bclassification\b', r'\bregression\b', r'\bclustering\b',
    r'\bdecision\s*tree\b', r'\brandom\s*forest\b', r'\bsvm\b', r'\bknn\b', r'\bk.?means\b',
    r'\bprobability\b', r'\bbayes\b', r'\bconditional\b',
    r'\bnatural\s*language\b', r'\bnlp\b', r'\bsentiment\b', r'\btf.?idf\b',
    r'\bcomputer\s*vision\b', r'\bimage\s*(?:recognition|classification)\b', r'\bcnn\b',
    r'\baccuracy\b', r'\bprecision\b', r'\brecall\b', r'\bf1.?score\b', r'\bconfusion\s*matrix\b',
    r'\boverfit\w*\b', r'\bunderfit\w*\b', r'\bbias\b',
    r'\bcomp\s*237\b', r'\bcentennial\b', r'\bsyllabus\b', r'\bweek\s*\d+\b',
    r'\bpython\b', r'\bscikit.?learn\b', r'\bnumpy\b', r'\bpandas\b', r'\btensorflow\b',
]
COMP237_RE = re.compile("|".join(COMP237_KEYWORDS), re.IGNORECASE)


# =============================================================================
# Fast-Path Heuristics (95%+ confidence patterns)
# =============================================================================

FAST_PATH_PATTERNS = {
    TaskType.CODE: [
        r"^\s*(?:def|class|import|from|print)\s",  # Python syntax
        r"\bsyntax\s*error\b",
        r"\bTraceback\b",
        r"\bpip\s+install\b",
        r"\bdebug\b.*\bcode\b",
    ],
    # NOTE: No QUICK patterns - all questions go through scaffolding
    TaskType.SOLVE: [
        r"\bderive\b",
        r"\bcalculate\b",
        r"\bsolve\b.*\b(?:equation|problem)\b",
        r"\bstep[\-\s]by[\-\s]step\b.*\b(?:math|formula)\b",
        r"\bprove\b",
    ],
}

# Confusion signals → always route to EXPLAIN with scaffolding
CONFUSION_PATTERNS = [
    r"\bdon'?t\s*(?:get|understand)\b",
    r"\bconfused\b",
    r"\bstruggling\b",
    r"\bhaving\s+trouble\b",
    r"\bneed\s+help\b",
    r"\bhelp\s*me\s+understand\b",
    r"\bi'?m\s+lost\b",
]

# Stuck patterns for escalation detection
STUCK_PATTERNS = [
    r"\bi\s+don'?t\s+(?:know|understand|get\s+it)\b",
    r"\bidk\b",
    r"\bstill\s+(?:don'?t|confused|unclear|not\s+sure)\b",
    r"\bdidn'?t\s+(?:make\s+)?sense\b",
    r"\bexplain\s+(?:again|it\s+again)\b",
    r"\bjust\s+(?:tell|explain|show)\s+me\b",
    r"\bi'?m\s+(?:really\s+)?confused\b",
    r"\bcan\s+you\s+just\s+explain\b",
    r"\bi\s+(?:really\s+)?(?:don'?t\s+)?(?:understand|get)\s+(?:this|it)\b",
    r"\bwhat\s+(?:do\s+you\s+mean|does\s+that\s+mean)\b",
    r"\bi'?m\s+(?:so\s+)?lost\b",
    r"\bthis\s+is\s+(?:too\s+)?confusing\b",
    r"\bhelp\s+me\s+understand\b",
]


def _check_policy(query: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check policy compliance (integrity and scope).
    
    Returns:
        (approved, rejection_reason, rejection_type)
    """
    # Law 2: Check integrity violations FIRST (fast regex)
    if INTEGRITY_RE.search(query):
        logger.info("[Planner] Policy: Integrity violation detected")
        return False, "integrity", "integrity"
    
    # Law 1: Check off-topic patterns
    has_course_keywords = bool(COMP237_RE.search(query))
    has_off_topic = bool(OFF_TOPIC_RE.search(query))
    
    # If has course keywords, give benefit of doubt
    if has_off_topic and not has_course_keywords:
        logger.info("[Planner] Policy: Off-topic pattern detected")
        return False, "off_topic", "off_topic"
    
    return True, None, None


def _check_scope_with_rag(query: str, threshold: float = 0.25) -> Tuple[bool, float, Optional[str]]:
    """
    Check if query is within COMP 237 scope using RAG.
    
    Also checks for topic mismatch - when RAG returns documents that don't
    actually relate to the query topic (e.g., returning "Statistics" for "Deep Q learning").
    
    Returns:
        (is_in_scope, best_score, reason)
    """
    # Topics NOT covered in COMP237 (advanced RL, specific architectures, etc.)
    OUT_OF_SCOPE_TOPICS = [
        r"\bdeep\s*q[- ]?learning\b",
        r"\breinforcement\s*learning\b",
        r"\bq[- ]?learning\b",
        r"\bdqn\b",
        r"\bppo\b",
        r"\bactor[- ]?critic\b",
        r"\bgpt[- ]?\d\b",
        r"\bbert\b",
        r"\btransformer\s*architecture\b",
        r"\battention\s*mechanism\b",
        r"\bllm\b",
        r"\blarge\s*language\s*model\b",
        r"\bgenerative\s*ai\b",
        r"\bdiffusion\s*model\b",
        r"\bgan\b",
        r"\bgenerative\s*adversarial\b",
    ]
    
    # Check for explicitly out-of-scope advanced topics
    query_lower = query.lower()
    for pattern in OUT_OF_SCOPE_TOPICS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.info(f"[Planner] Out-of-scope topic detected: {pattern}")
            return False, 0.0, "advanced_topic_not_covered"
    
    try:
        retriever = get_rag_retriever()
        docs, metadata = retriever.retrieve(query, k=1, threshold=0.1)
        
        if not docs:
            return False, 0.0, "no_course_content"
        
        best_score = docs[0].get("score", 0.0) if docs else 0.0
        
        if best_score < threshold:
            logger.info(f"[Planner] Low RAG score: {best_score:.3f} < {threshold}")
            return False, best_score, "low_relevance"
        
        return True, best_score, None
        
    except Exception as e:
        logger.warning(f"[Planner] RAG check failed: {e}")
        return True, 0.5, None


def _check_fast_path(query: str) -> Optional[TaskType]:
    """Check if query matches fast-path patterns"""
    query_lower = query.lower()
    
    # Check confusion first - always routes to EXPLAIN
    for pattern in CONFUSION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return TaskType.EXPLAIN
    
    # Check other fast-path patterns
    for task_type, patterns in FAST_PATH_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return task_type
    
    return None


def _detect_stuck(query: str, conversation_history: List[dict]) -> tuple[bool, int]:
    """Detect if student is stuck and count stuck instances"""
    query_lower = query.lower()
    
    # Check current query
    is_stuck = any(re.search(p, query_lower, re.IGNORECASE) for p in STUCK_PATTERNS)
    
    # Count stuck instances in history
    stuck_count = 0
    for msg in conversation_history or []:
        if msg.get("role") == "user":
            msg_lower = msg.get("content", "").lower()
            if any(re.search(p, msg_lower, re.IGNORECASE) for p in STUCK_PATTERNS):
                stuck_count += 1
    
    return is_stuck, stuck_count


def _calculate_escalation_level(is_stuck: bool, stuck_count: int) -> int:
    """
    Calculate escalation level based on stuck signals.
    
    Logic:
    - If student has been stuck multiple times in history, escalate even if current query isn't stuck
    - stuck_count >= 2 → Level 4 (full explanation)
    - stuck_count == 1 OR is_stuck → Level 3 (concrete examples)  
    - is_stuck with no history → Level 2 (directed hints)
    - No stuck signals → Level 1 (diagnostic)
    """
    # If history shows repeated confusion, escalate regardless of current query
    if stuck_count >= 2:
        return 4  # Full explanation needed
    
    if stuck_count == 1:
        return 3  # Concrete examples needed
    
    # Current query is stuck but no prior history
    if is_stuck:
        return 2  # Start with directed hints
    
    # No stuck signals at all
    return 1  # Default: diagnostic questions


def _create_payload(task_type: TaskType, query: str) -> Any:
    """Create appropriate payload for task type
    
    NOTE: No QUICK type - all questions get scaffolded EXPLAIN
    """
    if task_type == TaskType.EXPLAIN:
        return ExplainPayload(topic=query)
    elif task_type == TaskType.SOLVE:
        return SolvePayload(problem=query)
    elif task_type == TaskType.CODE:
        return CodePayload(request=query)
    else:
        return RejectPayload(reason="Off-topic query")


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response"""
    text = text.strip()
    
    # Try direct parse
    if text.startswith("{"):
        try:
            return json.loads(text)
        except:
            pass
    
    # Find JSON block
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    
    raise ValueError("No valid JSON found in response")


def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Planner node: policy-aware query classification and routing
    
    Pipeline:
    1. Policy checks (integrity, off-topic, scope)
    2. Fast-path heuristics for obvious cases
    3. LLM classification for nuanced queries
    4. Fallback to EXPLAIN if all else fails
    
    Uses Langfuse v3 context managers for proper trace hierarchy.
    """
    query = state.get("query", "")
    conversation_history = state.get("conversation_history", [])
    
    logger.info(f"[Planner] Processing query: {query[:50]}...")
    
    # Get Langfuse client for tracing
    langfuse = get_langfuse_client()
    start_time = time.time()
    
    def _execute_planner_logic() -> Dict[str, Any]:
        """Inner function containing all planner logic."""
        
        # =====================================================================
        # Step 1: Policy Checks (fast regex-based)
        # =====================================================================
        approved, rejection_reason, rejection_type = _check_policy(query)
        
        if not approved:
            logger.info(f"[Planner] Policy rejected: {rejection_reason}")
            plan = {
                "subtasks": [{"task": "reject", "payload": {"reason": rejection_reason}}],
                "confidence": 1.0,
                "reasoning": f"Policy violation: {rejection_reason}",
            }
            return {
                **state,
                "plan": plan,
                "approved": False,
                "rejection_reason": rejection_reason,
                "escalation_level": 1,
                "stuck_count": 0,
                "is_stuck": False,
                "routing_info": {"method": "policy", "task": "reject", "reason": rejection_reason},
            }
        
        # Step 1b: RAG-based scope check for ambiguous queries
        is_in_scope, rag_score, scope_reason = _check_scope_with_rag(query)
        
        if not is_in_scope:
            logger.info(f"[Planner] Out of scope: {scope_reason} (score: {rag_score:.3f})")
            plan = {
                "subtasks": [{"task": "reject", "payload": {"reason": scope_reason}}],
                "confidence": 0.9,
                "reasoning": f"Out of scope: {scope_reason}",
            }
            return {
                **state,
                "plan": plan,
                "approved": False,
                "rejection_reason": scope_reason,
                "escalation_level": 1,
                "stuck_count": 0,
                "is_stuck": False,
                "routing_info": {"method": "rag-scope", "task": "reject", "reason": scope_reason, "rag_score": rag_score},
            }
        
        # =====================================================================
        # Step 2: Escalation Detection
        # =====================================================================
        is_stuck, stuck_count = _detect_stuck(query, conversation_history)
        escalation_level = _calculate_escalation_level(is_stuck, stuck_count)
        
        logger.info(f"[Planner] Stuck: {is_stuck}, Count: {stuck_count}, Escalation: {escalation_level}")
        
        # Try fast-path first
        fast_task = _check_fast_path(query)
        if fast_task:
            logger.info(f"[Planner] Fast-path match: {fast_task}")
            payload = _create_payload(fast_task, query)
            if fast_task == TaskType.EXPLAIN:
                payload.escalation_level = escalation_level
            
            plan = {
                "subtasks": [{"task": fast_task.value, "payload": payload.model_dump()}],
                "confidence": 0.95,
                "reasoning": f"Fast-path match for {fast_task.value}",
            }
            
            return {
                **state,
                "plan": plan,
                "approved": True,
                "rejection_reason": None,
                "escalation_level": escalation_level,
                "stuck_count": stuck_count,
                "is_stuck": is_stuck,
                "routing_info": {"method": "fast-path", "task": fast_task.value},
            }
        
        # =====================================================================
        # Step 3: LLM Classification with Langfuse Tracing
        # =====================================================================
        try:
            langfuse = get_langfuse_client()
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.1,
                google_api_key=settings.google_api_key,
            )
            
            # Format history
            history_str = ""
            if conversation_history:
                for msg in conversation_history[-3:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    history_str += f"{role}: {content}\n"
            
            # Build messages
            user_prompt = PLANNER_USER_PROMPT.format(
                query=query,
                history=history_str or "No history",
            )
            
            messages = [
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]
            
            # Trace the LLM call with Langfuse generation
            trace_id = state.get("trace_id")
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="planner_classification",
                model="gemini-2.5-flash",
                input={
                    "system": PLANNER_SYSTEM_PROMPT,
                    "user": user_prompt,
                },
                metadata={
                    "escalation_level": escalation_level,
                    "is_stuck": is_stuck,
                    "stuck_count": stuck_count,
                    "fast_path_bypassed": True,
                },
            ) as generation:
                response = llm.invoke(messages)
                
                # Update generation with output
                generation.update(
                    output=response.content,
                    usage_details={
                        "input": len(PLANNER_SYSTEM_PROMPT) + len(user_prompt),
                        "output": len(response.content),
                    },
                )
            
            raw_plan = _extract_json(response.content)
            
            # Validate and normalize
            subtasks = raw_plan.get("subtasks", [])
            if not subtasks:
                raise ValueError("No subtasks in plan")
            
            task_str = subtasks[0].get("task", "explain")
            try:
                task_type = TaskType(task_str)
            except ValueError:
                task_type = TaskType.EXPLAIN
            
            payload = _create_payload(task_type, query)
            if task_type == TaskType.EXPLAIN:
                payload.escalation_level = escalation_level
            
            plan = {
                "subtasks": [{"task": task_type.value, "payload": payload.model_dump()}],
                "confidence": raw_plan.get("confidence", 0.7),
                "reasoning": raw_plan.get("reasoning", "LLM classification"),
            }
            
            logger.info(f"[Planner] LLM classified as: {task_type.value}")
            
            return {
                **state,
                "plan": plan,
                "approved": True,
                "rejection_reason": None,
                "escalation_level": escalation_level,
                "stuck_count": stuck_count,
                "is_stuck": is_stuck,
                "routing_info": {"method": "llm", "task": task_type.value},
            }
            
        except Exception as e:
            logger.warning(f"[Planner] LLM failed: {e}, falling back to EXPLAIN")
            
            payload = ExplainPayload(topic=query, escalation_level=escalation_level)
            plan = {
                "subtasks": [{"task": TaskType.EXPLAIN.value, "payload": payload.model_dump()}],
                "confidence": 0.5,
                "reasoning": f"Fallback due to error: {e}",
            }
            
            return {
                **state,
                "plan": plan,
                "approved": True,
                "rejection_reason": None,
                "escalation_level": escalation_level,
                "stuck_count": stuck_count,
                "is_stuck": is_stuck,
                "routing_info": {"method": "fallback", "task": "explain", "error": str(e)},
            }
    
    # =========================================================================
    # Execute with Langfuse tracing
    # =========================================================================
    if langfuse:
        try:
            # Use context propagation from root span, not trace_context
            with langfuse.start_as_current_observation(
                as_type="chain",
                name="planner_node",
                input={"query": query[:200], "history_length": len(conversation_history)},
                metadata={"node": "planner", "version": "v3"}
            ) as planner_span:
                result = _execute_planner_logic()
                
                # Update span with output
                planner_span.update(
                    output={
                        "approved": result.get("approved", True),
                        "task": result.get("routing_info", {}).get("task", "unknown"),
                        "method": result.get("routing_info", {}).get("method", "unknown"),
                        "escalation_level": result.get("escalation_level", 1),
                        "is_stuck": result.get("is_stuck", False),
                    },
                    metadata={
                        "duration_ms": int((time.time() - start_time) * 1000),
                    }
                )
                
                return result
        except Exception as e:
            logger.error(f"[Planner] Error with tracing: {e}")
            # Fall through to non-traced execution
    
    # Execute without tracing if Langfuse not available
    return _execute_planner_logic()
