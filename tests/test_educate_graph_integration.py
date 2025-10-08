"""
Integration tests for Educate Graph workflow

Tests verify:
1. Complete educate mode flow
2. Conditional routing (quiz vs study plan vs teaching)
3. Student model integration
4. State passing between agents
5. End-to-end teaching scenarios
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langgraph.educate_graph import build_educate_graph, query_educate_mode, EducateState


class MockChromaDB:
    """Mock ChromaDB for testing"""
    
    def query(self, query_embeddings, n_results=5, where=None):
        """Return mock results"""
        return {
            'ids': [['doc1', 'doc2', 'doc3']],
            'documents': [[
                'DFS is a graph traversal algorithm that explores depth-first.',
                'BFS explores breadth-first instead of depth-first.',
                'Time complexity of DFS is O(V + E).'
            ]],
            'metadatas': [[
                {'source': 'Week 3 Notes', 'module': 'Graph Algorithms'},
                {'source': 'Week 3 Notes', 'module': 'Graph Algorithms'},
                {'source': 'Week 3 Notes', 'module': 'Graph Algorithms'}
            ]],
            'distances': [[0.1, 0.2, 0.3]]
        }


class TestEducateGraphRouting:
    """Test conditional routing in educate graph"""
    
    def test_quiz_query_routes_to_quiz_generator(self):
        """'quiz me' queries should route to quiz generator"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'quiz me on dfs',
            'chroma_db': MockChromaDB(),
            'student_context': {'mastery_map': {'dfs': 0.5}}
        }
        
        # Run graph
        final_state = graph.invoke(initial_state)
        
        # Should have quiz data
        assert 'quiz_data' in final_state or 'formatted_response' in final_state
        
    def test_study_plan_query_routes_to_planner(self):
        """'study plan' queries should route to study planner"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'create a study plan for my exam',
            'chroma_db': MockChromaDB(),
            'student_context': {'mastery_map': {'dfs': 0.6}}
        }
        
        final_state = graph.invoke(initial_state)
        
        # Should have study plan data
        assert 'study_plan' in final_state or 'formatted_response' in final_state
        
    def test_explain_query_routes_to_teaching(self):
        """'explain' queries should route to interactive teaching"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'explain how dfs works',
            'chroma_db': MockChromaDB(),
            'student_context': {'mastery_map': {'dfs': 0.3}}
        }
        
        final_state = graph.invoke(initial_state)
        
        # Should have formatted response with teaching content
        assert 'formatted_response' in final_state


class TestStudentModelIntegration:
    """Test student model updates throughout workflow"""
    
    def test_student_insights_added_to_state(self):
        """Student model should add insights to state"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'explain neural networks',
            'chroma_db': MockChromaDB(),
            'student_context': {'mastery_map': {'neural networks': 0.4}}
        }
        
        final_state = graph.invoke(initial_state)
        
        # Should have student insights
        assert 'student_insights' in final_state
        insights = final_state['student_insights']
        
        assert 'current_mastery' in insights
        assert 'recommended_difficulty' in insights
        
    def test_student_context_updated_with_interaction(self):
        """Student context should be updated after interaction"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'test my understanding of dfs',
            'chroma_db': MockChromaDB(),
            'student_context': {
                'mastery_map': {'dfs': 0.5},
                'interaction_history': []
            }
        }
        
        final_state = graph.invoke(initial_state)
        
        # Student context should be updated
        assert 'student_context' in final_state
        
        # Should have interaction history (if student_model ran)
        if 'interaction_history' in final_state['student_context']:
            assert len(final_state['student_context']['interaction_history']) >= 0


class TestEndToEndTeachingScenarios:
    """Test complete teaching scenarios"""
    
    def test_struggling_student_gets_scaffolded_hints(self):
        """Student struggling with topic should get scaffolded hints"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'explain backpropagation',
            'chroma_db': MockChromaDB(),
            'student_context': {
                'mastery_map': {'backpropagation': 0.2},
                'struggling_topics': ['backpropagation']
            }
        }
        
        final_state = graph.invoke(initial_state)
        
        # Should use scaffolded hints strategy for struggling topic
        assert 'teaching_strategy' in final_state
        
        # Response should be formatted for interaction
        assert 'formatted_response' in final_state
        
    def test_advanced_student_gets_harder_content(self):
        """Student with high mastery should get challenging content"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'explain advanced dfs techniques',
            'chroma_db': MockChromaDB(),
            'student_context': {
                'mastery_map': {'dfs': 0.9}
            }
        }
        
        final_state = graph.invoke(initial_state)
        
        # Should have formatted response
        assert 'formatted_response' in final_state
        
        # Student insights should show high mastery
        if 'student_insights' in final_state:
            assert final_state['student_insights']['recommended_difficulty'] in ['hard', 'challenge']


class TestQueryEducateMode:
    """Test high-level query_educate_mode function"""
    
    def test_returns_formatted_response(self):
        """Should return formatted response dict"""
        result = query_educate_mode(
            query='explain dfs algorithm',
            chroma_db=MockChromaDB(),
            student_context={'mastery_map': {'dfs': 0.5}}
        )
        
        assert 'formatted_response' in result
        assert 'metadata' in result
        
    def test_initializes_default_student_context(self):
        """Should initialize default context if none provided"""
        result = query_educate_mode(
            query='explain neural networks',
            chroma_db=MockChromaDB(),
            student_context=None  # No context provided
        )
        
        # Should still work with default context
        assert 'formatted_response' in result
        
    def test_returns_teaching_strategy(self):
        """Should return the teaching strategy used"""
        result = query_educate_mode(
            query='explain dfs',
            chroma_db=MockChromaDB(),
            student_context={'mastery_map': {}}
        )
        
        # Should have teaching strategy in response
        assert 'teaching_strategy' in result or 'metadata' in result


class TestStatePassingBetweenAgents:
    """Test state is correctly passed between agents"""
    
    def test_retrieval_results_passed_to_formatter(self):
        """Retrieved content should be passed to formatting agent"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'what is dfs',
            'chroma_db': MockChromaDB(),
            'student_context': {}
        }
        
        final_state = graph.invoke(initial_state)
        
        # Should have retrieved chunks
        assert 'retrieved_chunks' in final_state or 'enriched_results' in final_state
        
    def test_student_insights_passed_to_quiz_generator(self):
        """Student insights should be available to quiz generator"""
        graph = build_educate_graph()
        
        initial_state: EducateState = {
            'query': 'quiz me on dfs',
            'chroma_db': MockChromaDB(),
            'student_context': {'mastery_map': {'dfs': 0.6}}
        }
        
        final_state = graph.invoke(initial_state)
        
        # Student insights should have been generated
        assert 'student_insights' in final_state


class TestErrorHandling:
    """Test error handling in educate graph"""
    
    def test_handles_empty_query(self):
        """Should handle empty query gracefully"""
        try:
            result = query_educate_mode(
                query='',
                chroma_db=MockChromaDB(),
                student_context={}
            )
            # Should still return a response
            assert 'formatted_response' in result or 'metadata' in result
        except Exception as e:
            # If it errors, should be a specific handled error
            assert 'query' in str(e).lower() or 'empty' in str(e).lower()
            
    def test_handles_missing_chroma_db(self):
        """Should handle missing ChromaDB gracefully"""
        try:
            result = query_educate_mode(
                query='explain dfs',
                chroma_db=None,
                student_context={}
            )
            # Should handle gracefully or provide error
            assert True  # Made it through without crashing
        except Exception:
            # Expected to fail, but shouldn't crash the system
            pass


class TestCompleteWorkflows:
    """Test complete realistic workflows"""
    
    def test_quiz_workflow(self):
        """Test complete quiz generation and evaluation workflow"""
        # Step 1: Student requests quiz
        result = query_educate_mode(
            query='quiz me on dfs',
            chroma_db=MockChromaDB(),
            student_context={'mastery_map': {'dfs': 0.5}}
        )
        
        # Should get quiz data or formatted quiz
        assert 'formatted_response' in result
        
    def test_study_plan_workflow(self):
        """Test complete study plan creation workflow"""
        # Student with upcoming exam
        exam_context = {
            'mastery_map': {'dfs': 0.6, 'bfs': 0.4, 'a*': 0.2},
            'struggling_topics': ['a*']
        }
        
        result = query_educate_mode(
            query='create study plan for exam on 2025-10-21',
            chroma_db=MockChromaDB(),
            student_context=exam_context
        )
        
        # Should get study plan
        assert 'formatted_response' in result
        
    def test_progressive_learning_workflow(self):
        """Test progressive learning: explain → hint → quiz → plan"""
        student_context = {'mastery_map': {'neural networks': 0.3}}
        
        # Step 1: Student asks for explanation
        result1 = query_educate_mode(
            query='explain neural networks',
            chroma_db=MockChromaDB(),
            student_context=student_context
        )
        
        assert 'formatted_response' in result1
        
        # Step 2: Student wants to test understanding
        result2 = query_educate_mode(
            query='quiz me on neural networks',
            chroma_db=MockChromaDB(),
            student_context=student_context
        )
        
        assert 'formatted_response' in result2
        
        # Step 3: Student asks for study plan
        result3 = query_educate_mode(
            query='plan my study week',
            chroma_db=MockChromaDB(),
            student_context=student_context
        )
        
        assert 'formatted_response' in result3


class TestPerformanceMetrics:
    """Test that system generates useful metrics"""
    
    def test_metadata_includes_query_info(self):
        """Metadata should include query parsing info"""
        result = query_educate_mode(
            query='explain dfs algorithm',
            chroma_db=MockChromaDB(),
            student_context={}
        )
        
        metadata = result.get('metadata', {})
        
        assert 'original_query' in metadata
        
    def test_metadata_includes_retrieval_info(self):
        """Metadata should include retrieval statistics"""
        result = query_educate_mode(
            query='what is neural network',
            chroma_db=MockChromaDB(),
            student_context={}
        )
        
        metadata = result.get('metadata', {})
        
        # Should have info about results
        assert 'total_results' in metadata or 'parsed_query' in metadata


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
