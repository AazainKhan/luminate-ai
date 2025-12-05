"""
Model Comparison Test Package

This package provides tools for comparing different LLM models
across pedagogical, factual, code, and instruction-following tasks.
"""

from .test_cases import TestCase, TestCategory, TEST_CASES, get_all_test_cases
from .model_runner import ModelRunner, ModelResponse
from .evaluator import ResponseEvaluator, EvaluationResult

__all__ = [
    "TestCase",
    "TestCategory", 
    "TEST_CASES",
    "get_all_test_cases",
    "ModelRunner",
    "ModelResponse",
    "ResponseEvaluator",
    "EvaluationResult",
]
