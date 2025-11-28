# schemas/planner.py
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Literal, Dict, Any, Optional, Union, Annotated
from enum import Enum

class TaskType(str, Enum):
    EXPLAIN = "explain"
    SOLVE = "solve"
    CHAT = "chat"
    REJECT = "reject"

class BasePayload(BaseModel):
    type: str

class ExplainPayload(BasePayload):
    type: Literal[TaskType.EXPLAIN] = Field(default=TaskType.EXPLAIN, exclude=True)
    topic: str

class SolvePayload(BasePayload):
    type: Literal[TaskType.SOLVE] = Field(default=TaskType.SOLVE, exclude=True)
    problem: str

class ChatPayload(BasePayload):
    type: Literal[TaskType.CHAT] = Field(default=TaskType.CHAT, exclude=True)
    message: str

class RejectPayload(BasePayload):
    type: Literal[TaskType.REJECT] = Field(default=TaskType.REJECT, exclude=True)
    reason: str

# Create a Union of all payload types with discriminator
PayloadType = Annotated[
    Union[ExplainPayload, SolvePayload, ChatPayload, RejectPayload],
    Field(discriminator='type')
]

class Subtask(BaseModel):
    task: TaskType
    payload: PayloadType

class PlannerPlan(BaseModel):
    subtasks: List[Subtask]
    router_confidence: float = Field(0.0, ge=0, le=1)
    reasoning: str = ""                 # brief plain text of why
    rules_triggered: List[str] = []     # heuristic rule ids
    llm_used: bool = False              # whether LLM plan was used

    @validator("subtasks")
    def non_empty(cls, v):
        if not v:
            raise ValueError("Planner must return at least one subtask")
        return v
