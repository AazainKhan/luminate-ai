"""
Pydantic schemas for the agent - Zod-compatible for frontend validation

These schemas use discriminated unions and follow JSON Schema conventions
that map directly to Zod validators in TypeScript.

Includes ThinkingTrace schemas for streaming pedagogical reasoning to UI.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union, Annotated, Dict, Any
from enum import Enum
from datetime import datetime


# =============================================================================
# Task Types for Routing
# =============================================================================

class TaskType(str, Enum):
    """Task types that the planner can route to
    
    NOTE: No QUICK type - all questions go through scaffolding.
    Even "simple" questions benefit from activating prior knowledge.
    """
    EXPLAIN = "explain"      # Socratic tutoring with scaffolding (default)
    SOLVE = "solve"          # Step-by-step math derivations with scaffolding
    CODE = "code"            # Code help with scaffolding
    REJECT = "reject"        # Off-topic or policy violation


# =============================================================================
# Thinking Trace Schemas (for streaming pedagogical reasoning to UI)
# =============================================================================

class ThinkingStepType(str, Enum):
    """Types of thinking steps that can be streamed to UI"""
    SCOPE_CHECK = "scope_check"           # Is query within COMP237?
    INTEGRITY_CHECK = "integrity_check"   # Academic integrity violation?
    MASTERY_LOOKUP = "mastery_lookup"     # Student's current mastery level
    ESCALATION = "escalation"             # What scaffolding level to use
    RAG_RETRIEVAL = "rag_retrieval"       # Course materials retrieved
    STRATEGY = "strategy"                 # Teaching strategy selected
    FOLLOW_UP = "follow_up"               # Is this a conversation follow-up?
    CONCEPT_DETECTION = "concept_detection"  # What AI/ML concept is this about?


class ThinkingStep(BaseModel):
    """A single step in the agent's thinking trace - streamable to UI"""
    step: ThinkingStepType
    status: Literal["pending", "processing", "completed", "error"] = "pending"
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None  # Human-readable description
    timestamp_ms: Optional[int] = None


class ScopeCheckResult(BaseModel):
    """Result of scope checking"""
    in_scope: bool
    topic: Optional[str] = None
    confidence: float = 0.0
    method: Literal["regex", "rag", "keyword"] = "regex"


class IntegrityCheckResult(BaseModel):
    """Result of academic integrity check"""
    passed: bool
    violation_type: Optional[str] = None  # "cheating_request", "assignment_completion"


class MasteryLookupResult(BaseModel):
    """Result of student mastery lookup"""
    concept: Optional[str] = None
    mastery_score: float = 0.5  # 0.0 = no mastery, 1.0 = full mastery
    needs_scaffolding: bool = True
    last_assessed: Optional[str] = None


class EscalationResult(BaseModel):
    """Result of escalation level decision"""
    level: int = Field(1, ge=1, le=4)
    reason: str = "default"
    is_stuck: bool = False
    stuck_count: int = 0


class RAGRetrievalResult(BaseModel):
    """Result of RAG retrieval"""
    docs_found: int = 0
    has_comp237_content: bool = False
    top_sources: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0


class StrategyResult(BaseModel):
    """Teaching strategy selection"""
    strategy: Literal["diagnostic", "socratic", "hints", "example", "direct", "redirect"] = "diagnostic"
    reasoning: str = ""


class ThinkingTrace(BaseModel):
    """Complete thinking trace for an agent execution"""
    steps: List[ThinkingStep] = Field(default_factory=list)
    scope_check: Optional[ScopeCheckResult] = None
    integrity_check: Optional[IntegrityCheckResult] = None
    mastery_lookup: Optional[MasteryLookupResult] = None
    escalation: Optional[EscalationResult] = None
    rag_retrieval: Optional[RAGRetrievalResult] = None
    strategy: Optional[StrategyResult] = None
    
    def add_step(self, step_type: ThinkingStepType, status: str = "completed", 
                 result: Optional[Dict] = None, message: Optional[str] = None):
        """Add a step to the trace"""
        import time
        self.steps.append(ThinkingStep(
            step=step_type,
            status=status,
            result=result,
            message=message,
            timestamp_ms=int(time.time() * 1000)
        ))


# =============================================================================
# Payload Types (Discriminated Union for Zod compatibility)
# =============================================================================

class ExplainPayload(BaseModel):
    """Payload for explain tasks - full Socratic scaffolding"""
    type: Literal["explain"] = "explain"
    topic: str = Field(..., description="The topic to explain")
    escalation_level: int = Field(1, ge=1, le=4, description="Scaffolding level 1-4")


class SolvePayload(BaseModel):
    """Payload for math/solve tasks"""
    type: Literal["solve"] = "solve"
    problem: str = Field(..., description="The problem to solve")


class CodePayload(BaseModel):
    """Payload for code tasks"""
    type: Literal["code"] = "code"
    request: str = Field(..., description="The code request")
    language: str = Field("python", description="Programming language")


class RejectPayload(BaseModel):
    """Payload for rejected queries"""
    type: Literal["reject"] = "reject"
    reason: str = Field(..., description="Reason for rejection")


# Discriminated union - maps to Zod discriminatedUnion()
# NOTE: No QuickPayload - all questions go through scaffolding
PayloadType = Annotated[
    Union[ExplainPayload, SolvePayload, CodePayload, RejectPayload],
    Field(discriminator="type")
]


# =============================================================================
# Planner Schemas
# =============================================================================

class Subtask(BaseModel):
    """A single subtask in the plan"""
    task: TaskType
    payload: PayloadType


class PlannerPlan(BaseModel):
    """The planner's routing decision"""
    subtasks: List[Subtask] = Field(..., min_length=1)
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Routing confidence")
    reasoning: str = Field("", description="Brief explanation of routing decision")


# =============================================================================
# Source/Citation Schemas
# =============================================================================

class Source(BaseModel):
    """A source citation from RAG retrieval (multi-collection support)"""
    title: str = Field(..., description="Title or identifier of the source")
    source_file: str = Field(..., description="File name or path (e.g., 'Module 4 - Topic 4.1')")
    collection: str = Field("COMP237", description="ChromaDB collection name")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance score (0-1)")
    content: Optional[str] = Field(None, description="Snippet of content for preview")
    page: Optional[int] = Field(None, description="Page number if applicable")
    week: Optional[int] = Field(None, description="Course week number (1-14)")
    module: Optional[str] = Field(None, description="Module name (e.g., 'Module 4')")
    description: Optional[str] = Field(None, description="Brief description of what this source covers")
    
    # Multi-collection fields
    source_type: Optional[str] = Field(None, description="Source type: course, oer, or embedded")
    citation_confidence: Optional[str] = Field(None, description="Citation confidence: high, medium, or low")
    url: Optional[str] = Field(None, description="URL for embedded resources (mediasite, external links)")
    link_type: Optional[str] = Field(None, description="Link type: mediasite, generic_url, etc.")


class RAGMetadata(BaseModel):
    """Metadata from RAG retrieval"""
    docs_retrieved: int = Field(0, ge=0)
    sources_used: List[str] = Field(default_factory=list)
    retrieval_success: bool = False
    has_comp237: bool = False


# =============================================================================
# Streaming Event Schemas (AI SDK v5 compatible)
# =============================================================================

class BaseStreamEvent(BaseModel):
    """Base class for all stream events"""
    type: str


class TextDeltaEvent(BaseStreamEvent):
    """Text chunk during streaming"""
    type: Literal["text-delta"] = "text-delta"
    textDelta: str


class SourcesEvent(BaseStreamEvent):
    """Sources retrieved from RAG"""
    type: Literal["sources"] = "sources"
    sources: List[Source]


class QueueInitEvent(BaseStreamEvent):
    """Initialize the processing queue UI"""
    type: Literal["queue-init"] = "queue-init"
    queue: List[dict]


class QueueUpdateEvent(BaseStreamEvent):
    """Update a queue item's status"""
    type: Literal["queue-update"] = "queue-update"
    queueItemId: str
    status: Literal["pending", "processing", "completed", "error"]


class ThinkingEvent(BaseStreamEvent):
    """Thinking step event for streaming reasoning to UI"""
    type: Literal["thinking"] = "thinking"
    step: str  # ThinkingStepType value
    status: Literal["pending", "processing", "completed", "error"] = "completed"
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class TraceIdEvent(BaseStreamEvent):
    """Langfuse trace ID for observability"""
    type: Literal["trace-id"] = "trace-id"
    traceId: str


class ErrorEvent(BaseStreamEvent):
    """Error during processing"""
    type: Literal["error"] = "error"
    error: str


class FinishEvent(BaseStreamEvent):
    """Signal completion"""
    type: Literal["finish"] = "finish"
    chatId: Optional[str] = None
    traceId: Optional[str] = None


# Union of all stream events for type safety
StreamEvent = Union[
    TextDeltaEvent,
    SourcesEvent,
    QueueInitEvent,
    QueueUpdateEvent,
    ThinkingEvent,
    TraceIdEvent,
    ErrorEvent,
    FinishEvent,
]


# =============================================================================
# Polymorphic Response Types (Generative UI)
# =============================================================================

class TextResponse(BaseModel):
    """Standard text response"""
    type: Literal["text"] = "text"
    content: str

class QuizOption(BaseModel):
    id: str
    text: str
    is_correct: bool
    explanation: Optional[str] = None

class QuizResponse(BaseModel):
    """Interactive quiz component"""
    type: Literal["quiz"] = "quiz"
    question: str
    options: List[QuizOption]
    topic: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"

class CodeDiffResponse(BaseModel):
    """Code difference view"""
    type: Literal["code_diff"] = "code_diff"
    original_code: str
    improved_code: str
    language: str = "python"
    explanation: str

class SocraticDialogueResponse(BaseModel):
    """Structured Socratic dialogue step"""
    type: Literal["socratic"] = "socratic"
    context: str
    question: str
    hint: Optional[str] = None
    expected_concept: str

# Union for polymorphic responses
InterventionType = Annotated[
    Union[TextResponse, QuizResponse, CodeDiffResponse, SocraticDialogueResponse],
    Field(discriminator="type")
]


# =============================================================================
# Response Schemas
# =============================================================================

class AgentResponse(BaseModel):
    """Complete response from the agent"""
    response: str = Field(..., description="The generated response text")
    intervention: Optional[InterventionType] = Field(None, description="Polymorphic UI component to render")
    sources: List[Source] = Field(default_factory=list)
    intent: str = Field("explain", description="Detected intent")
    escalation_level: int = Field(1, ge=1, le=4)
    rag_metadata: RAGMetadata = Field(default_factory=RAGMetadata)
    trace_id: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Evaluation Schemas
# =============================================================================

class EvaluationScores(BaseModel):
    """Quality evaluation scores"""
    pedagogical_quality: float = Field(0.0, ge=0.0, le=1.0)
    policy_compliance: bool = True
    response_confidence: float = Field(0.0, ge=0.0, le=1.0)
    scaffolding_appropriate: bool = True
