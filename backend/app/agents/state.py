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
    
    # ========== Routing Decisions ==========
    intent: Optional[str]  # "fast", "coder", "reasoning", "syllabus_query", "tutor", "math"
    model_selected: Optional[str]  # "gemini-flash", "groq-llama-70b"
    
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
    
    # ========== Sub-agent Outputs ==========
    syllabus_check: Optional[dict]
    math_explanation: Optional[str]
    math_derivation: Optional[MathDerivation]  # Structured math work
    code_suggestion: Optional[str]
    pedagogical_strategy: Optional[str]
    
    # ========== Final Response ==========
    response: Optional[str]
    response_sources: List[str]  # Citations
    
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

