"""
Quiz Generator Agent - Creates adaptive quizzes

Based on assessment theory:
- Bloom's Taxonomy (knowledge → application → analysis)
- Item Response Theory (question difficulty matching)
- Formative assessment (identifying gaps, not just grading)
- Distractor analysis (plausible wrong answers reveal misconceptions)

This generates EDUCATIONAL quizzes, not just random questions.
"""

from typing import Dict, List, Any, Optional
import json
import re


class QuizGenerator:
    """
    Generates adaptive quizzes based on student mastery and learning goals
    """
    
    def __init__(self, llm_client: Any, course_chunks: List[Dict[str, Any]]):
        """
        Args:
            llm_client: LLM for generating questions
            course_chunks: Retrieved course content chunks
        """
        self.llm = llm_client
        self.chunks = course_chunks
    
    def generate_adaptive_quiz(
        self,
        topic: str,
        student_mastery: float,
        num_questions: int = 3,
        difficulty_target: str = None
    ) -> Dict[str, Any]:
        """
        Generate quiz adapted to student's mastery level
        
        Args:
            topic: Topic to quiz on
            student_mastery: 0-1 mastery level
            num_questions: Number of questions
            difficulty_target: Override difficulty ('easy', 'medium', 'hard')
        
        Returns:
            {
                'questions': [Question],
                'metadata': {difficulty_distribution, bloom_levels, estimated_time}
            }
        """
        # Determine difficulty based on mastery (Zone of Proximal Development)
        if difficulty_target is None:
            if student_mastery < 0.3:
                difficulty_target = 'easy'
            elif student_mastery < 0.7:
                difficulty_target = 'medium'
            else:
                difficulty_target = 'hard'
        
        # Extract relevant content
        content = self._extract_content_for_topic(topic)
        
        # Generate questions with progressive difficulty
        questions = []
        for i in range(num_questions):
            # Progressive difficulty within quiz
            if i == 0:
                q_difficulty = 'easy' if difficulty_target != 'easy' else 'medium'
            elif i == num_questions - 1:
                q_difficulty = 'hard' if difficulty_target == 'hard' else 'medium'
            else:
                q_difficulty = difficulty_target
            
            # Choose Bloom level based on difficulty
            bloom_level = self._get_bloom_level(q_difficulty, i)
            
            question = self._generate_question(
                topic,
                content,
                q_difficulty,
                bloom_level,
                question_num=i+1
            )
            
            questions.append(question)
        
        # Calculate metadata
        difficulty_dist = {
            'easy': sum(1 for q in questions if q['difficulty'] == 'easy'),
            'medium': sum(1 for q in questions if q['difficulty'] == 'medium'),
            'hard': sum(1 for q in questions if q['difficulty'] == 'hard')
        }
        
        bloom_dist = {}
        for q in questions:
            level = q['bloom_level']
            bloom_dist[level] = bloom_dist.get(level, 0) + 1
        
        # Estimate time (2 min for easy, 3 for medium, 5 for hard)
        time_per_q = {'easy': 2, 'medium': 3, 'hard': 5}
        estimated_time = sum(time_per_q[q['difficulty']] for q in questions)
        
        return {
            'topic': topic,
            'questions': questions,
            'metadata': {
                'difficulty_distribution': difficulty_dist,
                'bloom_distribution': bloom_dist,
                'estimated_time_minutes': estimated_time,
                'target_mastery_level': student_mastery
            }
        }
    
    def generate_formative_assessment(
        self,
        topics: List[str],
        weak_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate diagnostic quiz to identify knowledge gaps
        
        Focus on:
        - Common misconceptions
        - Prerequisite knowledge
        - Boundary cases
        
        Returns quiz + interpretation guide for results
        """
        questions = []
        
        # For each topic, create diagnostic questions
        for topic in topics[:3]:  # Limit to 3 topics
            content = self._extract_content_for_topic(topic)
            
            # Misconception question (distractor analysis)
            misconception_q = self._generate_misconception_question(topic, content)
            questions.append(misconception_q)
            
            # Application question (can they use it?)
            application_q = self._generate_question(
                topic,
                content,
                'medium',
                'application',
                question_num=len(questions)+1
            )
            questions.append(application_q)
        
        # Add interpretation guide
        interpretation = {
            'scoring': {
                '0-33%': 'Foundational gaps - focus on basic concepts and worked examples',
                '34-66%': 'Partial understanding - practice application and review misconceptions',
                '67-100%': 'Strong grasp - ready for advanced topics and challenge problems'
            },
            'next_steps_by_question': [
                {
                    'question_id': q['id'],
                    'if_incorrect': q.get('remediation', f"Review {q['topic']} fundamentals")
                }
                for q in questions
            ]
        }
        
        return {
            'type': 'formative',
            'questions': questions,
            'interpretation': interpretation,
            'purpose': 'Diagnostic assessment to identify knowledge gaps and guide study plan'
        }
    
    def _generate_question(
        self,
        topic: str,
        content: str,
        difficulty: str,
        bloom_level: str,
        question_num: int
    ) -> Dict[str, Any]:
        """
        Generate a single question using LLM
        
        Args:
            bloom_level: 'remember', 'understand', 'apply', 'analyze'
        """
        # Bloom-specific prompt guidance
        bloom_prompts = {
            'remember': 'Recall or recognize specific facts, terms, or concepts.',
            'understand': 'Explain concepts in your own words or give examples.',
            'apply': 'Use knowledge to solve a problem in a new situation.',
            'analyze': 'Break down concepts and explain relationships or differences.'
        }
        
        prompt = f"""Generate an educational multiple-choice question for COMP237.

Topic: {topic}
Difficulty: {difficulty}
Cognitive Level (Bloom's Taxonomy): {bloom_level} - {bloom_prompts[bloom_level]}

Course Content:
{content[:1500]}

Requirements:
1. Question should assess {bloom_level}-level understanding
2. Provide 4 answer choices (A, B, C, D)
3. Make wrong answers (distractors) plausible - they should reflect common misconceptions
4. Include brief explanation of why correct answer is right
5. For {difficulty} difficulty: {'basic facts and definitions' if difficulty == 'easy' else 'application and reasoning' if difficulty == 'medium' else 'complex analysis and synthesis'}

Return JSON:
{{
    "question_text": "...",
    "choices": {{
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
    }},
    "correct_answer": "A|B|C|D",
    "explanation": "...",
    "distractors_represent": ["misconception 1", "misconception 2", "common error"]
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group())
            else:
                # Fallback parsing
                question_data = self._parse_question_from_text(response.content)
            
            # Add metadata
            question_data.update({
                'id': f"q{question_num}",
                'topic': topic,
                'difficulty': difficulty,
                'bloom_level': bloom_level,
                'points': 1
            })
            
            return question_data
            
        except Exception as e:
            print(f"Error generating question: {e}")
            # Return fallback question
            return self._fallback_question(topic, difficulty, question_num)
    
    def _generate_misconception_question(
        self,
        topic: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Generate question targeting common misconceptions
        
        Distractors are carefully designed to reveal specific misunderstandings
        """
        prompt = f"""Generate a misconception-revealing question for COMP237.

Topic: {topic}
Course Content: {content[:1000]}

Create a question where:
1. Each wrong answer represents a SPECIFIC common misconception
2. Students who hold that misconception would logically choose that answer
3. The correct answer demonstrates proper understanding

Label each distractor with the misconception it represents.

Return JSON:
{{
    "question_text": "...",
    "choices": {{
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
    }},
    "correct_answer": "A|B|C|D",
    "misconceptions": {{
        "A": "misconception name or 'correct'",
        "B": "misconception name or 'correct'",
        "C": "misconception name or 'correct'",
        "D": "misconception name or 'correct'"
    }},
    "explanation": "Explain why correct answer is right and what each misconception is."
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            
            if json_match:
                question_data = json.loads(json_match.group())
            else:
                question_data = self._parse_question_from_text(response.content)
            
            question_data.update({
                'id': 'misconception',
                'topic': topic,
                'difficulty': 'medium',
                'bloom_level': 'understand',
                'type': 'misconception_diagnostic',
                'points': 1
            })
            
            return question_data
            
        except Exception as e:
            return self._fallback_question(topic, 'medium', 1)
    
    def evaluate_answer(
        self,
        question: Dict[str, Any],
        student_answer: str,
        student_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        Evaluate answer and provide feedback
        
        Returns:
            {
                'correct': bool,
                'feedback': str,
                'misconception_detected': str | None,
                'next_action': str
            }
        """
        correct = question['correct_answer'] == student_answer.upper()
        
        feedback_parts = []
        
        if correct:
            feedback_parts.append(f"✅ Correct! {question['explanation']}")
            
            if student_confidence < 0.5:
                feedback_parts.append(
                    "\n💡 You got it right but seemed uncertain. "
                    "Review the concept to build confidence."
                )
                next_action = 'review_concept'
            else:
                feedback_parts.append("\n🎯 Great understanding! Ready for harder questions.")
                next_action = 'increase_difficulty'
        else:
            feedback_parts.append(f"❌ Not quite. The correct answer is {question['correct_answer']}.")
            feedback_parts.append(f"\n{question['explanation']}")
            
            # Detect misconception if available
            misconception = None
            if 'misconceptions' in question:
                misconception = question['misconceptions'].get(student_answer.upper())
                if misconception and misconception != 'correct':
                    feedback_parts.append(
                        f"\n🔍 This suggests a misconception about: {misconception}. "
                        "Let's address this."
                    )
            
            next_action = 'provide_remediation'
        
        return {
            'correct': correct,
            'feedback': ''.join(feedback_parts),
            'misconception_detected': misconception if not correct else None,
            'next_action': next_action,
            'performance_data': {
                'correct': correct,
                'confidence': student_confidence,
                'question_difficulty': question['difficulty'],
                'bloom_level': question['bloom_level']
            }
        }
    
    def _get_bloom_level(self, difficulty: str, question_index: int) -> str:
        """Map difficulty to Bloom's taxonomy level"""
        # Progressive cognitive demand
        bloom_progression = {
            'easy': ['remember', 'understand', 'understand'],
            'medium': ['understand', 'apply', 'apply'],
            'hard': ['apply', 'analyze', 'analyze']
        }
        
        levels = bloom_progression.get(difficulty, ['understand', 'apply', 'apply'])
        return levels[min(question_index, len(levels) - 1)]
    
    def _extract_content_for_topic(self, topic: str) -> str:
        """Extract relevant content from chunks"""
        topic_lower = topic.lower()
        relevant_chunks = [
            chunk for chunk in self.chunks
            if topic_lower in chunk.get('content', '').lower()
        ]
        
        if relevant_chunks:
            # Combine top 3 most relevant
            return '\n\n'.join(
                chunk.get('content', '')[:500]
                for chunk in relevant_chunks[:3]
            )
        else:
            return f"Course material on {topic}"
    
    def _parse_question_from_text(self, text: str) -> Dict[str, Any]:
        """Parse question from unstructured text (fallback)"""
        # Simple parsing - in production, use more robust extraction
        return {
            'question_text': 'Sample question',
            'choices': {
                'A': 'Option A',
                'B': 'Option B',
                'C': 'Option C',
                'D': 'Option D'
            },
            'correct_answer': 'A',
            'explanation': 'Explanation here'
        }
    
    def _fallback_question(
        self,
        topic: str,
        difficulty: str,
        question_num: int
    ) -> Dict[str, Any]:
        """Generate fallback question if LLM fails"""
        return {
            'id': f'q{question_num}',
            'question_text': f'What is the main concept of {topic}?',
            'choices': {
                'A': 'Option A',
                'B': 'Option B',
                'C': 'Option C',
                'D': 'Option D'
            },
            'correct_answer': 'A',
            'explanation': f'Review the {topic} section of your course materials.',
            'topic': topic,
            'difficulty': difficulty,
            'bloom_level': 'remember',
            'points': 1
        }


def quiz_generator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate quiz based on student needs
    
    Handles queries like:
    - "quiz me on DFS"
    - "test my understanding of neural networks"
    - "diagnostic quiz for week 3"
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    query = state.get('query', '').lower()
    
    # Extract topic from query
    topic = _extract_topic(query)
    
    # Get student insights
    student_insights = state.get('student_insights', {})
    mastery = student_insights.get('current_mastery', 0.5)
    
    # Get retrieved content
    retrieved_results = state.get('retrieved_results', [])
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
    
    # Initialize generator
    generator = QuizGenerator(llm, retrieved_results)
    
    # Determine quiz type
    if 'diagnostic' in query or 'assess' in query or 'check understanding' in query:
        # Formative assessment
        topics = [topic]  # Could extract multiple
        quiz = generator.generate_formative_assessment(topics)
    else:
        # Adaptive quiz
        num_questions = 3  # Could parse from query
        quiz = generator.generate_adaptive_quiz(topic, mastery, num_questions)
    
    state['quiz_data'] = quiz
    
    return state


def _extract_topic(query: str) -> str:
    """Extract topic from query"""
    import re
    
    topics = [
        'dfs', 'bfs', 'a*', 'neural network', 'backpropagation',
        'gradient descent', 'supervised learning', 'unsupervised learning',
        'classification', 'regression', 'clustering', 'k-means'
    ]
    
    query_lower = query.lower()
    for topic in topics:
        if topic in query_lower:
            return topic
    
    # Fallback
    words = re.findall(r'\b[a-z]+\b', query_lower)
    return ' '.join(words[-2:]) if len(words) >= 2 else 'general topic'


if __name__ == "__main__":
    print("=" * 60)
    print("QUIZ GENERATOR TEST")
    print("=" * 60)
    
    # Mock LLM response
    class MockLLM:
        def invoke(self, prompt):
            class Response:
                content = '''{
                    "question_text": "What is the time complexity of DFS?",
                    "choices": {
                        "A": "O(V + E)",
                        "B": "O(V * E)",
                        "C": "O(V^2)",
                        "D": "O(E log V)"
                    },
                    "correct_answer": "A",
                    "explanation": "DFS visits each vertex once and explores each edge once, giving O(V + E).",
                    "distractors_represent": [
                        "correct",
                        "confusing with some graph algorithms",
                        "assuming adjacency matrix",
                        "confusing with Dijkstra"
                    ]
                }'''
            return Response()
    
    # Mock course content
    chunks = [
        {
            'content': 'Depth-First Search (DFS) is a graph traversal algorithm that explores as far as possible along each branch before backtracking. Time complexity: O(V + E).'
        }
    ]
    
    llm = MockLLM()
    generator = QuizGenerator(llm, chunks)
    
    # Test 1: Adaptive quiz
    print("\n1. ADAPTIVE QUIZ (medium mastery student)")
    quiz = generator.generate_adaptive_quiz('dfs', student_mastery=0.5, num_questions=3)
    
    print(f"\nTopic: {quiz['topic']}")
    print(f"Estimated Time: {quiz['metadata']['estimated_time_minutes']} minutes")
    print(f"Difficulty Distribution: {quiz['metadata']['difficulty_distribution']}")
    print(f"\nQuestions:")
    for q in quiz['questions']:
        print(f"\n  {q['id']}. {q['question_text']}")
        print(f"     Difficulty: {q['difficulty']}, Bloom: {q['bloom_level']}")
        for choice_id, choice_text in q['choices'].items():
            marker = '✓' if choice_id == q['correct_answer'] else ' '
            print(f"     [{marker}] {choice_id}. {choice_text}")
    
    # Test 2: Answer evaluation
    print("\n\n2. ANSWER EVALUATION")
    question = quiz['questions'][0]
    
    # Correct answer, high confidence
    eval1 = generator.evaluate_answer(question, 'A', confidence=0.9)
    print(f"\nStudent answer: A (confidence 90%)")
    print(f"Result: {eval1['feedback']}")
    print(f"Next action: {eval1['next_action']}")
    
    # Wrong answer
    eval2 = generator.evaluate_answer(question, 'B', confidence=0.6)
    print(f"\nStudent answer: B (confidence 60%)")
    print(f"Result: {eval2['feedback']}")
    print(f"Misconception: {eval2['misconception_detected']}")
    print(f"Next action: {eval2['next_action']}")
