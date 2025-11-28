from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from typing import Literal

class Step(BaseModel):
    title: str
    text: str

class Source(BaseModel):
    marker: str
    collection: str
    metadata: Dict[str, Any]

class ComputationResult(BaseModel):
    tool: str
    input: str
    result_text: str
    result_latex: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

class MathTask(BaseModel):
    agent: Literal["MathAgent"] = "MathAgent"
    task: Literal["solve"] = "solve"
    problem: str
    topic: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None

class MathAgentOutput(BaseModel):
    final_answer: str
    final_answer_latex: Optional[str] = None
    steps: List[Step]
    concepts_used: List[str]
    sources: List[Source]
    computation: Optional[ComputationResult] = None
    needs_clarification: bool = False
    clarifying_questions: List[str] = []
    confidence: float = 0.6
    notes: Optional[str] = None
