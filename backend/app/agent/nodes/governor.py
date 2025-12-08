"""
Governor Node - Policy Engine (3 Laws Enforcement)

Runs BEFORE any agent action to enforce:
- Law 1 (Scope): Only COMP 237 topics allowed
- Law 2 (Integrity): No complete assignment solutions
- Law 3 (Mastery): Track understanding verification

Based on research from:
- LearnLM principles (adaptivity, active learning)
- Adarsh's off-topic detection patterns
- Google prompting strategies (clear constraints)
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple

from app.agent.state import AgentState
from app.agent.tools.rag import get_rag_retriever
from app.observability import get_langfuse_client

logger = logging.getLogger(__name__)


# =============================================================================
# Law 2: Academic Integrity Patterns
# =============================================================================

INTEGRITY_VIOLATION_PATTERNS = [
    # Direct requests for complete solutions
    r"\bdo\s+my\s+(?:assignment|homework|project|lab|quiz|exam|test)\b",
    r"\bcomplete\s+(?:solution|answer|code|assignment)\s+(?:for|to)\b",
    r"\bsolve\s+(?:this|my)\s+(?:entire|whole|full|complete)\b",
    r"\bwrite\s+(?:my|the)\s+(?:entire|whole|full|complete)\s+(?:essay|report|code|assignment|lab)\b",
    r"\bgive\s+me\s+(?:the|all)\s+(?:answers?|solutions?)\b",
    r"\bjust\s+give\s+me\s+the\s+(?:answer|solution|code)\b",
    
    # Lab/code specific
    r"\b(?:write|do|complete)\s+(?:my\s+)?(?:entire\s+)?lab\s*\d*\s*(?:code|assignment)?\b",
    r"\b(?:finish|complete)\s+(?:my\s+)?(?:code|lab|project)\s+for\s+me\b",
    
    # Cheating indicators
    r"\bdon'?t\s+explain\s*,?\s*just\s+(?:solve|answer|give)\b",
    r"\bi\s+need\s+(?:the|this)\s+(?:answer|solution)\s+(?:now|fast|quick|asap)\b",
    r"\bsubmit\s+(?:this|it)\s+(?:for|as)\s+me\b",
    r"\bcopy\s*(?:and|&)?\s*paste\s+(?:solution|answer)\b",
    
    # Exam/test cheating
    r"\bexam\s+(?:answers?|solutions?|help)\b",
    r"\btest\s+(?:answers?|solutions?)\b",
    r"\bquiz\s+(?:answers?|solutions?)\b",
    r"\bfinal\s+(?:answers?|solutions?|exam)\b",
]

# Compile for efficiency
INTEGRITY_RE = re.compile("|".join(INTEGRITY_VIOLATION_PATTERNS), re.IGNORECASE)


# =============================================================================
# Law 1: Off-Topic Detection (Outside COMP 237 Scope)
# =============================================================================

OFF_TOPIC_PATTERNS = [
    # Food and recipes
    r'\bpizza\b', r'\bcoffee\b', r'\btea\b', r'\brecipe\b', r'\bcook(?:ing)?\b',
    r'\bfood\b', r'\brestaurant\b', r'\bmeal\b', r'\bbreakfast\b', r'\blunch\b', r'\bdinner\b',
    
    # Weather
    r'\bweather\b', r'\btemperature\b', r'\brain(?:ing)?\b', r'\bsnow(?:ing)?\b', r'\bsunny\b',
    r'\bforecast\b', r'\bhumid\b', r'\bstorm\b', r'\bwindy\b', r'\bclimate\b',
    
    # Sports
    r'\bsports?\b', r'\bfootball\b', r'\bbasketball\b', r'\bsoccer\b',
    r'\btennis\b', r'\bgolf\b', r'\bbaseball\b', r'\bhockey\b', r'\bnba\b', r'\bnfl\b',
    
    # Entertainment
    r'\bmovies?\b', r'\bnetflix\b', r'\bdisney\b', r'\bprime video\b', r'\bhulu\b',
    r'\bcelebrit(?:y|ies)\b', r'\bactor\b', r'\bactress\b', r'\bhollywood\b',
    r'\btaylor swift\b', r'\bbeyonce\b', r'\bbts\b', r'\bkpop\b',
    r'\bsinger\b', r'\bentertainment\b', r'\bmusic\b', r'\bsong\b', r'\balbum\b', r'\bconcert\b',
    
    # Social media
    r'\binstagram\b', r'\btwitter\b', r'\btiktok\b', r'\bfacebook\b', r'\bsnapchat\b',
    r'\byoutube\b', r'\breddit\b', r'\btwitch\b',
    
    # Shopping
    r'\bshop(?:ping)?\b', r'\bbuy\b', r'\bpurchase\b', r'\bamazon\b', r'\bebay\b',
    r'\bwhere\s+(?:can\s+)?i\s+buy\b', r'\bbest\s+(?:deal|price)\b',
    
    # Games
    r'\bvideo\s*games?\b', r'\bgaming\b', r'\bplaystation\b', r'\bxbox\b', r'\bnintendo\b',
    r'\bfortnite\b', r'\bminecraft\b', r'\bcall\s+of\s+duty\b',
    
    # Personal/Small talk
    r'\bhow\s+old\s+are\s+you\b', r'\bwho\s+(?:made|created)\s+you\b',
    r'\bwhat\'?s\s+your\s+(?:name|favorite)\b', r'\bare\s+you\s+(?:real|human|ai)\b',
    
    # Jokes and fun
    r'\btell\s+(?:me\s+)?a\s+joke\b', r'\bfunny\b', r'\blol\b', r'\blmao\b',
    
    # Dating/Relationships
    r'\bdating\b', r'\brelationship\b', r'\bboyfriend\b', r'\bgirlfriend\b',
    
    # Travel
    r'\btravel\b', r'\bvacation\b', r'\bhotel\b', r'\bflight\b', r'\bairline\b',
    
    # Health (non-AI related)
    r'\bdoctor\b', r'\bmedicine\b', r'\bsick\b', r'\bhospital\b', r'\bheadache\b',
    
    # Politics
    r'\bpolitics\b', r'\belection\b', r'\bpresident\b', r'\bvote\b', r'\bconservative\b', r'\bliberal\b',
]

# Compile for efficiency
OFF_TOPIC_RE = re.compile("|".join(OFF_TOPIC_PATTERNS), re.IGNORECASE)


# =============================================================================
# COMP 237 In-Scope Keywords (positive signal)
# =============================================================================

COMP237_KEYWORDS = [
    # Core AI/ML concepts
    r'\bartificial\s*intelligence\b', r'\bmachine\s*learning\b', r'\bdeep\s*learning\b',
    r'\bneural\s*network\b', r'\bperceptron\b', r'\bbackpropagation\b',
    r'\bgradient\s*descent\b', r'\blearning\s*rate\b', r'\bactivation\s*function\b',
    
    # Search algorithms
    r'\bsearch\s*algorithm\b', r'\ba\*\b', r'\bbfs\b', r'\bdfs\b',
    r'\bbreadth.first\b', r'\bdepth.first\b', r'\bheuristic\b',
    
    # ML algorithms
    r'\bclassification\b', r'\bregression\b', r'\bclustering\b',
    r'\bdecision\s*tree\b', r'\brandom\s*forest\b', r'\bsvm\b', r'\bknn\b',
    r'\bk.?means\b', r'\bnaive\s*bayes\b', r'\blogistic\b',
    
    # Probability/Stats
    r'\bprobability\b', r'\bbayes\b', r'\bconditional\b', r'\bprior\b', r'\bposterior\b',
    r'\bvariance\b', r'\bstandard\s*deviation\b', r'\bnormal\s*distribution\b',
    
    # NLP
    r'\bnatural\s*language\b', r'\bnlp\b', r'\btext\s*processing\b',
    r'\btokeniz\w+\b', r'\bstemm\w+\b', r'\blemmatiz\w+\b',
    r'\bsentiment\b', r'\bword\s*embed\w+\b', r'\btf.?idf\b',
    
    # Computer Vision
    r'\bcomputer\s*vision\b', r'\bimage\s*(?:recognition|classification|processing)\b',
    r'\bcnn\b', r'\bconvolution\w*\b',
    
    # Evaluation
    r'\baccuracy\b', r'\bprecision\b', r'\brecall\b', r'\bf1.?score\b',
    r'\bconfusion\s*matrix\b', r'\bcross.?validation\b',
    r'\boverfit\w*\b', r'\bunderfit\w*\b', r'\bbias\b',
    
    # Data preprocessing
    r'\bnormaliz\w+\b', r'\bfeature\s*(?:engineering|extraction|selection)\b',
    r'\btrain.?test\s*split\b', r'\bdata\s*(?:clean|preprocess)\w*\b',
    
    # Course specific
    r'\bcomp\s*237\b', r'\bcentennial\b', r'\bcourse\b', r'\bsyllabus\b',
    r'\bassignment\b', r'\blab\b', r'\bexam\b', r'\bweek\s*\d+\b',
    
    # Python/Code (for course)
    r'\bpython\b', r'\bscikit.?learn\b', r'\bsklearn\b', r'\bnumpy\b',
    r'\bpandas\b', r'\btensorflow\b', r'\bpytorch\b', r'\bkeras\b',
]

COMP237_RE = re.compile("|".join(COMP237_KEYWORDS), re.IGNORECASE)


# =============================================================================
# Governor Node Implementation
# =============================================================================

def _check_integrity(query: str) -> Tuple[bool, Optional[str]]:
    """
    Law 2: Check for academic integrity violations.
    
    Returns:
        (is_violation, violation_type)
    """
    if INTEGRITY_RE.search(query):
        return True, "integrity"
    return False, None


def _check_off_topic(query: str) -> Tuple[bool, Optional[str]]:
    """
    Check if query matches off-topic patterns.
    
    Returns:
        (is_off_topic, reason)
    """
    # First check if it has COMP237 keywords (positive signal)
    has_course_keywords = bool(COMP237_RE.search(query))
    
    # Check for off-topic patterns
    has_off_topic = bool(OFF_TOPIC_RE.search(query))
    
    # If has course keywords, give benefit of doubt
    if has_course_keywords:
        return False, None
    
    # Pure off-topic
    if has_off_topic:
        return True, "off_topic"
    
    return False, None


def _check_scope_with_rag(query: str, threshold: float = 0.25) -> Tuple[bool, float, Optional[str]]:
    """
    Law 1: Check if query is within COMP 237 scope using RAG.
    
    Uses ChromaDB distance to determine relevance.
    Lower distance = more relevant.
    
    Returns:
        (is_in_scope, best_score, reason)
    """
    try:
        retriever = get_rag_retriever()
        docs, metadata = retriever.retrieve(query, k=1, threshold=0.1)  # Low threshold to get any match
        
        if not docs:
            # No documents found at all
            return False, 0.0, "no_course_content"
        
        # Get the best match score
        best_score = docs[0].get("score", 0.0) if docs else 0.0
        
        # If best score is below threshold, query is likely out of scope
        if best_score < threshold:
            logger.info(f"[Governor] Low RAG score: {best_score:.3f} < {threshold}")
            return False, best_score, "low_relevance"
        
        return True, best_score, None
        
    except Exception as e:
        logger.warning(f"[Governor] RAG check failed: {e}")
        # On error, don't block - let it through with a warning
        return True, 0.5, None


def _log_to_langfuse(
    trace_id: Optional[str],
    law_checks: Dict[str, Any],
    approved: bool,
    rejection_reason: Optional[str]
):
    """Log Governor decision to Langfuse for observability."""
    try:
        client = get_langfuse_client()
        if not client or not trace_id:
            return
        
        # Use start_span with trace context
        span = client.start_span(
            name="governor_check",
            input={"law_checks": law_checks},
            metadata={
                "approved": approved,
                "rejection_reason": rejection_reason,
                "law1_scope": law_checks.get("scope", {}),
                "law2_integrity": law_checks.get("integrity", {}),
            }
        )
        
        # Link to trace
        span.update_trace(
            metadata={
                "governor_approved": approved,
                "governor_reason": rejection_reason,
            }
        )
        
        # Update span with output
        span.update(
            output={
                "approved": approved,
                "rejection_reason": rejection_reason,
            }
        )
        
        # End the span
        span.end()
        
        # Score the policy compliance
        client.create_score(
            trace_id=trace_id,
            name="policy_compliance",
            value=1.0 if approved else 0.0,
            comment=f"Governor: {'approved' if approved else rejection_reason}"
        )
        
    except Exception as e:
        logger.warning(f"[Governor] Langfuse logging failed: {e}")


def governor_node(state: AgentState) -> Dict[str, Any]:
    """
    Governor Node: Enforces 3 Laws before any agent action.
    
    Law 1 (Scope): Only COMP 237 topics - checked via RAG distance
    Law 2 (Integrity): No complete assignment solutions - regex patterns
    Law 3 (Mastery): Verify understanding - deferred to Evaluator
    
    If any law is violated, sets approved=False and provides rejection reason.
    """
    query = state.get("query", "")
    trace_id = state.get("trace_id")
    
    logger.info(f"[Governor] Checking query: {query[:50]}...")
    
    law_checks = {}
    
    # =================================================================
    # Law 2: Integrity Check (FIRST - fast regex, critical)
    # =================================================================
    is_integrity_violation, integrity_reason = _check_integrity(query)
    law_checks["integrity"] = {
        "violated": is_integrity_violation,
        "reason": integrity_reason,
    }
    
    if is_integrity_violation:
        logger.warning(f"[Governor] ⚠️ Law 2 VIOLATED: Integrity breach detected")
        _log_to_langfuse(trace_id, law_checks, False, "integrity")
        return {
            **state,
            "approved": False,
            "rejection_reason": "integrity",
            "governor_checks": law_checks,
        }
    
    # =================================================================
    # Law 1: Scope Check (Off-topic patterns first, then RAG)
    # =================================================================
    
    # Quick off-topic pattern check
    is_off_topic, off_topic_reason = _check_off_topic(query)
    
    if is_off_topic:
        logger.info(f"[Governor] Off-topic pattern detected")
        law_checks["scope"] = {
            "in_scope": False,
            "method": "pattern",
            "reason": off_topic_reason,
        }
        _log_to_langfuse(trace_id, law_checks, False, "off_topic")
        return {
            **state,
            "approved": False,
            "rejection_reason": "off_topic",
            "governor_checks": law_checks,
        }
    
    # RAG-based scope check for ambiguous queries
    is_in_scope, rag_score, scope_reason = _check_scope_with_rag(query)
    law_checks["scope"] = {
        "in_scope": is_in_scope,
        "method": "rag",
        "rag_score": rag_score,
        "reason": scope_reason,
    }
    
    if not is_in_scope:
        logger.info(f"[Governor] ⚠️ Law 1: Out of scope (RAG score: {rag_score:.3f})")
        _log_to_langfuse(trace_id, law_checks, False, scope_reason)
        return {
            **state,
            "approved": False,
            "rejection_reason": scope_reason or "off_topic",
            "governor_checks": law_checks,
        }
    
    # =================================================================
    # Law 3: Mastery Check (deferred to Evaluator node)
    # =================================================================
    law_checks["mastery"] = {
        "checked": False,
        "note": "Deferred to Evaluator node",
    }
    
    # All checks passed
    logger.info(f"[Governor] ✅ All laws satisfied (RAG score: {rag_score:.3f})")
    _log_to_langfuse(trace_id, law_checks, True, None)
    
    return {
        **state,
        "approved": True,
        "rejection_reason": None,
        "governor_checks": law_checks,
    }
