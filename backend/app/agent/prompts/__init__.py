"""
Agent Prompts module

NOTE: No QUICK_ANSWER_PROMPT - all questions go through scaffolding.
This aligns with LearnLM principle: "Inspire active learning"
"""

from app.agent.prompts.tutor import (
    TUTOR_SYSTEM_PROMPT,
    MATH_PROMPT,
    OUT_OF_SCOPE_PROMPT,
    CODE_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_PROMPT,
)

__all__ = [
    "TUTOR_SYSTEM_PROMPT",
    "MATH_PROMPT",
    "OUT_OF_SCOPE_PROMPT",
    "CODE_PROMPT",
    "PLANNER_SYSTEM_PROMPT",
    "PLANNER_USER_PROMPT",
]
