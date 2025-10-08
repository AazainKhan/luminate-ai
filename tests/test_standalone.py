"""
Standalone test runner for intelligent logic layer

Runs tests directly without pytest to verify core logic.
Can be run with: python3 test_standalone.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import directly from agent files
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../langgraph/agents'))

from student_model import StudentModel
from study_planner import StudyPlanner
from quiz_generator import QuizGenerator


class TestRunner:
    """Simple test runner"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
        
    def assert_equal(self, actual, expected, message=""):
        """Assert equality"""
        if actual == expected:
            self.passed += 1
            print(f"  ✅ {message or 'Test passed'}")
            return True
        else:
            self.failed += 1
            print(f"  ❌ {message or 'Test failed'}")
            print(f"     Expected: {expected}")
            print(f"     Got: {actual}")
            return False
            
    def assert_true(self, condition, message=""):
        """Assert condition is true"""
        if condition:
            self.passed += 1
            print(f"  ✅ {message or 'Test passed'}")
            return True
        else:
            self.failed += 1
            print(f"  ❌ {message or 'Test failed'}")
            return False
            
    def assert_in(self, item, collection, message=""):
        """Assert item in collection"""
        if item in collection:
            self.passed += 1
            print(f"  ✅ {message or 'Test passed'}")
            return True
        else:
            self.failed += 1
            print(f"  ❌ {message or 'Test failed'}")
            print(f"     '{item}' not in {collection}")
            return False
            
    def assert_greater(self, a, b, message=""):
        """Assert a > b"""
        if a > b:
            self.passed += 1
            print(f"  ✅ {message or 'Test passed'}")
            return True
        else:
            self.failed += 1
            print(f"  ❌ {message or 'Test failed'}")
            print(f"     {a} not > {b}")
            return False
            
    def assert_less(self, a, b, message=""):
        """Assert a < b"""
        if a < b:
            self.passed += 1
            print(f"  ✅ {message or 'Test passed'}")
            return True
        else:
            self.failed += 1
            print(f"  ❌ {message or 'Test failed'}")
            print(f"     {a} not < {b}")
            return False
    
    def run_test(self, name, func):
        """Run a single test"""
        print(f"\n{name}")
        try:
            func(self)
        except Exception as e:
            self.failed += 1
            print(f"  ❌ Test error: {e}")
            import traceback
            traceback.print_exc()
    
    def summary(self):
        """Print summary"""
        total = self.passed + self.failed
        print("\n" + "="*60)
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"⚠️  {self.failed} tests failed")
        else:
            print("✅ All tests passed!")
        print("="*60)
        return self.failed == 0


# ============================================================================
# STUDENT MODEL TESTS
# ============================================================================

def test_student_model_initialization(runner):
    """Test student model creation"""
    model = StudentModel()
    runner.assert_equal(model.student_id, 'anonymous', "Default student ID")
    runner.assert_equal(model.mastery_map, {}, "Empty mastery map")
    runner.assert_equal(model.struggling_topics, [], "No struggling topics")


def test_mastery_estimation_new_topic(runner):
    """Test mastery for never-seen topic"""
    model = StudentModel()
    mastery = model.estimate_mastery('quantum physics')
    runner.assert_equal(mastery, 0.2, "New topic has 0.2 prior mastery")


def test_mastery_estimation_known_topic(runner):
    """Test mastery for known topic"""
    model = StudentModel()
    model.mastery_map['dfs'] = 0.8
    mastery = model.estimate_mastery('dfs')
    runner.assert_equal(mastery, 0.8, "Known topic returns stored mastery")


def test_correct_answer_increases_mastery(runner):
    """Test that correct answers increase mastery"""
    model = StudentModel()
    model.mastery_map['dfs'] = 0.5
    
    model.update_mastery('dfs', {
        'correct': True,
        'confidence': 0.9,
        'time_taken': 30,
        'hint_level_used': 0
    })
    
    new_mastery = model.estimate_mastery('dfs')
    runner.assert_greater(new_mastery, 0.5, "Correct answer increases mastery")


def test_incorrect_answer_decreases_mastery(runner):
    """Test that incorrect answers decrease mastery"""
    model = StudentModel()
    model.mastery_map['dfs'] = 0.7
    
    model.update_mastery('dfs', {
        'correct': False,
        'confidence': 0.3,
        'time_taken': 120,
        'hint_level_used': 2
    })
    
    new_mastery = model.estimate_mastery('dfs')
    runner.assert_less(new_mastery, 0.7, "Incorrect answer decreases mastery")


def test_struggling_topics_tracking(runner):
    """Test struggling topics are tracked"""
    model = StudentModel()
    
    # Multiple failures should mark as struggling
    for _ in range(2):
        model.update_mastery('backpropagation', {
            'correct': False,
            'confidence': 0.2,
            'time_taken': 200,
            'hint_level_used': 3
        })
    
    runner.assert_in('backpropagation', model.struggling_topics, "Failed topic marked as struggling")


def test_misconception_detection(runner):
    """Test misconception detection from patterns"""
    model = StudentModel()
    
    student_answer = "DFS explores using breadth-first approach"
    correct_answer = "DFS uses depth-first approach"
    
    misconception = model.detect_misconception('dfs', student_answer, correct_answer)
    
    runner.assert_equal(misconception, 'search_algorithm_confusion', "Detects DFS/BFS confusion")


def test_review_scheduling(runner):
    """Test spaced repetition scheduling"""
    model = StudentModel()
    
    # Low mastery → short interval
    model.update_mastery('topic_a', {
        'correct': False,
        'confidence': 0.3,
        'time_taken': 100,
        'hint_level_used': 2
    })
    
    runner.assert_in('topic_a', model.review_schedule, "Review scheduled for topic")


def test_student_model_serialization(runner):
    """Test to_dict and back"""
    model1 = StudentModel()
    model1.mastery_map = {'dfs': 0.8}
    model1.struggling_topics = ['bfs']
    
    data = model1.to_dict()
    
    model2 = StudentModel(data)
    runner.assert_equal(model2.mastery_map['dfs'], 0.8, "Serialization preserves mastery")
    runner.assert_in('bfs', model2.struggling_topics, "Serialization preserves struggling topics")


# ============================================================================
# STUDY PLANNER TESTS
# ============================================================================

def create_mock_course():
    """Create mock course structure"""
    return {
        'topics': {
            'dfs': {'prerequisites': [], 'difficulty': 'medium', 'materials': ['Week 3']},
            'bfs': {'prerequisites': [], 'difficulty': 'medium', 'materials': ['Week 3']},
            'a*': {'prerequisites': ['dfs', 'bfs'], 'difficulty': 'hard', 'materials': ['Week 4']},
            'neural networks': {'prerequisites': [], 'difficulty': 'hard', 'materials': ['Week 6']},
            'backpropagation': {'prerequisites': ['neural networks'], 'difficulty': 'hard', 'materials': ['Week 7']}
        }
    }


def test_exam_prep_plan_creation(runner):
    """Test exam prep plan generation"""
    model = StudentModel({'mastery_map': {'dfs': 0.5, 'bfs': 0.6}})
    planner = StudyPlanner(model, create_mock_course())
    
    exam_date = (datetime.now() + timedelta(days=14)).isoformat()
    plan = planner.create_exam_prep_plan(exam_date, ['dfs', 'bfs'], 10)
    
    runner.assert_in('sessions', plan, "Plan includes sessions")
    runner.assert_in('total_hours', plan, "Plan includes total hours")
    runner.assert_in('recommendations', plan, "Plan includes recommendations")


def test_weak_topics_get_more_time(runner):
    """Test time allocation favors weak topics"""
    model = StudentModel({'mastery_map': {'dfs': 0.9, 'neural networks': 0.2}})
    planner = StudyPlanner(model, create_mock_course())
    
    exam_date = (datetime.now() + timedelta(days=14)).isoformat()
    plan = planner.create_exam_prep_plan(exam_date, ['dfs', 'neural networks'], 10)
    
    coverage = plan['coverage']
    runner.assert_greater(
        coverage['neural networks'],
        coverage['dfs'],
        "Weak topic gets more study hours"
    )


def test_prerequisite_ordering(runner):
    """Test topics ordered by prerequisites"""
    model = StudentModel()
    planner = StudyPlanner(model, create_mock_course())
    
    ordered = planner.optimize_topic_order(['a*', 'dfs', 'bfs'])
    topic_names = [item['topic'] for item in ordered]
    
    dfs_idx = topic_names.index('dfs')
    astar_idx = topic_names.index('a*')
    
    runner.assert_less(dfs_idx, astar_idx, "Prerequisites come before dependent topics")


def test_weekly_plan_creation(runner):
    """Test weekly study plan"""
    model = StudentModel({'mastery_map': {'dfs': 0.6}})
    planner = StudyPlanner(model, create_mock_course())
    
    plan = planner.create_weekly_plan(hours_available=10)
    
    runner.assert_in('sessions', plan, "Weekly plan has sessions")
    runner.assert_in('balance', plan, "Weekly plan shows activity balance")


# ============================================================================
# QUIZ GENERATOR TESTS
# ============================================================================

class MockLLM:
    """Mock LLM for testing"""
    def invoke(self, prompt):
        class Response:
            content = '''{
                "question_text": "What is the time complexity of DFS?",
                "choices": {"A": "O(V+E)", "B": "O(V*E)", "C": "O(V^2)", "D": "O(log V)"},
                "correct_answer": "A",
                "explanation": "DFS visits each vertex and edge once.",
                "distractors_represent": ["correct", "confusion", "wrong", "different"]
            }'''
        return Response()


def test_quiz_generation(runner):
    """Test adaptive quiz generation"""
    llm = MockLLM()
    generator = QuizGenerator(llm, [])
    
    quiz = generator.generate_adaptive_quiz('dfs', student_mastery=0.5, num_questions=3)
    
    runner.assert_equal(len(quiz['questions']), 3, "Generates requested number of questions")
    runner.assert_in('metadata', quiz, "Quiz includes metadata")


def test_adaptive_difficulty_low_mastery(runner):
    """Test low mastery gets easy questions"""
    llm = MockLLM()
    generator = QuizGenerator(llm, [])
    
    quiz = generator.generate_adaptive_quiz('dfs', student_mastery=0.2, num_questions=3)
    difficulties = [q['difficulty'] for q in quiz['questions']]
    
    runner.assert_in('easy', difficulties, "Low mastery gets easy questions")


def test_adaptive_difficulty_high_mastery(runner):
    """Test high mastery gets hard questions"""
    llm = MockLLM()
    generator = QuizGenerator(llm, [])
    
    quiz = generator.generate_adaptive_quiz('dfs', student_mastery=0.85, num_questions=3)
    difficulties = [q['difficulty'] for q in quiz['questions']]
    
    runner.assert_in('hard', difficulties, "High mastery gets hard questions")


def test_answer_evaluation_correct(runner):
    """Test correct answer evaluation"""
    llm = MockLLM()
    generator = QuizGenerator(llm, [])
    
    question = {
        'id': 'q1',
        'correct_answer': 'A',
        'explanation': 'DFS has O(V+E) complexity.',
        'difficulty': 'medium',
        'bloom_level': 'remember',
        'topic': 'dfs'
    }
    
    # Use positional argument for student_confidence (3rd param)
    evaluation = generator.evaluate_answer(question, 'A', 0.9)
    
    runner.assert_true(evaluation['correct'], "Evaluates correct answer as correct")
    runner.assert_in('✅', evaluation['feedback'], "Feedback includes success indicator")


def test_answer_evaluation_incorrect(runner):
    """Test incorrect answer evaluation"""
    llm = MockLLM()
    generator = QuizGenerator(llm, [])
    
    question = {
        'id': 'q1',
        'correct_answer': 'A',
        'explanation': 'Explanation here.',
        'difficulty': 'medium',
        'bloom_level': 'understand',
        'topic': 'dfs'
    }
    
    # Use positional argument for student_confidence (3rd param)
    evaluation = generator.evaluate_answer(question, 'B', 0.6)
    
    runner.assert_true(not evaluation['correct'], "Evaluates wrong answer as incorrect")
    runner.assert_in('❌', evaluation['feedback'], "Feedback includes error indicator")


# ============================================================================
# MAIN RUNNER
# ============================================================================

def main():
    """Run all tests"""
    print("="*60)
    print("Luminate AI - Intelligent Logic Layer Tests (Standalone)")
    print("="*60)
    
    runner = TestRunner()
    
    print("\n📚 STUDENT MODEL TESTS")
    print("-"*60)
    runner.run_test("Test 1: Student model initialization", test_student_model_initialization)
    runner.run_test("Test 2: Mastery estimation (new topic)", test_mastery_estimation_new_topic)
    runner.run_test("Test 3: Mastery estimation (known topic)", test_mastery_estimation_known_topic)
    runner.run_test("Test 4: Correct answer increases mastery", test_correct_answer_increases_mastery)
    runner.run_test("Test 5: Incorrect answer decreases mastery", test_incorrect_answer_decreases_mastery)
    runner.run_test("Test 6: Struggling topics tracking", test_struggling_topics_tracking)
    runner.run_test("Test 7: Misconception detection", test_misconception_detection)
    runner.run_test("Test 8: Review scheduling", test_review_scheduling)
    runner.run_test("Test 9: Student model serialization", test_student_model_serialization)
    
    print("\n📅 STUDY PLANNER TESTS")
    print("-"*60)
    runner.run_test("Test 10: Exam prep plan creation", test_exam_prep_plan_creation)
    runner.run_test("Test 11: Weak topics get more time", test_weak_topics_get_more_time)
    runner.run_test("Test 12: Prerequisite ordering", test_prerequisite_ordering)
    runner.run_test("Test 13: Weekly plan creation", test_weekly_plan_creation)
    
    print("\n📝 QUIZ GENERATOR TESTS")
    print("-"*60)
    runner.run_test("Test 14: Quiz generation", test_quiz_generation)
    runner.run_test("Test 15: Adaptive difficulty (low mastery)", test_adaptive_difficulty_low_mastery)
    runner.run_test("Test 16: Adaptive difficulty (high mastery)", test_adaptive_difficulty_high_mastery)
    runner.run_test("Test 17: Answer evaluation (correct)", test_answer_evaluation_correct)
    runner.run_test("Test 18: Answer evaluation (incorrect)", test_answer_evaluation_incorrect)
    
    # Summary
    success = runner.summary()
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
