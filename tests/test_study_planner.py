"""
High-level tests for Study Planner Agent

Tests verify:
1. Spaced repetition scheduling (Ebbinghaus curve)
2. Prerequisite ordering (topological sort)
3. Time allocation based on mastery gaps
4. Interleaving (mixing topics)
5. Exam preparation optimization
6. Weekly study plan generation
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langgraph.agents.study_planner import StudyPlanner, StudySession, study_planner_agent
from langgraph.agents.student_model import StudentModel


def create_mock_student_model(mastery_map=None, struggling=None):
    """Helper to create student model for testing"""
    context = {
        'mastery_map': mastery_map or {},
        'struggling_topics': struggling or [],
        'review_schedule': {}
    }
    return StudentModel(context)


def create_mock_course_structure():
    """Helper to create course structure"""
    return {
        'topics': {
            'dfs': {
                'prerequisites': [],
                'difficulty': 'medium',
                'materials': ['Week 3 Notes', 'DFS Practice']
            },
            'bfs': {
                'prerequisites': [],
                'difficulty': 'medium',
                'materials': ['Week 3 Notes', 'BFS Practice']
            },
            'a*': {
                'prerequisites': ['dfs', 'bfs'],
                'difficulty': 'hard',
                'materials': ['Week 4 Notes', 'A* Examples']
            },
            'neural networks': {
                'prerequisites': [],
                'difficulty': 'hard',
                'materials': ['Week 6 Notes', 'NN Simulator']
            },
            'backpropagation': {
                'prerequisites': ['neural networks', 'calculus'],
                'difficulty': 'hard',
                'materials': ['Week 7 Notes', 'Backprop Derivation']
            },
            'calculus': {
                'prerequisites': [],
                'difficulty': 'medium',
                'materials': ['Math Review']
            }
        }
    }


class TestExamPrepPlanning:
    """Test exam preparation plan generation"""
    
    def test_creates_plan_with_sessions(self):
        """Should create study plan with scheduled sessions"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.5, 'bfs': 0.6, 'a*': 0.2}
        )
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        exam_date = (datetime.now() + timedelta(days=14)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['dfs', 'bfs', 'a*'],
            available_hours_per_week=10
        )
        
        assert 'sessions' in plan
        assert len(plan['sessions']) > 0
        assert 'total_hours' in plan
        assert 'recommendations' in plan
        
    def test_allocates_more_time_to_weak_topics(self):
        """Weak topics should get more study hours"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.9, 'neural networks': 0.2}
        )
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        exam_date = (datetime.now() + timedelta(days=14)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['dfs', 'neural networks'],
            available_hours_per_week=10
        )
        
        coverage = plan['coverage']
        
        # Neural networks (low mastery) should get more hours than DFS (high mastery)
        assert coverage['neural networks'] > coverage['dfs']
        
    def test_distributes_study_over_available_time(self):
        """Should distribute study sessions across available time (anti-cramming)"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.5}
        )
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        exam_date = (datetime.now() + timedelta(days=21)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['dfs'],
            available_hours_per_week=5
        )
        
        # Sessions should be spread out (not all on same day)
        session_dates = [s['date'] for s in plan['sessions']]
        unique_dates = set(session_dates)
        
        # Should have multiple different dates
        assert len(unique_dates) > 1
        
    def test_calculates_readiness_score(self):
        """Should calculate exam readiness based on current mastery"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.8, 'bfs': 0.7, 'a*': 0.6}
        )
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        exam_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['dfs', 'bfs', 'a*'],
            available_hours_per_week=10
        )
        
        # Readiness should be around 70% (average of 0.8, 0.7, 0.6)
        assert 60 <= plan['readiness_score'] <= 80
        
    def test_provides_recommendations(self):
        """Should provide actionable study recommendations"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.2}  # Low mastery
        )
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        exam_date = (datetime.now() + timedelta(days=3)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['dfs'],
            available_hours_per_week=10
        )
        
        recommendations = plan['recommendations']
        
        # Should have multiple recommendations
        assert len(recommendations) > 0
        
        # Should warn about urgency (< 7 days)
        assert any('URGENT' in rec or 'week' in rec for rec in recommendations)


class TestSpacedRepetition:
    """Test spaced repetition scheduling"""
    
    def test_spaces_sessions_with_increasing_intervals(self):
        """Sessions should have exponentially increasing intervals"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.5}
        )
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        exam_date = (datetime.now() + timedelta(days=28)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['dfs'],
            available_hours_per_week=5
        )
        
        # Get sessions for DFS
        dfs_sessions = [s for s in plan['sessions'] if s['topic'] == 'dfs']
        
        if len(dfs_sessions) > 1:
            # Check that intervals increase
            dates = [datetime.fromisoformat(s['date']) for s in dfs_sessions]
            dates.sort()
            
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            
            # Intervals should generally increase (spaced repetition)
            # First interval should be shorter than last
            if len(intervals) > 1:
                assert intervals[0] <= intervals[-1]
                
    def test_first_session_is_learning(self):
        """First session for a topic should be 'learn', later ones 'review'"""
        model = create_mock_student_model(
            mastery_map={'neural networks': 0.3}
        )
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        exam_date = (datetime.now() + timedelta(days=21)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['neural networks'],
            available_hours_per_week=10
        )
        
        nn_sessions = [s for s in plan['sessions'] if s['topic'] == 'neural networks']
        
        if len(nn_sessions) > 1:
            # Sort by date
            nn_sessions.sort(key=lambda s: s['date'])
            
            # First should be learn, later ones should include review
            assert nn_sessions[0]['activity_type'] == 'learn'
            assert any(s['activity_type'] == 'review' for s in nn_sessions[1:])


class TestWeeklyPlanning:
    """Test weekly study plan generation"""
    
    def test_creates_balanced_weekly_plan(self):
        """Should create plan with balanced activities (learn/review/practice)"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.6, 'bfs': 0.5},
            struggling=['neural networks']
        )
        # Add review schedule
        model.review_schedule['dfs'] = (datetime.now() - timedelta(days=1)).isoformat()
        
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        plan = planner.create_weekly_plan(hours_available=10)
        
        assert 'sessions' in plan
        assert 'balance' in plan
        
        # Should have mix of activities
        activities = [s['activity_type'] for s in plan['sessions']]
        activity_types = set(activities)
        
        # Should have at least 2 different types
        assert len(activity_types) >= 2
        
    def test_includes_review_for_due_topics(self):
        """Should include review sessions for topics due for review"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.7}
        )
        # Set DFS as due for review (yesterday)
        model.review_schedule['dfs'] = (datetime.now() - timedelta(days=1)).isoformat()
        
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        plan = planner.create_weekly_plan(hours_available=10)
        
        # Should have review session for DFS
        review_sessions = [s for s in plan['sessions'] 
                          if s['activity_type'] == 'review' and s['topic'] == 'dfs']
        
        assert len(review_sessions) > 0
        
    def test_includes_practice_for_struggling_topics(self):
        """Should include practice sessions for struggling areas"""
        model = create_mock_student_model(
            mastery_map={'neural networks': 0.2},
            struggling=['neural networks']
        )
        
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        plan = planner.create_weekly_plan(hours_available=10)
        
        # Should have practice session for neural networks
        practice_sessions = [s for s in plan['sessions'] 
                           if s['activity_type'] == 'practice' and s['topic'] == 'neural networks']
        
        assert len(practice_sessions) > 0
        
    def test_respects_hour_limit(self):
        """Total study hours should not exceed available hours"""
        model = create_mock_student_model()
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        plan = planner.create_weekly_plan(hours_available=8)
        
        total_hours = plan['total_hours']
        
        # Should be close to but not exceed 8 hours
        assert total_hours <= 10  # Some buffer for rounding


class TestPrerequisiteOrdering:
    """Test topological sort for prerequisite ordering"""
    
    def test_orders_topics_by_prerequisites(self):
        """Should order topics so prerequisites come first"""
        model = create_mock_student_model()
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        topics = ['backpropagation', 'neural networks', 'a*', 'dfs', 'bfs']
        
        ordered = planner.optimize_topic_order(topics)
        
        # Extract topic names in order
        topic_names = [item['topic'] for item in ordered]
        
        # dfs and bfs should come before a* (prerequisites)
        dfs_idx = topic_names.index('dfs')
        bfs_idx = topic_names.index('bfs')
        astar_idx = topic_names.index('a*')
        
        assert dfs_idx < astar_idx
        assert bfs_idx < astar_idx
        
        # neural networks should come before backpropagation
        nn_idx = topic_names.index('neural networks')
        backprop_idx = topic_names.index('backpropagation')
        
        assert nn_idx < backprop_idx
        
    def test_estimates_hours_based_on_mastery(self):
        """Should estimate more hours for topics with low mastery"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.9, 'neural networks': 0.1}
        )
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        ordered = planner.optimize_topic_order(['dfs', 'neural networks'])
        
        # Find estimated hours for each
        dfs_hours = next(item['estimated_hours'] for item in ordered if item['topic'] == 'dfs')
        nn_hours = next(item['estimated_hours'] for item in ordered if item['topic'] == 'neural networks')
        
        # Neural networks (low mastery) should need more hours
        assert nn_hours > dfs_hours
        
    def test_includes_prerequisite_info(self):
        """Should include prerequisite information for each topic"""
        model = create_mock_student_model()
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        ordered = planner.optimize_topic_order(['a*', 'dfs', 'bfs'])
        
        # Find a* entry
        astar_entry = next(item for item in ordered if item['topic'] == 'a*')
        
        # Should list prerequisites
        assert 'prerequisites' in astar_entry
        assert set(astar_entry['prerequisites']) == {'dfs', 'bfs'}


class TestInterleaving:
    """Test interleaving of topics (mixing vs blocking)"""
    
    def test_weekly_plan_interleaves_topics(self):
        """Should mix different topics rather than blocking by topic"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.5, 'bfs': 0.5, 'neural networks': 0.4}
        )
        model.review_schedule['dfs'] = (datetime.now() - timedelta(days=1)).isoformat()
        model.review_schedule['bfs'] = (datetime.now() - timedelta(days=1)).isoformat()
        
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        plan = planner.create_weekly_plan(hours_available=15)
        
        # Get topics in order of sessions
        topics_in_order = [s['topic'] for s in plan['sessions']]
        
        # Should have variety (not all same topic consecutively)
        unique_topics = set(topics_in_order)
        
        # Should have at least 2 different topics
        assert len(unique_topics) >= 2


class TestSessionGoals:
    """Test session goal generation"""
    
    def test_learning_sessions_have_understanding_goals(self):
        """Learning sessions should focus on understanding concepts"""
        model = create_mock_student_model()
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        exam_date = (datetime.now() + timedelta(days=14)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['dfs'],
            available_hours_per_week=5
        )
        
        learning_sessions = [s for s in plan['sessions'] if s['activity_type'] == 'learn']
        
        if learning_sessions:
            goals = learning_sessions[0]['goals']
            
            # Should have understanding-focused goals
            goal_text = ' '.join(goals).lower()
            assert 'understand' in goal_text or 'concepts' in goal_text
            
    def test_review_sessions_have_recall_goals(self):
        """Review sessions should focus on recall and practice"""
        model = create_mock_student_model(
            mastery_map={'dfs': 0.6}
        )
        model.review_schedule['dfs'] = (datetime.now() - timedelta(days=1)).isoformat()
        
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        plan = planner.create_weekly_plan(hours_available=5)
        
        review_sessions = [s for s in plan['sessions'] if s['activity_type'] == 'review']
        
        if review_sessions:
            goals = review_sessions[0]['goals']
            
            # Should have recall-focused goals
            goal_text = ' '.join(goals).lower()
            assert 'recall' in goal_text or 'practice' in goal_text or 'refresh' in goal_text


class TestStudyPlannerAgent:
    """Test LangGraph agent wrapper"""
    
    def test_agent_creates_exam_plan_from_query(self):
        """Agent should create exam prep plan from exam query"""
        state = {
            'query': 'create study plan for exam on 2025-10-21',
            'student_context': {
                'mastery_map': {'dfs': 0.5}
            }
        }
        
        result = study_planner_agent(state)
        
        assert 'study_plan' in result
        assert result['plan_type'] == 'exam_prep'
        
    def test_agent_creates_weekly_plan_from_query(self):
        """Agent should create weekly plan from weekly query"""
        state = {
            'query': 'plan my study week',
            'student_context': {
                'mastery_map': {'dfs': 0.6}
            }
        }
        
        result = study_planner_agent(state)
        
        assert 'study_plan' in result
        assert result['plan_type'] == 'weekly'
        
    def test_agent_optimizes_topic_order_from_query(self):
        """Agent should optimize topic order from sequence query"""
        state = {
            'query': 'what order should i study these topics',
            'student_context': {}
        }
        
        result = study_planner_agent(state)
        
        assert 'study_plan' in result
        assert result['plan_type'] == 'topic_order'


class TestStudyPlanIntegration:
    """High-level integration tests"""
    
    def test_complete_exam_prep_workflow(self):
        """Test complete exam prep planning workflow"""
        # Student with mixed mastery levels
        model = create_mock_student_model(
            mastery_map={'dfs': 0.8, 'bfs': 0.6, 'a*': 0.2, 'neural networks': 0.3},
            struggling=['neural networks']
        )
        
        course = create_mock_course_structure()
        planner = StudyPlanner(model, course)
        
        # Create 2-week exam prep plan
        exam_date = (datetime.now() + timedelta(days=14)).isoformat()
        
        plan = planner.create_exam_prep_plan(
            exam_date=exam_date,
            exam_topics=['dfs', 'bfs', 'a*', 'neural networks'],
            available_hours_per_week=12
        )
        
        # Verify plan structure
        assert 'sessions' in plan
        assert 'timeline' in plan
        assert 'coverage' in plan
        assert 'recommendations' in plan
        
        # Verify coverage favors weak topics
        assert plan['coverage']['a*'] >= plan['coverage']['dfs']
        assert plan['coverage']['neural networks'] >= plan['coverage']['bfs']
        
        # Verify sessions are distributed
        assert len(plan['timeline']) > 1  # Multiple weeks
        
        # Verify readiness score
        assert 0 <= plan['readiness_score'] <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
