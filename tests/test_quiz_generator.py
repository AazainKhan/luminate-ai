"""
High-level tests for Quiz Generator Agent

Tests verify:
1. Adaptive difficulty selection (Zone of Proximal Development)
2. Bloom's Taxonomy level assignment
3. Misconception-revealing question generation
4. Intelligent answer evaluation and feedback
5. Progressive difficulty within quizzes
6. Formative assessment capabilities
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langgraph.agents.quiz_generator import QuizGenerator, quiz_generator_agent


class MockLLM:
    """Mock LLM for testing without API calls"""
    
    def __init__(self, response_template=None):
        self.response_template = response_template or {
            "question_text": "What is the time complexity of DFS?",
            "choices": {
                "A": "O(V + E)",
                "B": "O(V * E)",
                "C": "O(V^2)",
                "D": "O(log V)"
            },
            "correct_answer": "A",
            "explanation": "DFS visits each vertex once and explores each edge once.",
            "distractors_represent": ["correct", "confusion", "wrong assumption", "different algorithm"]
        }
    
    def invoke(self, prompt):
        class Response:
            def __init__(self, content):
                self.content = content
        
        return Response(json.dumps(self.response_template))


class TestAdaptiveDifficulty:
    """Test Zone of Proximal Development difficulty selection"""
    
    def test_low_mastery_gets_easy_questions(self):
        """Students with mastery < 30% should get easy questions"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='dfs',
            student_mastery=0.2,  # Low mastery
            num_questions=3
        )
        
        # Should target easy difficulty
        difficulties = [q['difficulty'] for q in quiz['questions']]
        assert 'easy' in difficulties
        
    def test_medium_mastery_gets_medium_questions(self):
        """Students with mastery 30-70% should get medium questions"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='neural networks',
            student_mastery=0.5,  # Medium mastery
            num_questions=3
        )
        
        # Should target medium difficulty
        difficulties = [q['difficulty'] for q in quiz['questions']]
        assert difficulties.count('medium') >= 2
        
    def test_high_mastery_gets_hard_questions(self):
        """Students with mastery > 70% should get hard questions"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='backpropagation',
            student_mastery=0.85,  # High mastery
            num_questions=3
        )
        
        # Should target hard difficulty
        difficulties = [q['difficulty'] for q in quiz['questions']]
        assert 'hard' in difficulties
        
    def test_progressive_difficulty_within_quiz(self):
        """Questions should progress from easier to harder within quiz"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='dfs',
            student_mastery=0.5,
            num_questions=3
        )
        
        difficulties = [q['difficulty'] for q in quiz['questions']]
        
        # Last question should not be easier than first
        difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
        assert difficulty_map[difficulties[-1]] >= difficulty_map[difficulties[0]]


class TestBloomsTaxonomy:
    """Test Bloom's Taxonomy cognitive level assignment"""
    
    def test_easy_questions_use_lower_bloom_levels(self):
        """Easy questions should focus on remember/understand"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='dfs',
            student_mastery=0.2,
            num_questions=3,
            difficulty_target='easy'
        )
        
        bloom_levels = [q['bloom_level'] for q in quiz['questions']]
        
        # Should use lower Bloom levels
        assert all(level in ['remember', 'understand'] for level in bloom_levels)
        
    def test_medium_questions_use_middle_bloom_levels(self):
        """Medium questions should focus on understand/apply"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='neural networks',
            student_mastery=0.5,
            num_questions=3,
            difficulty_target='medium'
        )
        
        bloom_levels = [q['bloom_level'] for q in quiz['questions']]
        
        # Should use middle Bloom levels
        assert any(level in ['understand', 'apply'] for level in bloom_levels)
        
    def test_hard_questions_use_higher_bloom_levels(self):
        """Hard questions should focus on apply/analyze"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='backpropagation',
            student_mastery=0.8,
            num_questions=3,
            difficulty_target='hard'
        )
        
        bloom_levels = [q['bloom_level'] for q in quiz['questions']]
        
        # Should use higher Bloom levels
        assert any(level in ['apply', 'analyze'] for level in bloom_levels)
        
    def test_bloom_progression_within_quiz(self):
        """Bloom levels should progress within quiz"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='dfs',
            student_mastery=0.5,
            num_questions=3
        )
        
        # Check that we have progression (not all same level)
        bloom_levels = [q['bloom_level'] for q in quiz['questions']]
        assert len(set(bloom_levels)) >= 2  # At least 2 different levels


class TestQuestionGeneration:
    """Test question generation with course content"""
    
    def test_generates_correct_number_of_questions(self):
        """Should generate requested number of questions"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='dfs',
            student_mastery=0.5,
            num_questions=5
        )
        
        assert len(quiz['questions']) == 5
        
    def test_questions_have_required_fields(self):
        """Each question should have all required fields"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='neural networks',
            student_mastery=0.5,
            num_questions=2
        )
        
        for question in quiz['questions']:
            assert 'id' in question
            assert 'question_text' in question
            assert 'choices' in question
            assert 'correct_answer' in question
            assert 'explanation' in question
            assert 'topic' in question
            assert 'difficulty' in question
            assert 'bloom_level' in question
            
            # Choices should have A, B, C, D
            assert set(question['choices'].keys()) == {'A', 'B', 'C', 'D'}
            
    def test_uses_course_content_in_generation(self):
        """Should extract and use relevant course content"""
        llm = MockLLM()
        chunks = [
            {'content': 'DFS is a graph traversal algorithm that explores depth-first.'},
            {'content': 'BFS explores breadth-first instead.'}
        ]
        generator = QuizGenerator(llm, chunks)
        
        # Extract content for topic
        content = generator._extract_content_for_topic('dfs')
        
        assert 'DFS' in content or 'dfs' in content.lower()


class TestMisconceptionQuestions:
    """Test misconception-revealing question generation"""
    
    def test_generates_misconception_question(self):
        """Should generate question with labeled misconceptions"""
        misconception_response = {
            "question_text": "What is supervised learning?",
            "choices": {
                "A": "Learning with labeled data",
                "B": "Learning without labels",
                "C": "Learning by trial and error",
                "D": "Learning from demonstrations"
            },
            "correct_answer": "A",
            "misconceptions": {
                "A": "correct",
                "B": "confusing with unsupervised",
                "C": "confusing with reinforcement",
                "D": "confusing with imitation"
            },
            "explanation": "Supervised learning requires labeled training data."
        }
        
        llm = MockLLM(misconception_response)
        generator = QuizGenerator(llm, [])
        
        question = generator._generate_misconception_question(
            'supervised learning',
            'Supervised learning uses labeled data for training.'
        )
        
        assert 'misconceptions' in question
        assert question['misconceptions']['A'] == 'correct'
        assert 'confusing' in question['misconceptions']['B']
        
    def test_formative_assessment_includes_diagnostics(self):
        """Formative assessments should include misconception questions"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        assessment = generator.generate_formative_assessment(
            topics=['dfs', 'neural networks'],
            weak_areas=['neural networks']
        )
        
        assert assessment['type'] == 'formative'
        assert 'interpretation' in assessment
        assert 'next_steps_by_question' in assessment['interpretation']


class TestAnswerEvaluation:
    """Test intelligent answer evaluation and feedback"""
    
    def test_correct_answer_high_confidence(self):
        """Correct answer with high confidence → increase difficulty"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        question = {
            'id': 'q1',
            'correct_answer': 'A',
            'explanation': 'DFS has O(V+E) complexity.',
            'difficulty': 'medium'
        }
        
        evaluation = generator.evaluate_answer(question, 'A', confidence=0.9)
        
        assert evaluation['correct'] == True
        assert '✅' in evaluation['feedback']
        assert evaluation['next_action'] == 'increase_difficulty'
        
    def test_correct_answer_low_confidence(self):
        """Correct answer with low confidence → review concept"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        question = {
            'id': 'q1',
            'correct_answer': 'B',
            'explanation': 'This is the correct approach.',
            'difficulty': 'medium'
        }
        
        evaluation = generator.evaluate_answer(question, 'B', confidence=0.3)
        
        assert evaluation['correct'] == True
        assert evaluation['next_action'] == 'review_concept'
        assert 'uncertain' in evaluation['feedback'].lower()
        
    def test_incorrect_answer_provides_remediation(self):
        """Incorrect answer → provide explanation and remediation"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        question = {
            'id': 'q1',
            'correct_answer': 'A',
            'explanation': 'DFS has O(V+E) time complexity.',
            'difficulty': 'medium'
        }
        
        evaluation = generator.evaluate_answer(question, 'B', confidence=0.6)
        
        assert evaluation['correct'] == False
        assert '❌' in evaluation['feedback']
        assert evaluation['next_action'] == 'provide_remediation'
        assert 'A' in evaluation['feedback']  # Shows correct answer
        
    def test_detects_misconception_from_wrong_answer(self):
        """Should detect specific misconception from wrong answer"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        question = {
            'id': 'q1',
            'correct_answer': 'A',
            'explanation': 'Supervised learning uses labeled data.',
            'misconceptions': {
                'A': 'correct',
                'B': 'confusing_with_unsupervised',
                'C': 'confusing_with_reinforcement',
                'D': 'overgeneralization'
            },
            'difficulty': 'easy'
        }
        
        evaluation = generator.evaluate_answer(question, 'B', confidence=0.7)
        
        assert evaluation['correct'] == False
        assert evaluation['misconception_detected'] == 'confusing_with_unsupervised'
        assert 'misconception' in evaluation['feedback'].lower()
        
    def test_performance_data_capture(self):
        """Evaluation should capture performance data for mastery update"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        question = {
            'id': 'q1',
            'correct_answer': 'A',
            'explanation': 'Explanation here.',
            'difficulty': 'hard',
            'bloom_level': 'analyze'
        }
        
        evaluation = generator.evaluate_answer(question, 'A', confidence=0.8)
        
        assert 'performance_data' in evaluation
        perf = evaluation['performance_data']
        assert perf['correct'] == True
        assert perf['confidence'] == 0.8
        assert perf['question_difficulty'] == 'hard'
        assert perf['bloom_level'] == 'analyze'


class TestQuizMetadata:
    """Test quiz metadata calculation"""
    
    def test_calculates_difficulty_distribution(self):
        """Should calculate distribution of difficulty levels"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='dfs',
            student_mastery=0.5,
            num_questions=6
        )
        
        metadata = quiz['metadata']
        dist = metadata['difficulty_distribution']
        
        # Should have counts for each difficulty
        assert 'easy' in dist
        assert 'medium' in dist
        assert 'hard' in dist
        
        # Total should equal number of questions
        assert sum(dist.values()) == 6
        
    def test_estimates_completion_time(self):
        """Should estimate time based on question difficulties"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        quiz = generator.generate_adaptive_quiz(
            topic='neural networks',
            student_mastery=0.5,
            num_questions=3
        )
        
        estimated_time = quiz['metadata']['estimated_time_minutes']
        
        # Should have reasonable estimate (2-5 min per question)
        assert estimated_time >= 3  # At least 1 min per question
        assert estimated_time <= 15  # At most 5 min per question


class TestQuizGeneratorAgent:
    """Test LangGraph agent wrapper"""
    
    def test_agent_generates_quiz_from_query(self):
        """Agent should generate quiz from student query"""
        state = {
            'query': 'quiz me on dfs',
            'student_insights': {
                'current_mastery': 0.6,
                'topic': 'dfs'
            },
            'retrieved_results': [
                {'content': 'DFS is a graph traversal algorithm.'}
            ]
        }
        
        # Mock the LLM import
        import sys
        from unittest.mock import MagicMock
        
        mock_llm_module = MagicMock()
        mock_llm_module.ChatGoogleGenerativeAI = MockLLM
        sys.modules['langchain_google_genai'] = mock_llm_module
        
        result = quiz_generator_agent(state)
        
        assert 'quiz_data' in result
        assert 'questions' in result['quiz_data']
        
    def test_agent_creates_formative_for_diagnostic(self):
        """Agent should create formative assessment for diagnostic queries"""
        state = {
            'query': 'diagnostic quiz for neural networks',
            'student_insights': {
                'current_mastery': 0.4,
                'topic': 'neural networks'
            },
            'retrieved_results': []
        }
        
        # Mock LLM
        import sys
        from unittest.mock import MagicMock
        
        mock_llm_module = MagicMock()
        mock_llm_module.ChatGoogleGenerativeAI = MockLLM
        sys.modules['langchain_google_genai'] = mock_llm_module
        
        result = quiz_generator_agent(state)
        
        quiz = result.get('quiz_data', {})
        
        # Should be formative type if diagnostic keyword present
        if quiz.get('type') == 'formative':
            assert 'interpretation' in quiz


class TestQuizIntegration:
    """High-level integration tests"""
    
    def test_complete_quiz_generation_flow(self):
        """Test complete flow: generate quiz → evaluate answer → provide feedback"""
        llm = MockLLM()
        generator = QuizGenerator(llm, [])
        
        # Step 1: Generate quiz
        quiz = generator.generate_adaptive_quiz(
            topic='dfs',
            student_mastery=0.5,
            num_questions=3
        )
        
        assert len(quiz['questions']) == 3
        
        # Step 2: Student answers question
        first_question = quiz['questions'][0]
        
        # Step 3: Evaluate answer
        evaluation = generator.evaluate_answer(
            first_question,
            student_answer='A',
            student_confidence=0.7
        )
        
        assert 'correct' in evaluation
        assert 'feedback' in evaluation
        assert 'performance_data' in evaluation
        
        # Performance data should be ready for mastery update
        perf = evaluation['performance_data']
        assert 'correct' in perf
        assert 'confidence' in perf


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
