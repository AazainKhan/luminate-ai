"""
Response Evaluator for Model Comparison

Evaluates model responses against test case criteria for quality,
instruction following, and pedagogical effectiveness.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Callable, Union
from .test_cases import TestCase, TestCategory


@dataclass
class EvaluationResult:
    """Result of evaluating a model response."""
    test_id: str
    model_name: str
    
    # Scores (0.0 - 1.0)
    behavior_score: float  # Expected behaviors present
    forbidden_score: float  # Forbidden behaviors absent (1.0 = none present)
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
    
    # Patterns for detecting expected behaviors
    BEHAVIOR_PATTERNS: Dict[str, Union[str, Callable]] = {
        # Pedagogical behaviors
        "asks clarifying question": r"\?[^?]*$|do you|would you|can you tell|what do you",
        "builds on prior knowledge": r"as you (may )?know|remember|recall|previously|building on|you('ve| have) learned",
        "provides analogy or example": r"for example|like|imagine|think of|consider|similar to|picture",
        "concise explanation": lambda text: len(text) < 800,
        "intuitive analogy": r"like|imagine|think of|picture|similar to|just like|think about",
        "offers to elaborate": r"want me to|would you like|shall I|let me know if|happy to explain",
        "explains with examples": r"for example|such as|instance|consider|like when",
        "contrasts the two clearly": r"while|whereas|on the other hand|in contrast|unlike|difference",
        "uses relatable analogy": r"like a|similar to|think of it as|imagine",
        
        # Factual behaviors
        "lists course topics": r"(?:\d+[\.\)]\s*|\*\s*|•\s*|[-]\s*).*(?:\n|$)",
        "one or two sentences": lambda text: text.count('.') <= 3 and len(text) < 300,
        "concise definition": lambda text: len(text) < 300,
        
        # Code behaviors
        "provides working code": r"```(?:python|py)?\n[\s\S]*?```|def \w+\(|class \w+:|import ",
        "includes comments": r"#.*\n|'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"",
        "explains key parts": r"this (?:line|part|section|function)|here we|notice that|the key",
        "identifies the bug": r"bug|error|issue|problem|fix|incorrect|missing|wrong|should be",
        "provides corrected code": r"```(?:python|py)?\n[\s\S]*?```",
        "explains the issue": r"because|the problem|the issue|this happens|the reason",
        "shows code example": r"```(?:python|py)?\n[\s\S]*?```",
        "explains algorithm steps": r"step|first|then|next|finally|1\.|2\.|3\.",
        
        # Math behaviors
        "step-by-step derivation": r"step \d|first,?|then,?|finally,?|next,?|1\.|2\.|3\.",
        "uses math notation": r"\$.*?\$|\\\[.*?\\\]|\\frac|\\sum|\\partial|=|→|×|÷",
        "explains each step": r"this (?:gives|means|shows)|because|therefore|which means",
        "shows the formula": r"[a-zA-Z]\s*=|\\[a-zA-Z]+{|formula|equation",
        "explains component by component": r"where|here,|the .* term|this part",
        
        # Instruction following
        "exactly one sentence": lambda text: text.strip().count('.') == 1 and len(text) < 300,
        "exactly 3 items": lambda text: len(re.findall(r'^\s*(?:\d+[\.\)]|\*|•|-)\s*', text, re.MULTILINE)) == 3,
        "numbered or bulleted": r"^\s*(?:\d+[\.\)]|\*|•|-)\s*",
        "2-3 sentences only": lambda text: 2 <= text.strip().count('.') <= 4,
        "clear definition": r"is a|refers to|means|defined as",
        "concise": lambda text: len(text) < 400,
    }
    
    # Patterns for detecting forbidden behaviors
    FORBIDDEN_PATTERNS: Dict[str, Union[str, Callable]] = {
        "gives complete solution": r"complete solution|full answer|here's everything",
        "uses overwhelming jargon": lambda text: len(re.findall(r'\b[A-Z]{2,}\b', text)) > 10,
        "lecture-style monologue": lambda text: len(text) > 3000 and text.count('?') < 2,
        "full mathematical derivation": lambda text: text.count('$') > 10 or len(re.findall(r'\\frac|\\sum', text)) > 5,
        "lengthy scaffolding": lambda text: len(text) > 1500,
        "socratic questions": r"\?[^?]*\?[^?]*\?",  # Multiple questions
        "asks for clarification": r"could you clarify|what do you mean|can you explain what",
        "refuses to give code": r"I (?:can't|cannot|won't) (?:provide|write|give)",
        "gives pseudocode only": r"pseudocode|pseudo-code",
        "says code looks correct": r"looks correct|is correct|no issues|seems fine",
        "skips steps": lambda text: "therefore" in text.lower() and text.count("step") < 2,
        "gives only final answer": lambda text: len(text) < 200 and 'step' not in text.lower(),
        "multiple sentences": lambda text: text.strip().count('.') > 2,
        "long explanation": lambda text: len(text) > 400,
        "more than 3 items": lambda text: len(re.findall(r'^\s*(?:\d+[\.\)]|\*|•|-)\s*', text, re.MULTILINE)) > 3,
        "fewer than 3 items": lambda text: len(re.findall(r'^\s*(?:\d+[\.\)]|\*|•|-)\s*', text, re.MULTILINE)) < 3 and len(re.findall(r'^\s*(?:\d+[\.\)]|\*|•|-)\s*', text, re.MULTILINE)) > 0,
        "more than 4 sentences": lambda text: text.strip().count('.') > 4,
        "includes examples": r"for example|such as|like|instance",
        "too technical": lambda text: len(re.findall(r'\b[A-Z]{2,}\b', text)) > 5,
        "only defines one": lambda text: "supervised" not in text.lower() or "unsupervised" not in text.lower(),
        "too abstract": lambda text: "example" not in text.lower() and "like" not in text.lower(),
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
            # Penalize being over length
            overage = actual_length - max_len
            length_score = max(0, 1.0 - (overage / max_len))
        
        # Check sources (if required)
        if test_case.requires_sources:
            source_patterns = r'\[.*?source.*?\]|\[from:.*?\]|according to|based on|from the|Source:'
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
            matches = sum(1 for p in structure_patterns if re.search(p, response_text, re.MULTILINE))
            structure_score = min(1.0, matches / 2)  # Need at least 2 structural elements
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
    
    def _check_behavior(
        self,
        behavior: str,
        text: str,
        patterns: Dict[str, Union[str, Callable]]
    ) -> bool:
        """Check if a behavior is present in the text."""
        if behavior not in patterns:
            # Fallback to substring match
            return behavior.lower() in text.lower()
        
        pattern = patterns[behavior]
        
        if callable(pattern):
            try:
                return pattern(text)
            except Exception:
                return False
        else:
            return bool(re.search(pattern, text, re.MULTILINE | re.IGNORECASE))
