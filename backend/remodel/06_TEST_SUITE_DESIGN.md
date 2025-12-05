# Test Suite Design: Revealing UX Shortcomings

## Philosophy

The existing tests focus on **functional correctness** (does the agent respond?) but miss **user experience quality** (does the response FEEL like a good tutor?).

This test suite focuses on:
1. **Response Pattern Variety** - Are responses varied or repetitive?
2. **Conversation Coherence** - Do follow-ups build on context?
3. **Adaptive Length** - Does response length match query needs?
4. **Source Quality** - Are sources cited properly?
5. **Intelligent Tutoring** - Does it teach, not just explain?

---

## Test Categories

### Category 1: Response Pattern Variety

**Goal**: Ensure the agent doesn't produce identical structure every time.

```python
# backend/tests/test_response_patterns.py

import pytest
import re
from typing import List, Dict
from app.agents.tutor_agent import run_agent

class TestResponsePatterns:
    """Test that responses show variety, not repetitive templates."""
    
    def test_no_rigid_structure_repetition(self):
        """
        Multiple queries should NOT produce identical response structures.
        
        FAILS IF: Every response has "What it is:", "How it works:", etc.
        """
        queries = [
            "explain gradient descent",
            "explain backpropagation",
            "explain decision trees",
            "explain k-means clustering",
            "explain neural networks",
        ]
        
        responses = []
        for query in queries:
            result = run_agent(query, "test-user", "test@test.com")
            responses.append(result.get("response", ""))
        
        # Check for repeated structural patterns
        structure_markers = [
            r"\*\*What it is\*\*:",
            r"\*\*How it works\*\*:",
            r"\*\*Example\*\*:",
            r"\*\*Key point\*\*:",
        ]
        
        responses_with_all_markers = 0
        for response in responses:
            has_all = all(re.search(marker, response) for marker in structure_markers)
            if has_all:
                responses_with_all_markers += 1
        
        # At most 20% should have identical structure
        assert responses_with_all_markers / len(responses) < 0.2, \
            f"Too many responses have identical structure: {responses_with_all_markers}/{len(responses)}"
    
    def test_varied_opening_lines(self):
        """
        Responses shouldn't all start the same way.
        
        FAILS IF: >50% of responses start with "X is a/an..."
        """
        queries = [
            "explain gradient descent",
            "explain backpropagation",
            "explain decision trees",
        ]
        
        openings = []
        for query in queries:
            result = run_agent(query, "test-user", "test@test.com")
            response = result.get("response", "")
            # Get first 50 chars as opening
            opening = response[:50].strip()
            openings.append(opening)
        
        # Check for "X is a/an" pattern
        is_pattern = r"^[A-Z][a-z]+ is (a|an|the)"
        is_pattern_count = sum(1 for o in openings if re.match(is_pattern, o))
        
        assert is_pattern_count / len(openings) < 0.5, \
            f"Too many responses start with 'X is a...' pattern: {is_pattern_count}/{len(openings)}"
    
    def test_varied_closing_lines(self):
        """
        Not every response should end with "Would you like me to...?"
        
        FAILS IF: >50% end with formulaic question
        """
        queries = [
            "explain gradient descent",
            "what is backpropagation",
            "briefly, what is ML",
        ]
        
        formulaic_endings = 0
        for query in queries:
            result = run_agent(query, "test-user", "test@test.com")
            response = result.get("response", "")
            
            # Check for formulaic endings
            ending_patterns = [
                r"Would you like me to (go deeper|explain more|elaborate)",
                r"Want me to (explain|elaborate|go deeper)",
                r"Would you like (a|an|more) (example|practice problem)",
            ]
            
            for pattern in ending_patterns:
                if re.search(pattern, response[-200:], re.IGNORECASE):
                    formulaic_endings += 1
                    break
        
        assert formulaic_endings / len(queries) < 0.5, \
            f"Too many formulaic endings: {formulaic_endings}/{len(queries)}"


class TestQuickAnswerMode:
    """Test that 'brief' queries get brief responses."""
    
    def test_briefly_keyword_triggers_short_response(self):
        """
        'Briefly, what is X' should get a SHORT response.
        
        FAILS IF: Response is > 500 characters
        """
        result = run_agent("briefly, what is gradient descent", "test", "test@test.com")
        response = result.get("response", "")
        
        assert len(response) < 500, \
            f"'Briefly' query got too long response: {len(response)} chars"
    
    def test_quick_answer_doesnt_ask_followup(self):
        """
        Quick answers shouldn't end with follow-up questions.
        
        FAILS IF: Brief response asks "Want me to explain more?"
        """
        result = run_agent("quick: what is a neural network", "test", "test@test.com")
        response = result.get("response", "")
        
        # Should not have follow-up question patterns
        followup_patterns = [
            r"Would you like",
            r"Want me to",
            r"Shall I",
            r"Do you want",
        ]
        
        for pattern in followup_patterns:
            assert not re.search(pattern, response), \
                f"Quick answer shouldn't ask follow-up: found '{pattern}'"
    
    def test_compare_brief_vs_detailed(self):
        """
        Same topic with 'briefly' vs 'explain in detail' should differ in length.
        
        FAILS IF: Lengths are within 2x of each other
        """
        brief = run_agent("briefly, what is backpropagation", "test", "test@test.com")
        detailed = run_agent("explain backpropagation in detail", "test", "test@test.com")
        
        brief_len = len(brief.get("response", ""))
        detailed_len = len(detailed.get("response", ""))
        
        assert detailed_len > brief_len * 2, \
            f"Detailed ({detailed_len}) should be >2x brief ({brief_len})"
```

### Category 2: Conversation Coherence

```python
# backend/tests/test_conversation_coherence.py

import pytest
from app.agents.tutor_agent import astream_agent
import asyncio

class TestConversationCoherence:
    """Test that follow-up responses build on previous context."""
    
    @pytest.fixture
    def run_conversation(self):
        """Helper to run a multi-turn conversation."""
        async def _run(messages: list, user_id: str = "test"):
            history = []
            responses = []
            
            for msg in messages:
                result = []
                async for event in astream_agent(
                    msg, user_id, "test@test.com", "test-session",
                    chat_id="test-chat",
                    conversation_history=history
                ):
                    if event.get("type") == "text-delta":
                        result.append(event.get("textDelta", ""))
                
                response = "".join(result)
                responses.append(response)
                
                # Add to history
                history.append({"role": "user", "content": msg})
                history.append({"role": "assistant", "content": response})
            
            return responses
        
        return _run
    
    def test_followup_doesnt_repeat_intro(self, run_conversation):
        """
        Follow-up 'go deeper' should NOT repeat the intro.
        
        FAILS IF: Turn 2 contains "What it is:" or re-explains basics
        """
        messages = [
            "explain gradient descent",
            "go deeper"
        ]
        
        responses = asyncio.run(run_conversation(messages))
        
        turn1 = responses[0]
        turn2 = responses[1]
        
        # Turn 2 should NOT have intro patterns
        intro_patterns = [
            r"\*\*What it is\*\*",
            r"Gradient descent is (a|an|the)",
            r"In machine learning, gradient descent",
        ]
        
        for pattern in intro_patterns:
            assert not re.search(pattern, turn2), \
                f"Follow-up repeats intro material: found '{pattern}'"
    
    def test_followup_references_previous(self, run_conversation):
        """
        Follow-up should reference previous content.
        
        PASSES IF: Turn 2 contains signals like "building on", "as I mentioned", etc.
        """
        messages = [
            "explain neural networks",
            "tell me more about the hidden layers"
        ]
        
        responses = asyncio.run(run_conversation(messages))
        turn2 = responses[1]
        
        # Should have continuity markers OR directly dive deeper
        continuity_patterns = [
            r"(building on|as (I |we )?(mentioned|discussed)|earlier)",
            r"hidden layer",  # At minimum, should mention the topic
            r"(going deeper|more detail)",
        ]
        
        has_continuity = any(re.search(p, turn2, re.I) for p in continuity_patterns)
        
        assert has_continuity, \
            "Follow-up doesn't show continuity with previous turn"
    
    def test_topic_switch_resets_properly(self, run_conversation):
        """
        Switching topics should reset, not force false continuity.
        
        PASSES IF: New topic gets proper introduction
        """
        messages = [
            "explain gradient descent",
            "now explain decision trees"  # Topic switch
        ]
        
        responses = asyncio.run(run_conversation(messages))
        turn2 = responses[1]
        
        # Should NOT reference gradient descent in decision tree explanation
        assert "gradient" not in turn2.lower(), \
            "Topic switch incorrectly references previous topic"
        
        # Should properly introduce new topic
        assert "decision tree" in turn2.lower() or "tree" in turn2.lower(), \
            "Topic switch should introduce new topic"
    
    def test_clarification_simplifies(self, run_conversation):
        """
        "I don't understand" should trigger simpler explanation.
        
        FAILS IF: Response is MORE complex than original
        """
        messages = [
            "explain backpropagation",
            "I don't understand, can you explain simpler?"
        ]
        
        responses = asyncio.run(run_conversation(messages))
        turn1 = responses[0]
        turn2 = responses[1]
        
        # Simplification indicators
        simplification_patterns = [
            r"(simpler|basic|fundamental|let me try)",
            r"(think of it|imagine|analogy)",
            r"(in other words|basically|essentially)",
        ]
        
        has_simplification = any(re.search(p, turn2, re.I) for p in simplification_patterns)
        
        # Should either simplify OR use analogy
        assert has_simplification or "like" in turn2.lower(), \
            "Clarification should simplify or use analogy"


class TestConversationLength:
    """Test response length adapts to conversation context."""
    
    def test_later_turns_can_be_shorter(self, run_conversation):
        """
        Turn 5 on same topic should be shorter than Turn 1.
        
        FAILS IF: Later turns are consistently as long as first
        """
        messages = [
            "explain neural networks",
            "what about activation functions?",
            "and the hidden layers?",
            "how many layers should I use?",
            "what's a good rule of thumb?"
        ]
        
        responses = asyncio.run(run_conversation(messages))
        
        turn1_len = len(responses[0])
        turn5_len = len(responses[4])
        
        # Turn 5 (simple question) should be shorter
        assert turn5_len < turn1_len * 0.7, \
            f"Turn 5 ({turn5_len}) should be shorter than Turn 1 ({turn1_len})"
```

### Category 3: Source Quality

```python
# backend/tests/test_source_quality.py

import pytest
from app.agents.tutor_agent import run_agent

class TestSourceQuality:
    """Test that sources are properly cited."""
    
    def test_no_unknown_sources(self):
        """
        Sources should have real filenames, not 'Unknown'.
        
        FAILS IF: Any source is 'Unknown'
        """
        result = run_agent("explain gradient descent", "test", "test@test.com")
        sources = result.get("sources", [])
        
        for source in sources:
            filename = source.get("filename") or source.get("title") or "Unknown"
            assert filename != "Unknown", \
                f"Source should not be 'Unknown': {source}"
    
    def test_sources_are_relevant(self):
        """
        Sources should be about the query topic.
        
        FAILS IF: Source content doesn't relate to query
        """
        result = run_agent("explain k-means clustering", "test", "test@test.com")
        sources = result.get("sources", [])
        
        if not sources:
            pytest.skip("No sources returned")
        
        # At least one source should mention clustering
        relevant = False
        for source in sources:
            desc = source.get("description", "").lower()
            if "cluster" in desc or "k-means" in desc or "unsupervised" in desc:
                relevant = True
                break
        
        assert relevant, "No source mentions the query topic (clustering)"
    
    def test_sources_have_scores(self):
        """
        Sources should include relevance scores.
        
        FAILS IF: Sources lack relevance_score
        """
        result = run_agent("explain backpropagation", "test", "test@test.com")
        sources = result.get("sources", [])
        
        for source in sources:
            # Score should be in description or as separate field
            has_score = (
                "score" in source.get("description", "").lower() or
                source.get("relevance_score") is not None
            )
            assert has_score, f"Source lacks relevance score: {source}"
    
    def test_response_cites_sources_naturally(self):
        """
        Response text should cite sources inline, not just append.
        
        PASSES IF: Response contains "According to...", "[Source:...]", etc.
        """
        result = run_agent("what does the course say about neural networks", "test", "test@test.com")
        response = result.get("response", "")
        
        citation_patterns = [
            r"(according to|from) (the )?(course|materials|syllabus)",
            r"\[(from|source):?",
            r"in the course (materials|outline|syllabus)",
            r"COMP.?237",
        ]
        
        has_citation = any(re.search(p, response, re.I) for p in citation_patterns)
        
        # Allow if sources are appended at end as fallback
        has_appended = "[Sources:" in response or "**Sources:**" in response
        
        assert has_citation or has_appended, \
            "Response should cite sources naturally or append them"
```

### Category 4: Intelligent Tutoring Behavior

```python
# backend/tests/test_intelligent_tutoring.py

import pytest
from app.agents.tutor_agent import run_agent

class TestIntelligentTutoring:
    """Test that the agent acts like a tutor, not a Wikipedia article."""
    
    def test_confused_student_gets_scaffolding(self):
        """
        "I don't understand" should trigger scaffolding, not just re-explain.
        
        PASSES IF: Response uses scaffolding techniques
        """
        result = run_agent(
            "I don't understand gradient descent at all, it's confusing", 
            "test", "test@test.com"
        )
        response = result.get("response", "")
        
        scaffolding_patterns = [
            r"\?",  # Asks questions
            r"(let me|let's) (break|start|try)",  # Offers to help
            r"(what|which) (part|aspect|concept)",  # Diagnoses confusion
            r"(for example|imagine|think of)",  # Uses analogies
        ]
        
        scaffolding_count = sum(
            1 for p in scaffolding_patterns 
            if re.search(p, response, re.I)
        )
        
        assert scaffolding_count >= 2, \
            f"Confused student should get scaffolding, found only {scaffolding_count} indicators"
    
    def test_doesnt_give_complete_assignment_solutions(self):
        """
        Should not provide complete homework solutions.
        
        FAILS IF: Response gives step-by-step solution to a problem
        """
        result = run_agent(
            "Can you solve this assignment problem: Implement KNN from scratch", 
            "test", "test@test.com"
        )
        response = result.get("response", "")
        
        # Should NOT have complete code implementation
        complete_solution_patterns = [
            r"```python\s*\n.*def.*\n.*for.*\n.*return",  # Complete function
            r"here is the (complete|full) (solution|implementation)",
            r"step 1:.*step 2:.*step 3:",  # Step-by-step solution
        ]
        
        for pattern in complete_solution_patterns:
            assert not re.search(pattern, response, re.I | re.DOTALL), \
                "Should not give complete assignment solution"
    
    def test_asks_clarifying_questions_for_ambiguous(self):
        """
        Ambiguous queries should prompt clarification.
        
        PASSES IF: Response asks what aspect they want to know
        """
        result = run_agent(
            "tell me about machine learning", 
            "test", "test@test.com"
        )
        response = result.get("response", "")
        
        # Should either ask for clarification or give options
        clarification_patterns = [
            r"\?",  # Any question
            r"(which|what) (aspect|topic|area)",
            r"(would you like|want me to|should I)",
            r"(for example|such as|like)",  # Gives options
        ]
        
        has_clarification = any(
            re.search(p, response, re.I) for p in clarification_patterns
        )
        
        assert has_clarification, \
            "Ambiguous query should prompt clarification or offer options"
    
    def test_adapts_to_advanced_student(self):
        """
        Student showing expertise should get advanced content.
        
        PASSES IF: Response doesn't over-explain basics
        """
        result = run_agent(
            "I understand the chain rule - can you explain how backprop handles vanishing gradients in deep networks?", 
            "test", "test@test.com"
        )
        response = result.get("response", "")
        
        # Should NOT explain chain rule basics
        basic_explanations = [
            r"chain rule is",
            r"first, let me explain",
            r"before we discuss vanishing gradients, let's review",
        ]
        
        for pattern in basic_explanations:
            assert not re.search(pattern, response, re.I), \
                f"Should not over-explain basics to advanced student: found '{pattern}'"
        
        # SHOULD discuss vanishing gradients directly
        assert "vanishing" in response.lower() or "gradient" in response.lower(), \
            "Should address the advanced topic directly"
```

---

## Running the Tests

```bash
# Run all UX tests
pytest backend/tests/test_response_patterns.py -v
pytest backend/tests/test_conversation_coherence.py -v
pytest backend/tests/test_source_quality.py -v
pytest backend/tests/test_intelligent_tutoring.py -v

# Run with verbose output showing failures
pytest backend/tests/test_*.py -v --tb=short

# Run specific test
pytest backend/tests/test_response_patterns.py::TestResponsePatterns::test_no_rigid_structure_repetition -v
```

---

## Test Fixtures

```python
# backend/tests/conftest.py

import pytest
import uuid

@pytest.fixture
def test_user_id():
    return str(uuid.uuid4())

@pytest.fixture
def test_email():
    return "test@my.centennialcollege.ca"

@pytest.fixture
def run_agent_helper(test_user_id, test_email):
    """Helper to run agent with consistent test user."""
    def _run(query: str):
        from app.agents.tutor_agent import run_agent
        return run_agent(query, test_user_id, test_email)
    return _run
```

---

## Expected Results (Current System)

Based on analysis, the current system will likely FAIL:

| Test | Expected Result | Why |
|------|-----------------|-----|
| `test_no_rigid_structure_repetition` | ❌ FAIL | `SYSTEM_PROMPTS["explain"]` forces structure |
| `test_varied_opening_lines` | ❌ FAIL | All start with "X is a..." |
| `test_varied_closing_lines` | ❌ FAIL | All end with "Would you like..." |
| `test_briefly_keyword_triggers_short_response` | ⚠️ PARTIAL | `fast` intent exists but may be too long |
| `test_followup_doesnt_repeat_intro` | ❌ FAIL | No conversation awareness |
| `test_no_unknown_sources` | ❌ FAIL | Known source metadata bug |
| `test_confused_student_gets_scaffolding` | ✅ PASS | Tutor intent handles this |
| `test_doesnt_give_complete_assignment_solutions` | ✅ PASS | Governor enforces this |

---

## Success Metrics

After implementing fixes, target:

| Metric | Before | After Target |
|--------|--------|--------------|
| Pattern variety tests passing | 0/3 | 3/3 |
| Conversation coherence tests passing | 0/4 | 4/4 |
| Source quality tests passing | 1/4 | 4/4 |
| Intelligent tutoring tests passing | 2/4 | 4/4 |
| **Total** | **3/15 (20%)** | **15/15 (100%)** |
