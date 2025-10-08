"""
High-level tests for Student Model Agent

Tests verify:
1. Bayesian mastery estimation and updates
2. Forgetting curve application
3. Misconception detection from answer patterns
4. Prerequisite gap identification
5. Review scheduling (spaced repetition)
6. Next topic recommendations
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langgraph.agents.student_model import StudentModel, student_model_agent


class TestStudentModelBasics:
    """Test basic student model initialization and mastery estimation"""
    
    def test_initialization_empty(self):
        """Test creating a new student with no history"""
        model = StudentModel()
        
        assert model.student_id == 'anonymous'
        assert model.mastery_map == {}
        assert model.struggling_topics == []
        assert model.misconceptions == {}
        assert model.interaction_history == []
        
    def test_initialization_with_context(self):
        """Test loading existing student context"""
        context = {
            'student_id': 'student_123',
            'mastery_map': {'dfs': 0.7, 'neural networks': 0.3},
            'struggling_topics': ['neural networks'],
            'misconceptions': {'neural networks': ['activation_confusion']}
        }
        
        model = StudentModel(context)
        
        assert model.student_id == 'student_123'
        assert model.mastery_map['dfs'] == 0.7
        assert 'neural networks' in model.struggling_topics
        assert 'activation_confusion' in model.misconceptions['neural networks']
    
    def test_estimate_mastery_new_topic(self):
        """Test mastery estimation for never-seen topic (prior belief)"""
        model = StudentModel()
        
        mastery = model.estimate_mastery('quantum computing')
        
        # Should return low prior (0.2) for unknown topic
        assert mastery == 0.2
        
    def test_estimate_mastery_known_topic(self):
        """Test mastery estimation for previously learned topic"""
        model = StudentModel()
        model.mastery_map['dfs'] = 0.8
        
        mastery = model.estimate_mastery('dfs')
        
        # With no time decay, should return stored mastery
        assert mastery == 0.8


class TestMasteryUpdates:
    """Test Bayesian mastery updates based on performance"""
    
    def test_correct_answer_increases_mastery(self):
        """Correct answer with high confidence should increase mastery"""
        model = StudentModel()
        model.mastery_map['dfs'] = 0.5
        
        # Correct answer, high confidence, no hints
        model.update_mastery('dfs', {
            'correct': True,
            'confidence': 0.9,
            'time_taken': 30,
            'hint_level_used': 0
        })
        
        new_mastery = model.estimate_mastery('dfs')
        
        # Mastery should increase
        assert new_mastery > 0.5
        assert new_mastery <= 1.0
        
    def test_incorrect_answer_decreases_mastery(self):
        """Incorrect answer should decrease mastery"""
        model = StudentModel()
        model.mastery_map['dfs'] = 0.7
        
        # Incorrect answer, low confidence
        model.update_mastery('dfs', {
            'correct': False,
            'confidence': 0.3,
            'time_taken': 120,
            'hint_level_used': 2
        })
        
        new_mastery = model.estimate_mastery('dfs')
        
        # Mastery should decrease
        assert new_mastery < 0.7
        assert new_mastery >= 0.0
        
    def test_hints_reduce_mastery_gain(self):
        """Using hints should reduce mastery increase even if correct"""
        model = StudentModel()
        model.mastery_map['neural networks'] = 0.3
        
        # Correct with hint level 3 (full answer)
        model.update_mastery('neural networks', {
            'correct': True,
            'confidence': 0.6,
            'time_taken': 180,
            'hint_level_used': 3
        })
        
        mastery_with_hints = model.estimate_mastery('neural networks')
        
        # Reset and try without hints
        model.mastery_map['neural networks'] = 0.3
        model.update_mastery('neural networks', {
            'correct': True,
            'confidence': 0.6,
            'time_taken': 60,
            'hint_level_used': 0
        })
        
        mastery_without_hints = model.estimate_mastery('neural networks')
        
        # No hints should result in greater mastery increase
        assert mastery_without_hints > mastery_with_hints
        
    def test_struggling_topics_tracking(self):
        """Topics with low mastery should be marked as struggling"""
        model = StudentModel()
        
        # First failure drops mastery below threshold
        model.update_mastery('backpropagation', {
            'correct': False,
            'confidence': 0.2,
            'time_taken': 200,
            'hint_level_used': 3
        })
        
        # Second failure should add to struggling topics
        model.update_mastery('backpropagation', {
            'correct': False,
            'confidence': 0.3,
            'time_taken': 150,
            'hint_level_used': 2
        })
        
        assert 'backpropagation' in model.struggling_topics
        assert model.estimate_mastery('backpropagation') < 0.3


class TestForgettingCurve:
    """Test Ebbinghaus forgetting curve application"""
    
    def test_mastery_degrades_over_time(self):
        """Mastery should decrease over time without review"""
        model = StudentModel()
        model.mastery_map['dfs'] = 0.8
        
        # Add old interaction (14 days ago)
        old_date = (datetime.now() - timedelta(days=14)).isoformat()
        model.interaction_history.append({
            'topic': 'dfs',
            'timestamp': old_date,
            'mastery_before': 0.7,
            'mastery_after': 0.8,
            'performance': {'correct': True}
        })
        
        current_mastery = model.estimate_mastery('dfs')
        
        # Mastery should have decayed from 0.8
        assert current_mastery < 0.8
        assert current_mastery > 0.4  # Not completely forgotten
        
    def test_recent_interaction_no_decay(self):
        """Recent interactions should have minimal decay"""
        model = StudentModel()
        model.mastery_map['dfs'] = 0.8
        
        # Add recent interaction (1 day ago)
        recent_date = (datetime.now() - timedelta(days=1)).isoformat()
        model.interaction_history.append({
            'topic': 'dfs',
            'timestamp': recent_date,
            'mastery_before': 0.7,
            'mastery_after': 0.8,
            'performance': {'correct': True}
        })
        
        current_mastery = model.estimate_mastery('dfs')
        
        # Mastery should be close to original
        assert current_mastery >= 0.75  # Minimal decay


class TestMisconceptionDetection:
    """Test detection of specific misconceptions from answer patterns"""
    
    def test_detect_dfs_bfs_confusion(self):
        """Should detect when student confuses DFS and BFS"""
        model = StudentModel()
        
        student_answer = "DFS explores using breadth-first approach"
        correct_answer = "DFS uses depth-first approach"
        
        misconception = model.detect_misconception('dfs', student_answer, correct_answer)
        
        assert misconception == 'search_algorithm_confusion'
        assert 'dfs' in model.misconceptions
        assert 'search_algorithm_confusion' in model.misconceptions['dfs']
        
    def test_detect_supervised_unsupervised_confusion(self):
        """Should detect when student confuses supervised and unsupervised learning"""
        model = StudentModel()
        
        student_answer = "Supervised learning works with no labels"
        correct_answer = "Supervised learning requires labeled data"
        
        misconception = model.detect_misconception(
            'supervised learning',
            student_answer,
            correct_answer
        )
        
        assert misconception == 'ml_paradigm_confusion'
        
    def test_no_misconception_on_correct(self):
        """Should return None for correct answers"""
        model = StudentModel()
        
        student_answer = "DFS explores depth-first"
        correct_answer = "DFS explores depth-first"
        
        misconception = model.detect_misconception('dfs', student_answer, correct_answer)
        
        assert misconception is None


class TestPrerequisiteAnalysis:
    """Test prerequisite gap detection"""
    
    def test_identify_prerequisite_gaps(self):
        """Should identify unmastered prerequisites"""
        model = StudentModel()
        model.mastery_map['neural networks'] = 0.3  # Low mastery
        model.mastery_map['linear algebra'] = 0.8   # High mastery
        
        topic_graph = {
            'backpropagation': ['neural networks', 'calculus', 'linear algebra'],
            'neural networks': ['linear algebra']
        }
        
        gaps = model.get_prerequisite_gaps('backpropagation', topic_graph)
        
        # Should identify neural networks and calculus as gaps
        assert 'neural networks' in gaps  # Low mastery
        assert 'calculus' in gaps  # Never studied (mastery < 0.5)
        assert 'linear algebra' not in gaps  # High mastery
        
    def test_no_gaps_when_prerequisites_met(self):
        """Should return empty list when all prerequisites mastered"""
        model = StudentModel()
        model.mastery_map['dfs'] = 0.8
        model.mastery_map['bfs'] = 0.7
        
        topic_graph = {
            'a*': ['dfs', 'bfs']
        }
        
        gaps = model.get_prerequisite_gaps('a*', topic_graph)
        
        assert gaps == []


class TestReviewScheduling:
    """Test spaced repetition review scheduling"""
    
    def test_schedule_review_based_on_mastery(self):
        """Review intervals should be based on mastery level"""
        model = StudentModel()
        
        # Low mastery → short interval (1 day)
        model.update_mastery('topic_a', {
            'correct': False,
            'confidence': 0.3,
            'time_taken': 100,
            'hint_level_used': 2
        })
        
        assert 'topic_a' in model.review_schedule
        review_date_a = datetime.fromisoformat(model.review_schedule['topic_a'])
        days_until_review_a = (review_date_a - datetime.now()).days
        assert days_until_review_a <= 1
        
        # High mastery → long interval (14 days)
        model.mastery_map['topic_b'] = 0.9
        model.update_mastery('topic_b', {
            'correct': True,
            'confidence': 0.95,
            'time_taken': 30,
            'hint_level_used': 0
        })
        
        review_date_b = datetime.fromisoformat(model.review_schedule['topic_b'])
        days_until_review_b = (review_date_b - datetime.now()).days
        assert days_until_review_b >= 10
        
    def test_should_review_detection(self):
        """Should detect when topic is due for review"""
        model = StudentModel()
        
        # Schedule review for yesterday
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        model.review_schedule['dfs'] = past_date
        
        assert model.should_review('dfs') == True
        
        # Schedule review for tomorrow
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        model.review_schedule['bfs'] = future_date
        
        assert model.should_review('bfs') == False


class TestNextTopicSuggestions:
    """Test intelligent next topic recommendations"""
    
    def test_suggest_review_topics_first(self):
        """Topics due for review should have highest priority"""
        model = StudentModel()
        
        # Set up topics with different states
        model.mastery_map['dfs'] = 0.6
        model.review_schedule['dfs'] = (datetime.now() - timedelta(days=1)).isoformat()
        
        model.mastery_map['bfs'] = 0.7
        model.struggling_topics = ['neural networks']
        
        topic_graph = {
            'dfs': [],
            'bfs': [],
            'neural networks': [],
            'a*': ['dfs', 'bfs']
        }
        
        suggestions = model.suggest_next_topics(topic_graph, n=3)
        
        # Review should be priority 1
        assert suggestions[0]['type'] == 'review'
        assert suggestions[0]['topic'] == 'dfs'
        
    def test_suggest_struggling_topics_second(self):
        """Struggling topics should be priority 2"""
        model = StudentModel()
        model.struggling_topics = ['neural networks']
        model.mastery_map['neural networks'] = 0.2
        
        topic_graph = {
            'neural networks': [],
            'backpropagation': ['neural networks']
        }
        
        suggestions = model.suggest_next_topics(topic_graph, n=2)
        
        # Find struggling topic suggestion
        struggling_suggestions = [s for s in suggestions if s['type'] == 'remediation']
        assert len(struggling_suggestions) > 0
        assert 'neural networks' in struggling_suggestions[0]['topic']
        
    def test_suggest_new_topics_with_prerequisites_met(self):
        """New topics should only be suggested when prerequisites are met"""
        model = StudentModel()
        model.mastery_map['dfs'] = 0.8
        model.mastery_map['bfs'] = 0.7
        
        topic_graph = {
            'dfs': [],
            'bfs': [],
            'a*': ['dfs', 'bfs'],
            'backpropagation': ['neural networks']  # Prerequisite not met
        }
        
        suggestions = model.suggest_next_topics(topic_graph, n=5)
        
        # a* should be suggested (prerequisites met)
        new_topic_names = [s['topic'] for s in suggestions if s['type'] == 'new']
        assert 'a*' in new_topic_names
        
        # backpropagation should NOT be suggested (prerequisite not met)
        assert 'backpropagation' not in new_topic_names


class TestStudentModelAgent:
    """Test the LangGraph agent wrapper"""
    
    def test_agent_updates_state_with_insights(self):
        """Agent should add student insights to state"""
        state = {
            'query': 'explain dfs algorithm',
            'student_context': {
                'mastery_map': {'dfs': 0.5}
            }
        }
        
        result = student_model_agent(state)
        
        assert 'student_insights' in result
        assert result['student_insights']['topic'] == 'dfs'
        assert 'current_mastery' in result['student_insights']
        assert 'recommended_difficulty' in result['student_insights']
        
    def test_agent_processes_student_response(self):
        """Agent should update mastery when student answers"""
        state = {
            'query': 'quiz on neural networks',
            'student_context': {
                'mastery_map': {'neural networks': 0.4}
            },
            'student_response': {
                'correct': True,
                'confidence': 0.8,
                'time_taken': 45,
                'hint_level_used': 0
            }
        }
        
        result = student_model_agent(state)
        
        # Mastery should have increased
        new_mastery = result['student_context']['mastery_map']['neural networks']
        assert new_mastery > 0.4
        
    def test_agent_detects_misconceptions(self):
        """Agent should detect misconceptions from incorrect answers"""
        state = {
            'query': 'test on supervised learning',
            'student_context': {},
            'student_response': {
                'correct': False,
                'confidence': 0.5,
                'time_taken': 60,
                'hint_level_used': 1,
                'answer': 'supervised learning works without labels',
                'correct_answer': 'supervised learning requires labeled data'
            }
        }
        
        result = student_model_agent(state)
        
        # Should detect misconception
        if 'detected_misconception' in result:
            assert result['detected_misconception'] == 'ml_paradigm_confusion'


class TestStudentModelPersistence:
    """Test student model serialization and persistence"""
    
    def test_to_dict_exports_all_data(self):
        """to_dict should export complete student model"""
        model = StudentModel({'student_id': 'test_123'})
        model.mastery_map = {'dfs': 0.7, 'bfs': 0.6}
        model.struggling_topics = ['neural networks']
        model.misconceptions = {'neural networks': ['activation_confusion']}
        
        data = model.to_dict()
        
        assert data['student_id'] == 'test_123'
        assert data['mastery_map']['dfs'] == 0.7
        assert 'neural networks' in data['struggling_topics']
        assert 'activation_confusion' in data['misconceptions']['neural networks']
        assert 'updated_at' in data
        
    def test_roundtrip_serialization(self):
        """Should be able to save and load student model"""
        model1 = StudentModel()
        model1.mastery_map = {'dfs': 0.8}
        model1.struggling_topics = ['bfs']
        
        # Export
        data = model1.to_dict()
        
        # Import
        model2 = StudentModel(data)
        
        assert model2.mastery_map['dfs'] == 0.8
        assert 'bfs' in model2.struggling_topics


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
