"""
Agent State Definition for LangGraph
Defines the shared state passed between all agent nodes
"""

from typing import TypedDict, List, Optional, Literal
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


# Scaffolding levels based on Zone of Proximal Development (ZPD) theory
ScaffoldingLevel = Literal["hint", "guided", "explained", "demonstrated"]

# Bloom's Taxonomy cognitive levels
BloomLevel = Literal["remember", "understand", "apply", "analyze", "evaluate", "create"]

# Pedagogical approaches based on educational research
PedagogicalApproach = Literal["socratic", "direct", "scaffolded", "exploratory"]


class ThinkingStep(TypedDict):
    """A single step in the agent's stochastic thinking process"""
    step_number: int
    thought: str
    alternatives_considered: Optional[List[str]]
    confidence: float
    selected: bool


class MathDerivation(TypedDict):
    """Structured mathematical derivation with steps"""
    concept: str
    intuition: str  # Visual/geometric explanation
    steps: List[dict]  # {step_number, latex, explanation}
    key_insight: str
    practice_problem: Optional[str]


class AgentState(TypedDict):
    """
    State schema for the tutor agent
    
    This state flows through the entire LangGraph pipeline:
    Governor → Supervisor → Agent → Tools → Evaluator
    """
    
    # ========== User Input ==========
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    
    # ========== User Context ==========
    user_id: Optional[str]
    user_email: Optional[str]
    user_role: Optional[Literal["student", "admin"]]
    trace_id: Optional[str]  # For linking manual spans
    parent_observation_id: Optional[str]  # For linking child spans to parent
    session_id: Optional[str]  # For Langfuse session tracking
    chat_id: Optional[str]  # For Supabase chat persistence
    langfuse_root_span: Optional[object]  # Root Langfuse span for creating child spans (v3 pattern)
    
    # ========== Conversation History (for context) ==========
    conversation_history: Optional[List[dict]]  # Prior messages: [{role, content, timestamp}]
    
    # ========== Routing Decisions ==========
    intent: Optional[str]  # "fast", "coder", "reasoning", "syllabus_query", "tutor", "math"
    model_selected: Optional[str]  # "gemini-flash", "groq-llama-70b", "gpt-4.1-mini", etc.
    model_override: Optional[str]  # User-specified model override (bypasses auto-selection)
    
    # ========== Reasoning Node Output (LLM-First Architecture) ==========
    # These fields are populated by the reasoning node before routing
    reasoning_complete: bool  # Flag indicating reasoning node has run
    reasoning_intent: Optional[str]  # Intent determined by reasoning (may differ from final)
    reasoning_confidence: Optional[float]  # Confidence in the intent (0.0-1.0)
    reasoning_strategy: Optional[str]  # Teaching strategy determined by reasoning
    reasoning_context_needed: Optional[List[str]]  # What context the reasoning node thinks we need
    reasoning_trace: Optional[str]  # Full reasoning trace for debugging
    
    # ========== Follow-up Context (NEW) ==========
    is_follow_up: Optional[bool]  # Is this a follow-up question?
    contextualized_query: Optional[str]  # Full query with context for follow-ups
    effective_query: Optional[str]  # Query to use for RAG/response (original or contextualized)
    
    # ========== Chain-of-Thought Visibility (NEW - Per CoT Paper) ==========
    # Visible reasoning steps shown to users for transparency
    # Based on "Chain-of-Thought Prompting Elicits Reasoning" (Wei et al., 2022)
    thought_chain: Optional[List[dict]]  # [{step, phase, thought, detail}, ...]
    key_concepts_detected: Optional[List[str]]  # Key AI/ML concepts identified in query
    
    # ========== Student History Context (NEW - Personalization) ==========
    # Fetched from Supabase for reminding students of prior work
    student_history_context: Optional[str]  # Formatted history string for prompts
    student_mastery_scores: Optional[dict]  # Dict of concept -> mastery score
    student_has_prior_sessions: Optional[bool]  # Whether student has prior interactions
    
    # ========== Curated Context (Context Engineering) ==========
    curated_context: Optional[str]  # Optimized context from ContextEngineer
    context_budget_tokens: Optional[int]  # Token budget for context window
    context_relevance_scores: Optional[dict]  # Relevance scores for context chunks
    
    # ========== RAG Context ==========
    retrieved_context: List[dict]  # Retrieved documents with metadata
    context_sources: List[dict]  # Source summaries with filenames/score
    
    # ========== Policy Enforcement ==========
    governor_approved: bool
    governor_reason: Optional[str]
    
    # ========== Pedagogical State (NEW) ==========
    # Scaffolding level based on student's current understanding
    scaffolding_level: Optional[ScaffoldingLevel]
    
    # Detected confusion from query analysis
    student_confusion_detected: bool
    
    # Stochastic thinking trace - agent explores multiple paths
    thinking_steps: Optional[List[ThinkingStep]]
    
    # Current Bloom's taxonomy level for the interaction
    bloom_level: Optional[BloomLevel]
    
    # Selected pedagogical approach for this response
    pedagogical_approach: Optional[PedagogicalApproach]
    
    # Diagnostic question state - track if we've asked and user's preference
    diagnostic_asked: bool  # Have we asked the user about depth preference?
    user_depth_preference: Optional[Literal["quick", "detailed", "unknown"]]  # User's stated preference
    
    # ========== Sub-agent Outputs ==========
    syllabus_check: Optional[dict]
    math_explanation: Optional[str]
    math_derivation: Optional[MathDerivation]  # Structured math work
    code_suggestion: Optional[str]
    pedagogical_strategy: Optional[str]
    
    # ========== Final Response ==========
    response: Optional[str]
    response_sources: List[str]  # Citations
    
    # ========== Quality Gate (Auto-Repair) ==========
    needs_repair: Optional[bool]  # Flag to trigger repair loop
    quality_retry_count: Optional[int]  # Number of repair attempts
    repair_guidance: Optional[str]  # Specific guidance for repair
    response_confidence: Optional[float]  # Calculated confidence score
    response_length_hint: Optional[Literal["short", "medium", "detailed"]]  # From reasoning node
    
    # ========== Error Handling ==========
    error: Optional[str]
    
    # ========== Execution Metadata (Observability) ==========
    request_id: Optional[str]  # Unique request identifier
    session_context: Optional[dict]  # Session-level context
    execution_start_time: Optional[float]  # Unix timestamp
    processing_times: Optional[dict]  # Node-level timing {node: duration_ms}
    context_lengths: Optional[dict]  # Context sizes {node: token_count}
    retrieval_metrics: Optional[dict]  # RAG retrieval stats
    model_parameters: Optional[dict]  # Model configuration used
    policy_decisions: Optional[List[dict]]  # Governor decision history
    cost_tracking: Optional[dict]  # Usage and cost details per model call

