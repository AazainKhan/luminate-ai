from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Plan(BaseModel):
    agent: str
    task: str
    topic: Optional[str] = None
    problem: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
