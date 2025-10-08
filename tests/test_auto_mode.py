"""
High-Level E2E Tests for Auto Mode
Tests orchestrator classification, routing accuracy, and conversation continuity.
"""

import sys
from pathlib import Path
import pytest
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir / "langgraph"))

from orchestrator import classify_mode, OrchestratorState


class TestOrchestratorClassification:
    """Test orchestrator mode classification accuracy."""
    
    # Test cases: (query, expected_mode, min_confidence)
    NAVIGATE_QUERIES = [
        ("Find me videos about neural networks", "navigate", 0.75),
        ("Show me materials for Week 5", "navigate", 0.85),
        ("Search for gradient descent slides", "navigate", 0.85),
        ("What is the definition of reinforcement learning?", "navigate", 0.75),
        ("Get me resources about transformers", "navigate", 0.75),
        ("Look up backpropagation materials", "navigate", 0.85),
        ("Find external resources for computer vision", "navigate", 0.85),
    ]
    
    EDUCATE_QUERIES = [
        ("Explain how gradient descent works step by step", "educate", 0.85),
        ("I don't understand the backpropagation formula", "educate", 0.90),
        ("Help me understand A* search algorithm", "educate", 0.90),
        ("Walk me through DFS implementation", "educate", 0.90),
        ("Quiz me on Week 6 machine learning topics", "educate", 0.65),
        ("How does the naive bayes classifier work?", "educate", 0.85),
        ("Can you teach me about neural networks?", "educate", 0.85),
        ("I'm confused about the difference between precision and recall", "educate", 0.90),
        ("Solve this A* problem for me", "educate", 0.75),
        ("Explain the math behind linear regression", "educate", 0.90),
    ]
    
    @pytest.mark.parametrize("query,expected_mode,min_confidence", NAVIGATE_QUERIES)
    def test_navigate_classification(self, query, expected_mode, min_confidence):
        """Test classification of Navigate mode queries."""
        state = OrchestratorState(
            query=query,
            student_id="test-student",
            session_id="test-session",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        assert result['mode'] == expected_mode, \
            f"Expected {expected_mode} but got {result['mode']} for query: {query}"
        assert result['confidence'] >= min_confidence, \
            f"Confidence {result['confidence']:.2f} below minimum {min_confidence} for: {query}"
    
    @pytest.mark.parametrize("query,expected_mode,min_confidence", EDUCATE_QUERIES)
    def test_educate_classification(self, query, expected_mode, min_confidence):
        """Test classification of Educate mode queries."""
        state = OrchestratorState(
            query=query,
            student_id="test-student",
            session_id="test-session",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        assert result['mode'] == expected_mode, \
            f"Expected {expected_mode} but got {result['mode']} for query: {query}"
        assert result['confidence'] >= min_confidence, \
            f"Confidence {result['confidence']:.2f} below minimum {min_confidence} for: {query}"


class TestConversationContinuity:
    """Test follow-up detection and mode consistency."""
    
    def test_follow_up_detection_simple(self):
        """Test basic follow-up patterns."""
        # Initial query in educate mode
        initial_query = "Explain how gradient descent works"
        conv_history = [
            {
                "role": "user",
                "content": initial_query,
                "mode": "educate",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Gradient descent is an optimization algorithm...",
                "mode": "educate",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Follow-up query
        follow_up_query = "Can you explain that with an example?"
        
        state = OrchestratorState(
            query=follow_up_query,
            student_id="test-student",
            session_id="test-session",
            conversation_history=conv_history,
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="educate",
            mode_switch_count=0,
            conversation_turns=2,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        # Should stay in educate mode for follow-up
        assert result['mode'] == 'educate', \
            f"Follow-up should stay in educate mode, got {result['mode']}"
        assert result['is_follow_up'] == True, \
            "Should be detected as follow-up"
    
    def test_follow_up_with_strong_override(self):
        """Test that strong signals override follow-up stickiness."""
        conv_history = [
            {
                "role": "user",
                "content": "Explain gradient descent",
                "mode": "educate",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Strong navigate signal should override
        override_query = "Find me videos and materials about this"
        
        state = OrchestratorState(
            query=override_query,
            student_id="test-student",
            session_id="test-session",
            conversation_history=conv_history,
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="educate",
            mode_switch_count=0,
            conversation_turns=1,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        # Strong navigate signal should switch mode
        assert result['mode'] == 'navigate', \
            f"Strong signal should override follow-up, got {result['mode']}"
    
    def test_pronoun_reference(self):
        """Test follow-up detection with pronoun references."""
        conv_history = [
            {
                "role": "user",
                "content": "Explain neural networks",
                "mode": "educate",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Pronoun reference indicates follow-up
        follow_up = "Tell me more about them"
        
        state = OrchestratorState(
            query=follow_up,
            student_id="test-student",
            session_id="test-session",
            conversation_history=conv_history,
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="educate",
            mode_switch_count=0,
            conversation_turns=1,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        assert result['is_follow_up'] == True, \
            "Pronoun reference should indicate follow-up"
        assert result['mode'] == 'educate', \
            "Should stay in educate mode"


class TestConfidenceThreshold:
    """Test confidence threshold and confirmation logic."""
    
    def test_low_confidence_flag(self):
        """Test that low confidence queries are flagged for confirmation."""
        ambiguous_query = "kmeans"  # Single word, ambiguous
        
        state = OrchestratorState(
            query=ambiguous_query,
            student_id="test-student",
            session_id="test-session",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        # Should have low confidence or be flagged for confirmation
        if result['confidence'] < 0.7:
            assert result['should_confirm'] == True, \
                "Low confidence should trigger confirmation flag"
    
    def test_high_confidence_no_confirmation(self):
        """Test that high confidence queries don't need confirmation."""
        clear_query = "Explain how backpropagation works step by step"
        
        state = OrchestratorState(
            query=clear_query,
            student_id="test-student",
            session_id="test-session",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        assert result['confidence'] >= 0.7, \
            f"Clear educate query should have high confidence, got {result['confidence']:.2f}"
        assert result['should_confirm'] == False, \
            "High confidence should not trigger confirmation"


class TestModeSwitching:
    """Test mode switching patterns and analytics."""
    
    def test_mode_switch_count(self):
        """Test that mode switches are tracked correctly."""
        # Conversation with multiple mode switches
        conv_history = [
            {"role": "user", "content": "Find materials", "mode": "navigate", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "...", "mode": "navigate", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "Explain this", "mode": "educate", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "...", "mode": "educate", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "Find more", "mode": "navigate", "timestamp": datetime.now().isoformat()},
        ]
        
        state = OrchestratorState(
            query="What about gradient descent?",
            student_id="test-student",
            session_id="test-session",
            conversation_history=conv_history,
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="navigate",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        # Should count 2 mode switches (navigate->educate and educate->navigate)
        assert result['mode_switch_count'] == 2, \
            f"Expected 2 mode switches, got {result['mode_switch_count']}"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_conversation_history(self):
        """Test handling of empty conversation history."""
        state = OrchestratorState(
            query="Explain A* search",
            student_id="test-student",
            session_id="test-session",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        assert result['is_follow_up'] == False, \
            "Empty history should not trigger follow-up detection"
        assert result['mode'] in ['navigate', 'educate'], \
            "Should classify to valid mode"
    
    def test_very_short_query(self):
        """Test handling of very short queries."""
        short_query = "BFS"
        
        state = OrchestratorState(
            query=short_query,
            student_id="test-student",
            session_id="test-session",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        # Should still classify (may be low confidence)
        assert result['mode'] in ['navigate', 'educate'], \
            "Short query should still be classified"
        assert 'reasoning' in result and result['reasoning'], \
            "Should provide reasoning even for short queries"


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test that classification is fast enough for real-time use."""
    
    def test_classification_latency(self):
        """Test that classification completes in < 2 seconds."""
        import time
        
        queries = [
            "Explain gradient descent",
            "Find materials about neural networks",
            "How does A* search work?",
            "Search for backpropagation videos"
        ]
        
        total_time = 0
        for query in queries:
            state = OrchestratorState(
                query=query,
                student_id="test-student",
                session_id="test-session",
                conversation_history=[],
                mode="navigate",
                confidence=0.0,
                reasoning="",
                next_graph="navigate_graph",
                student_context={},
                last_mode="",
                mode_switch_count=0,
                conversation_turns=0,
                is_follow_up=False,
                should_confirm=False
            )
            
            start = time.time()
            classify_mode(state)
            elapsed = time.time() - start
            total_time += elapsed
            
            assert elapsed < 2.0, \
                f"Classification took {elapsed:.2f}s, should be < 2s"
        
        avg_time = total_time / len(queries)
        print(f"\n✓ Average classification time: {avg_time:.3f}s")


# ============================================================================
# Summary Report
# ============================================================================

def test_generate_accuracy_report():
    """Generate an accuracy report for all test queries."""
    from orchestrator import classify_mode, OrchestratorState
    
    all_queries = (
        TestOrchestratorClassification.NAVIGATE_QUERIES +
        TestOrchestratorClassification.EDUCATE_QUERIES
    )
    
    correct = 0
    total = len(all_queries)
    low_confidence = 0
    
    for query, expected_mode, _ in all_queries:
        state = OrchestratorState(
            query=query,
            student_id="test-student",
            session_id="test-session",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(state)
        
        if result['mode'] == expected_mode:
            correct += 1
        
        if result['confidence'] < 0.7:
            low_confidence += 1
    
    accuracy = (correct / total) * 100
    
    print(f"\n{'='*60}")
    print("AUTO MODE CLASSIFICATION ACCURACY REPORT")
    print(f"{'='*60}")
    print(f"Total queries tested: {total}")
    print(f"Correct classifications: {correct}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"Low confidence predictions: {low_confidence} ({(low_confidence/total)*100:.1f}%)")
    print(f"{'='*60}\n")
    
    # Assert minimum accuracy threshold
    assert accuracy >= 85.0, \
        f"Classification accuracy {accuracy:.1f}% below 85% threshold"


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])

