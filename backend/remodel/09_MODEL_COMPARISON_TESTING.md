# Model Comparison Testing Framework

## Overview

This document describes a framework for testing and comparing different LLM models to optimize response quality, latency, and cost across different use cases.

---

## Current Model Configuration

### Available Models

```python
# From config.py and supervisor.py
MODELS = {
    "gemini-2.0-flash": {
        "provider": "google",
        "use_case": "general purpose",
        "temperature": 0.7,
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
    },
    "gemini-tutor": {
        "provider": "google",
        "use_case": "pedagogical (high creativity)",
        "temperature": 0.9,
        "model_name": "gemini-2.0-flash",  # Same model, different temp
    },
    "gemini-classifier": {
        "provider": "google",
        "use_case": "intent classification",
        "temperature": 0.1,
    },
    "groq-llama-3.3-70b-versatile": {
        "provider": "groq",
        "use_case": "code generation, fast responses",
        "temperature": 0.5,
        "cost_per_1k_tokens": 0.00059,  # Much cheaper
    },
}
```

### Routing Matrix

| Intent | Current Model | Notes |
|--------|--------------|-------|
| tutor | gemini-tutor (temp=0.9) | Socratic scaffolding |
| math | gemini-flash | Step-by-step derivations |
| coder | groq-llama-70b | Code generation |
| syllabus_query | gemini-flash | Course info |
| explain | gemini-flash | Medium explanations |
| fast | groq-fast | Quick answers |

---

## Comparison Framework Design

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Model Comparison Framework                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Test Suite   │───▶│ Model Runner │───▶│ Evaluator    │      │
│  │              │    │              │    │              │      │
│  │ • Queries    │    │ • Parallel   │    │ • Quality    │      │
│  │ • Expected   │    │   execution  │    │ • Latency    │      │
│  │   behaviors  │    │ • Streaming  │    │ • Cost       │      │
│  │ • Edge cases │    │ • Timeout    │    │ • Format     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
│                              │                                   │
│                              ▼                                   │
│                    ┌──────────────────┐                         │
│                    │ Results Analyzer │                         │
│                    │                  │                         │
│                    │ • Rankings       │                         │
│                    │ • Visualizations │                         │
│                    │ • Recommendations│                         │
│                    └──────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation

### Test Suite Definition

```python
# backend/tests/model_comparison/test_cases.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class TestCategory(Enum):
    PEDAGOGICAL = "pedagogical"
    FACTUAL = "factual"
    CODE = "code"
    MATH = "math"
    CREATIVITY = "creativity"
    INSTRUCTION_FOLLOWING = "instruction_following"


@dataclass
class TestCase:
    id: str
    category: TestCategory
    query: str
    expected_behaviors: List[str]  # What should be present
    forbidden_behaviors: List[str]  # What should NOT be present
    ideal_length: tuple[int, int]  # (min_chars, max_chars)
    requires_sources: bool = False
    requires_structure: bool = False
    metadata: Optional[Dict] = None


# Test cases for model comparison
TEST_CASES = [
    # Pedagogical - Socratic Teaching
    TestCase(
        id="ped_001",
        category=TestCategory.PEDAGOGICAL,
        query="I'm confused about backpropagation. Can you help me understand it?",
        expected_behaviors=[
            "asks clarifying question",
            "builds on prior knowledge",
            "provides analogy or example",
            "does not give full answer immediately",
        ],
        forbidden_behaviors=[
            "gives complete solution",
            "uses overwhelming jargon",
            "lecture-style monologue",
        ],
        ideal_length=(500, 2000),
        requires_structure=True,
    ),
    TestCase(
        id="ped_002",
        category=TestCategory.PEDAGOGICAL,
        query="what is gradient descent",
        expected_behaviors=[
            "concise explanation",
            "intuitive analogy",
            "offers to elaborate",
        ],
        forbidden_behaviors=[
            "full mathematical derivation",
            "lengthy scaffolding",
        ],
        ideal_length=(200, 800),
    ),
    
    # Factual - Quick Information
    TestCase(
        id="fact_001",
        category=TestCategory.FACTUAL,
        query="What topics are covered in COMP 237?",
        expected_behaviors=[
            "lists course topics",
            "concise answer",
        ],
        forbidden_behaviors=[
            "socratic questions",
            "asks for clarification",
        ],
        ideal_length=(100, 400),
        requires_sources=True,
    ),
    
    # Code Generation
    TestCase(
        id="code_001",
        category=TestCategory.CODE,
        query="Write a Python function to implement a perceptron",
        expected_behaviors=[
            "provides working code",
            "includes comments",
            "explains key parts",
        ],
        forbidden_behaviors=[
            "refuses to give code",
            "gives pseudocode only",
        ],
        ideal_length=(400, 1500),
    ),
    TestCase(
        id="code_002",
        category=TestCategory.CODE,
        query="Debug this: def sigmoid(x): return 1/1+np.exp(-x)",
        expected_behaviors=[
            "identifies the bug (parentheses)",
            "provides corrected code",
            "explains the issue",
        ],
        forbidden_behaviors=[
            "says code looks correct",
        ],
        ideal_length=(200, 800),
    ),
    
    # Math Derivations
    TestCase(
        id="math_001",
        category=TestCategory.MATH,
        query="Derive the gradient for MSE loss",
        expected_behaviors=[
            "step-by-step derivation",
            "uses LaTeX notation",
            "explains each step",
        ],
        forbidden_behaviors=[
            "skips steps",
            "gives only final answer",
        ],
        ideal_length=(500, 2000),
    ),
    
    # Instruction Following
    TestCase(
        id="inst_001",
        category=TestCategory.INSTRUCTION_FOLLOWING,
        query="Briefly explain neural networks in one sentence",
        expected_behaviors=[
            "exactly one sentence",
            "concise",
        ],
        forbidden_behaviors=[
            "multiple sentences",
            "long explanation",
        ],
        ideal_length=(50, 200),
    ),
    TestCase(
        id="inst_002",
        category=TestCategory.INSTRUCTION_FOLLOWING,
        query="List exactly 3 types of machine learning",
        expected_behaviors=[
            "exactly 3 items",
            "numbered or bulleted",
        ],
        forbidden_behaviors=[
            "more than 3 items",
            "fewer than 3 items",
        ],
        ideal_length=(50, 300),
    ),
]
```

### Model Runner

```python
# backend/tests/model_comparison/model_runner.py

import asyncio
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.config import settings


@dataclass
class ModelResponse:
    model_name: str
    response_text: str
    latency_ms: float
    tokens_used: Dict[str, int]
    cost_estimate: float
    error: Optional[str] = None


class ModelRunner:
    """Run queries against multiple models for comparison."""
    
    MODELS_TO_TEST = {
        "gemini-flash": {
            "provider": "google",
            "model_name": "gemini-2.0-flash",
            "temperature": 0.7,
        },
        "gemini-creative": {
            "provider": "google",
            "model_name": "gemini-2.0-flash",
            "temperature": 0.9,
        },
        "gemini-precise": {
            "provider": "google",
            "model_name": "gemini-2.0-flash",
            "temperature": 0.3,
        },
        "groq-llama-70b": {
            "provider": "groq",
            "model_name": "llama-3.3-70b-versatile",
            "temperature": 0.7,
        },
        "groq-llama-70b-precise": {
            "provider": "groq",
            "model_name": "llama-3.3-70b-versatile",
            "temperature": 0.3,
        },
    }
    
    # Cost estimates per 1K tokens
    COST_MAP = {
        "gemini-2.0-flash": {"input": 0.00015, "output": 0.0006},
        "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
    }
    
    def __init__(self, system_prompt: Optional[str] = None):
        self.system_prompt = system_prompt or "You are a helpful AI tutor for COMP 237."
        self._init_models()
    
    def _init_models(self):
        """Initialize all model clients."""
        self.models = {}
        
        for name, config in self.MODELS_TO_TEST.items():
            if config["provider"] == "google":
                self.models[name] = ChatGoogleGenerativeAI(
                    model=config["model_name"],
                    temperature=config["temperature"],
                    google_api_key=settings.google_api_key,
                )
            elif config["provider"] == "groq":
                self.models[name] = ChatGroq(
                    model=config["model_name"],
                    temperature=config["temperature"],
                    api_key=settings.groq_api_key,
                )
    
    async def run_query(
        self,
        model_name: str,
        query: str,
        timeout: float = 30.0
    ) -> ModelResponse:
        """Run a single query against a model."""
        if model_name not in self.models:
            return ModelResponse(
                model_name=model_name,
                response_text="",
                latency_ms=0,
                tokens_used={},
                cost_estimate=0,
                error=f"Model {model_name} not found"
            )
        
        model = self.models[model_name]
        config = self.MODELS_TO_TEST[model_name]
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            start_time = time.perf_counter()
            
            # Run with timeout
            response = await asyncio.wait_for(
                model.ainvoke(messages),
                timeout=timeout
            )
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Extract token usage
            tokens = {}
            if hasattr(response, "usage_metadata"):
                tokens = {
                    "input": response.usage_metadata.get("input_tokens", 0),
                    "output": response.usage_metadata.get("output_tokens", 0),
                }
            
            # Estimate cost
            base_model = config["model_name"]
            cost_rates = self.COST_MAP.get(base_model, {"input": 0, "output": 0})
            cost = (
                tokens.get("input", 0) * cost_rates["input"] / 1000 +
                tokens.get("output", 0) * cost_rates["output"] / 1000
            )
            
            return ModelResponse(
                model_name=model_name,
                response_text=response.content,
                latency_ms=latency_ms,
                tokens_used=tokens,
                cost_estimate=cost,
            )
        
        except asyncio.TimeoutError:
            return ModelResponse(
                model_name=model_name,
                response_text="",
                latency_ms=timeout * 1000,
                tokens_used={},
                cost_estimate=0,
                error="Timeout"
            )
        except Exception as e:
            return ModelResponse(
                model_name=model_name,
                response_text="",
                latency_ms=0,
                tokens_used={},
                cost_estimate=0,
                error=str(e)
            )
    
    async def run_comparison(
        self,
        query: str,
        models: Optional[List[str]] = None
    ) -> Dict[str, ModelResponse]:
        """Run the same query against multiple models in parallel."""
        models_to_run = models or list(self.MODELS_TO_TEST.keys())
        
        tasks = [
            self.run_query(model_name, query)
            for model_name in models_to_run
        ]
        
        responses = await asyncio.gather(*tasks)
        
        return {resp.model_name: resp for resp in responses}
```

### Response Evaluator

```python
# backend/tests/model_comparison/evaluator.py

import re
from dataclasses import dataclass
from typing import List, Dict
from test_cases import TestCase, TestCategory


@dataclass
class EvaluationResult:
    test_id: str
    model_name: str
    
    # Scores (0.0 - 1.0)
    behavior_score: float  # Expected behaviors present
    forbidden_score: float  # Forbidden behaviors absent
    length_score: float  # Within ideal length
    source_score: float  # Sources included if required
    structure_score: float  # Proper formatting if required
    
    # Composite
    overall_score: float
    
    # Details
    behaviors_present: List[str]
    behaviors_missing: List[str]
    forbidden_present: List[str]
    actual_length: int
    
    # Meta
    latency_ms: float
    cost_estimate: float


class ResponseEvaluator:
    """Evaluate model responses against test case criteria."""
    
    # Patterns for detecting behaviors
    BEHAVIOR_PATTERNS = {
        "asks clarifying question": r"\?.*$|do you|would you|can you tell|what do you",
        "builds on prior knowledge": r"as you (may )?know|remember|recall|previously|building on",
        "provides analogy or example": r"for example|like|imagine|think of|consider",
        "does not give full answer immediately": r"^(?!.*(?:the answer is|here's the solution|the result)).*$",
        "concise explanation": lambda text: len(text) < 800,
        "intuitive analogy": r"like|imagine|think of|picture|similar to",
        "offers to elaborate": r"want me to|would you like|shall I|let me know if",
        "lists course topics": r"(?:\d+[\.\)]\s*|\*\s*|•\s*|[-]\s*).*(?:\n|$)",
        "provides working code": r"```(?:python|py)?\n.*?```",
        "includes comments": r"#.*\n|'''.*?'''|\"\"\".*?\"\"\"",
        "explains key parts": r"this (?:line|part|section)|here we|notice that",
        "identifies the bug": r"bug|error|issue|problem|fix|incorrect",
        "step-by-step derivation": r"step \d|first,|then,|finally,|next,",
        "uses LaTeX notation": r"\$.*?\$|\\\[.*?\\\]|\\frac|\\sum|\\partial",
        "exactly one sentence": lambda text: text.count('.') <= 2 and len(text) < 300,
        "exactly 3 items": lambda text: len(re.findall(r'^\s*(?:\d+[\.\)]|\*|•|-)\s*', text, re.MULTILINE)) == 3,
        "numbered or bulleted": r"^\s*(?:\d+[\.\)]|\*|•|-)\s*",
    }
    
    FORBIDDEN_PATTERNS = {
        "gives complete solution": r"complete solution|full answer|here's everything",
        "uses overwhelming jargon": lambda text: len(re.findall(r'\b[A-Z]{2,}\b', text)) > 10,
        "lecture-style monologue": lambda text: len(text) > 3000 and text.count('?') < 2,
        "full mathematical derivation": lambda text: text.count('$') > 10 or len(re.findall(r'\\frac|\\sum', text)) > 5,
        "lengthy scaffolding": lambda text: len(text) > 1500,
        "socratic questions": r"\?.*\?.*\?",  # Multiple questions
        "asks for clarification": r"could you clarify|what do you mean|can you explain",
        "refuses to give code": r"I (?:can't|cannot|won't) (?:provide|write|give)",
        "gives pseudocode only": r"(?:pseudocode|pseudo-code|algorithm steps)(?:.*\n){3,}",
        "says code looks correct": r"looks correct|is correct|no issues",
        "skips steps": r"therefore|thus|hence|so we get",
        "gives only final answer": lambda text: len(text) < 200 and 'step' not in text.lower(),
        "multiple sentences": lambda text: text.count('.') > 2,
        "long explanation": lambda text: len(text) > 300,
        "more than 3 items": lambda text: len(re.findall(r'^\s*(?:\d+[\.\)]|\*|•|-)\s*', text, re.MULTILINE)) > 3,
        "fewer than 3 items": lambda text: len(re.findall(r'^\s*(?:\d+[\.\)]|\*|•|-)\s*', text, re.MULTILINE)) < 3,
    }
    
    def evaluate(
        self,
        test_case: TestCase,
        model_name: str,
        response_text: str,
        latency_ms: float,
        cost_estimate: float
    ) -> EvaluationResult:
        """Evaluate a model response against test case criteria."""
        
        # Check expected behaviors
        behaviors_present = []
        behaviors_missing = []
        
        for behavior in test_case.expected_behaviors:
            if self._check_behavior(behavior, response_text, self.BEHAVIOR_PATTERNS):
                behaviors_present.append(behavior)
            else:
                behaviors_missing.append(behavior)
        
        behavior_score = len(behaviors_present) / max(len(test_case.expected_behaviors), 1)
        
        # Check forbidden behaviors
        forbidden_present = []
        
        for behavior in test_case.forbidden_behaviors:
            if self._check_behavior(behavior, response_text, self.FORBIDDEN_PATTERNS):
                forbidden_present.append(behavior)
        
        forbidden_score = 1.0 - (len(forbidden_present) / max(len(test_case.forbidden_behaviors), 1))
        
        # Check length
        actual_length = len(response_text)
        min_len, max_len = test_case.ideal_length
        
        if min_len <= actual_length <= max_len:
            length_score = 1.0
        elif actual_length < min_len:
            length_score = max(0, actual_length / min_len)
        else:
            length_score = max(0, 1.0 - (actual_length - max_len) / max_len)
        
        # Check sources (if required)
        if test_case.requires_sources:
            source_patterns = r'\[.*?source.*?\]|\[from:.*?\]|according to|based on|from the'
            source_score = 1.0 if re.search(source_patterns, response_text, re.I) else 0.0
        else:
            source_score = 1.0
        
        # Check structure (if required)
        if test_case.requires_structure:
            structure_patterns = [
                r'\*\*.*?\*\*',  # Bold headings
                r'^#+\s',  # Markdown headers
                r'^\s*[-\*•]\s',  # Lists
            ]
            structure_score = sum(
                1 for p in structure_patterns
                if re.search(p, response_text, re.MULTILINE)
            ) / len(structure_patterns)
        else:
            structure_score = 1.0
        
        # Composite score (weighted)
        overall_score = (
            behavior_score * 0.35 +
            forbidden_score * 0.25 +
            length_score * 0.20 +
            source_score * 0.10 +
            structure_score * 0.10
        )
        
        return EvaluationResult(
            test_id=test_case.id,
            model_name=model_name,
            behavior_score=behavior_score,
            forbidden_score=forbidden_score,
            length_score=length_score,
            source_score=source_score,
            structure_score=structure_score,
            overall_score=overall_score,
            behaviors_present=behaviors_present,
            behaviors_missing=behaviors_missing,
            forbidden_present=forbidden_present,
            actual_length=actual_length,
            latency_ms=latency_ms,
            cost_estimate=cost_estimate,
        )
    
    def _check_behavior(self, behavior: str, text: str, patterns: Dict) -> bool:
        """Check if a behavior is present in the text."""
        if behavior not in patterns:
            # Fallback to substring match
            return behavior.lower() in text.lower()
        
        pattern = patterns[behavior]
        
        if callable(pattern):
            return pattern(text)
        else:
            return bool(re.search(pattern, text, re.MULTILINE | re.IGNORECASE))
```

### Results Analyzer

```python
# backend/tests/model_comparison/analyzer.py

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict
from collections import defaultdict
from datetime import datetime
from evaluator import EvaluationResult
from test_cases import TestCategory


@dataclass
class ModelRanking:
    model_name: str
    avg_score: float
    avg_latency_ms: float
    total_cost: float
    category_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]


class ResultsAnalyzer:
    """Analyze comparison results and generate recommendations."""
    
    def __init__(self, results: List[EvaluationResult]):
        self.results = results
    
    def get_model_rankings(self) -> List[ModelRanking]:
        """Get overall model rankings."""
        model_results = defaultdict(list)
        
        for result in self.results:
            model_results[result.model_name].append(result)
        
        rankings = []
        
        for model_name, results in model_results.items():
            avg_score = sum(r.overall_score for r in results) / len(results)
            avg_latency = sum(r.latency_ms for r in results) / len(results)
            total_cost = sum(r.cost_estimate for r in results)
            
            # Category breakdown
            category_scores = self._get_category_scores(results)
            
            # Find strengths and weaknesses
            strengths = [cat for cat, score in category_scores.items() if score > 0.8]
            weaknesses = [cat for cat, score in category_scores.items() if score < 0.5]
            
            rankings.append(ModelRanking(
                model_name=model_name,
                avg_score=avg_score,
                avg_latency_ms=avg_latency,
                total_cost=total_cost,
                category_scores=category_scores,
                strengths=strengths,
                weaknesses=weaknesses,
            ))
        
        # Sort by score descending
        rankings.sort(key=lambda x: x.avg_score, reverse=True)
        
        return rankings
    
    def _get_category_scores(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """Get average scores per category for a model."""
        # Map test_id prefix to category
        category_map = {
            "ped_": TestCategory.PEDAGOGICAL.value,
            "fact_": TestCategory.FACTUAL.value,
            "code_": TestCategory.CODE.value,
            "math_": TestCategory.MATH.value,
            "inst_": TestCategory.INSTRUCTION_FOLLOWING.value,
        }
        
        category_scores = defaultdict(list)
        
        for result in results:
            for prefix, category in category_map.items():
                if result.test_id.startswith(prefix):
                    category_scores[category].append(result.overall_score)
                    break
        
        return {
            cat: sum(scores) / len(scores)
            for cat, scores in category_scores.items()
            if scores
        }
    
    def get_recommendations(self) -> Dict[str, str]:
        """Get routing recommendations based on results."""
        rankings = self.get_model_rankings()
        
        # Find best model per category
        category_best = {}
        
        for ranking in rankings:
            for category, score in ranking.category_scores.items():
                if category not in category_best or score > category_best[category][1]:
                    category_best[category] = (ranking.model_name, score)
        
        # Map categories to intents
        intent_map = {
            TestCategory.PEDAGOGICAL.value: "tutor",
            TestCategory.FACTUAL.value: "syllabus_query",
            TestCategory.CODE.value: "coder",
            TestCategory.MATH.value: "math",
            TestCategory.INSTRUCTION_FOLLOWING.value: "fast",
        }
        
        recommendations = {}
        for category, (model, score) in category_best.items():
            intent = intent_map.get(category, category)
            recommendations[intent] = model
        
        return recommendations
    
    def generate_report(self, output_path: Path) -> None:
        """Generate a markdown report of results."""
        rankings = self.get_model_rankings()
        recommendations = self.get_recommendations()
        
        report = ["# Model Comparison Report\n"]
        report.append(f"Generated: {datetime.now().isoformat()}\n")
        report.append(f"Total tests: {len(self.results)}\n\n")
        
        # Rankings table
        report.append("## Overall Rankings\n\n")
        report.append("| Rank | Model | Avg Score | Avg Latency | Total Cost |\n")
        report.append("|------|-------|-----------|-------------|------------|\n")
        
        for i, ranking in enumerate(rankings, 1):
            report.append(
                f"| {i} | {ranking.model_name} | {ranking.avg_score:.2f} | "
                f"{ranking.avg_latency_ms:.0f}ms | ${ranking.total_cost:.4f} |\n"
            )
        
        # Category breakdown
        report.append("\n## Category Performance\n\n")
        
        for ranking in rankings:
            report.append(f"### {ranking.model_name}\n\n")
            report.append("| Category | Score |\n")
            report.append("|----------|-------|\n")
            
            for cat, score in ranking.category_scores.items():
                report.append(f"| {cat} | {score:.2f} |\n")
            
            if ranking.strengths:
                report.append(f"\n**Strengths:** {', '.join(ranking.strengths)}\n")
            if ranking.weaknesses:
                report.append(f"\n**Weaknesses:** {', '.join(ranking.weaknesses)}\n")
            
            report.append("\n")
        
        # Recommendations
        report.append("## Routing Recommendations\n\n")
        report.append("Based on the comparison results, the recommended model for each intent:\n\n")
        report.append("| Intent | Recommended Model |\n")
        report.append("|--------|-------------------|\n")
        
        for intent, model in recommendations.items():
            report.append(f"| {intent} | {model} |\n")
        
        # Write report
        output_path.write_text("".join(report))
    
    def save_raw_results(self, output_path: Path) -> None:
        """Save raw results as JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results],
            "rankings": [asdict(r) for r in self.get_model_rankings()],
            "recommendations": self.get_recommendations(),
        }
        
        output_path.write_text(json.dumps(data, indent=2))
```

### Main Test Runner

```python
# backend/tests/model_comparison/run_comparison.py

import asyncio
import logging
from pathlib import Path
from datetime import datetime

from test_cases import TEST_CASES
from model_runner import ModelRunner
from evaluator import ResponseEvaluator
from analyzer import ResultsAnalyzer, EvaluationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_full_comparison():
    """Run complete model comparison test suite."""
    
    logger.info(f"Starting model comparison with {len(TEST_CASES)} test cases")
    
    # Initialize components
    runner = ModelRunner()
    evaluator = ResponseEvaluator()
    
    all_results: list[EvaluationResult] = []
    
    for test_case in TEST_CASES:
        logger.info(f"Running test: {test_case.id} - {test_case.query[:50]}...")
        
        # Run query against all models
        responses = await runner.run_comparison(test_case.query)
        
        # Evaluate each response
        for model_name, response in responses.items():
            if response.error:
                logger.warning(f"  {model_name}: ERROR - {response.error}")
                continue
            
            result = evaluator.evaluate(
                test_case=test_case,
                model_name=model_name,
                response_text=response.response_text,
                latency_ms=response.latency_ms,
                cost_estimate=response.cost_estimate,
            )
            
            all_results.append(result)
            
            logger.info(
                f"  {model_name}: score={result.overall_score:.2f}, "
                f"latency={result.latency_ms:.0f}ms"
            )
    
    # Analyze results
    analyzer = ResultsAnalyzer(all_results)
    
    # Generate outputs
    output_dir = Path("test_output/model_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save report
    report_path = output_dir / f"report_{timestamp}.md"
    analyzer.generate_report(report_path)
    logger.info(f"Report saved to: {report_path}")
    
    # Save raw data
    data_path = output_dir / f"results_{timestamp}.json"
    analyzer.save_raw_results(data_path)
    logger.info(f"Raw results saved to: {data_path}")
    
    # Print summary
    rankings = analyzer.get_model_rankings()
    
    print("\n" + "=" * 60)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 60)
    
    for i, ranking in enumerate(rankings, 1):
        print(f"\n{i}. {ranking.model_name}")
        print(f"   Score: {ranking.avg_score:.2f}")
        print(f"   Latency: {ranking.avg_latency_ms:.0f}ms")
        print(f"   Cost: ${ranking.total_cost:.4f}")
        if ranking.strengths:
            print(f"   Strengths: {', '.join(ranking.strengths)}")
        if ranking.weaknesses:
            print(f"   Weaknesses: {', '.join(ranking.weaknesses)}")
    
    print("\n" + "-" * 60)
    print("RECOMMENDED ROUTING:")
    for intent, model in analyzer.get_recommendations().items():
        print(f"  {intent}: {model}")
    print("=" * 60)
    
    return all_results


if __name__ == "__main__":
    asyncio.run(run_full_comparison())
```

---

## Groq Model Router Integration

### Arch-Router Research

Based on web search results, there are several approaches to intelligent model routing:

1. **Arch-Router** (SambaNova): 1.5B param model for preference-aligned routing, 93% accuracy, 50ms latency
2. **RouteLLM** (LMSys): Cost-based routing between expensive/cheap models
3. **Custom Intent Router**: Use lightweight classifier to route by task type

### Proposed Integration

```python
# backend/app/agents/smart_router.py

from typing import Dict, Optional, Tuple
import re
from langchain_groq import ChatGroq
from app.config import settings


class SmartRouter:
    """
    Intelligent model router that selects the best model based on:
    1. Task type (pedagogical, code, math, etc.)
    2. Required quality level
    3. Latency requirements
    4. Cost optimization
    """
    
    # Model tiers
    MODELS = {
        "tier1_quality": {
            "name": "gemini-2.0-flash",
            "provider": "google",
            "temperature": 0.7,
            "best_for": ["pedagogical", "complex_reasoning"],
            "cost": "medium",
            "latency": "medium",
        },
        "tier1_creative": {
            "name": "gemini-2.0-flash",
            "provider": "google", 
            "temperature": 0.9,
            "best_for": ["socratic", "brainstorming"],
            "cost": "medium",
            "latency": "medium",
        },
        "tier2_fast": {
            "name": "llama-3.3-70b-versatile",
            "provider": "groq",
            "temperature": 0.5,
            "best_for": ["code", "factual", "fast_response"],
            "cost": "low",
            "latency": "fast",
        },
        "tier3_cheap": {
            "name": "llama-3.3-8b-instant",
            "provider": "groq",
            "temperature": 0.3,
            "best_for": ["classification", "simple_qa"],
            "cost": "very_low",
            "latency": "very_fast",
        },
    }
    
    # Task to model mapping (from comparison results)
    TASK_MODEL_MAP = {
        "tutor": "tier1_creative",
        "math": "tier1_quality",
        "coder": "tier2_fast",
        "syllabus_query": "tier2_fast",
        "explain": "tier1_quality",
        "fast": "tier3_cheap",
        "classify": "tier3_cheap",
    }
    
    def __init__(self, comparison_results: Optional[Dict] = None):
        """
        Initialize router with optional comparison results to override defaults.
        """
        if comparison_results:
            self._apply_comparison_results(comparison_results)
    
    def _apply_comparison_results(self, results: Dict) -> None:
        """Update routing based on comparison test results."""
        if "recommendations" in results:
            for intent, model_name in results["recommendations"].items():
                # Find matching tier
                for tier, config in self.MODELS.items():
                    if config["name"] in model_name:
                        self.TASK_MODEL_MAP[intent] = tier
                        break
    
    def select_model(
        self,
        task_type: str,
        priority: str = "balanced",  # "quality", "speed", "cost", "balanced"
        context_length: int = 0,
    ) -> Tuple[str, Dict]:
        """
        Select the optimal model for a given task.
        
        Returns:
            Tuple of (model_name, config_dict)
        """
        # Get default model for task
        default_tier = self.TASK_MODEL_MAP.get(task_type, "tier1_quality")
        
        # Adjust based on priority
        if priority == "quality":
            # Upgrade to tier 1 if not already
            if default_tier.startswith("tier2") or default_tier.startswith("tier3"):
                default_tier = "tier1_quality"
        elif priority == "speed":
            # Use fastest available
            default_tier = "tier2_fast" if task_type != "classify" else "tier3_cheap"
        elif priority == "cost":
            # Use cheapest that can handle the task
            if task_type in ["fast", "syllabus_query", "classify"]:
                default_tier = "tier3_cheap"
            else:
                default_tier = "tier2_fast"
        
        config = self.MODELS[default_tier]
        return config["name"], config
    
    def get_router_prompt(self) -> str:
        """
        Get a routing prompt for LLM-based routing (fallback).
        """
        return """Classify the user's intent into one of these categories:
        
        - tutor: Educational question requiring explanation or scaffolding
        - math: Mathematical derivation or proof needed
        - coder: Code generation, debugging, or implementation
        - syllabus_query: Question about course logistics or topics
        - explain: Simple explanation request (not full teaching)
        - fast: Quick factual answer needed
        
        Respond with ONLY the category name."""
```

---

## Usage

### Running Comparisons

```bash
cd backend

# Run full comparison
python -m tests.model_comparison.run_comparison

# View results
cat test_output/model_comparison/report_*.md
```

### Integrating Results

```python
# In supervisor.py, load comparison results
import json
from pathlib import Path

# Load latest comparison results
results_dir = Path("test_output/model_comparison")
latest_results = sorted(results_dir.glob("results_*.json"))[-1]

with open(latest_results) as f:
    comparison_data = json.load(f)

# Update router with results
router = SmartRouter(comparison_results=comparison_data)
```

---

## Metrics to Track

1. **Quality Score** (0-1): Composite of behavior, format, length compliance
2. **Latency** (ms): Time to first token, total response time
3. **Cost** ($): Estimated based on token usage
4. **Category Performance**: Breakdown by task type
5. **Instruction Following**: How well model follows constraints

---

## Next Steps

1. [ ] Run initial comparison across all models
2. [ ] Analyze results and update routing
3. [ ] Implement SmartRouter in supervisor.py
4. [ ] Add A/B testing for live traffic
5. [ ] Create dashboard for monitoring model performance
