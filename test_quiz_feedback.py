"""
Test Quiz Feedback System
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_single_quiz_question():
    """Test feedback for a single question"""
    print("="*70)
    print("TEST 1: Single Quiz Question Feedback")
    print("="*70)
    
    data = {
        "question": "What is the Turing Test?",
        "question_type": "short_answer",
        "correct_answer": "A test proposed by Alan Turing to determine if a machine can exhibit intelligent behavior indistinguishable from a human.",
        "student_answer": "It's when you talk to a computer and try to guess if it's human or AI",
        "course_context": "The Turing Test was introduced by Alan Turing in 1950 in his paper 'Computing Machinery and Intelligence'."
    }
    
    try:
        response = requests.post(
            f"{API_URL}/quiz/feedback",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ FEEDBACK RECEIVED:")
            print(f"  Correct: {result['is_correct']}")
            print(f"  Level: {result['correctness_level']}")
            print(f"  Score: {result['score']}")
            print(f"\n  Feedback: {result['feedback']}")
            print(f"\n  Hints:")
            for hint in result.get('hints', []):
                print(f"    - {hint}")
            print(f"\n  Encouragement: {result['encouragement']}")
            print(f"  Next Step: {result['next_step']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")


def test_batch_quiz():
    """Test feedback for multiple questions"""
    print("\n\n" + "="*70)
    print("TEST 2: Batch Quiz Feedback (3 questions)")
    print("="*70)
    
    data = {
        "questions": [
            {
                "question": "What is supervised learning?",
                "type": "short_answer",
                "correct_answer": "A type of machine learning where the algorithm learns from labeled training data with known inputs and outputs."
            },
            {
                "question": "Neural networks are inspired by the human brain. True or False?",
                "type": "true_false",
                "correct_answer": "True"
            },
            {
                "question": "Which of these is NOT a type of machine learning? A) Supervised B) Unsupervised C) Telepathic D) Reinforcement",
                "type": "multiple_choice",
                "correct_answer": "C"
            }
        ],
        "student_answers": [
            "Learning where you have examples with the right answers",
            "True",
            "C"
        ],
        "course_context": "Machine learning is a subset of AI that enables systems to learn from data."
    }
    
    try:
        response = requests.post(
            f"{API_URL}/quiz/batch-feedback",
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ QUIZ RESULTS:")
            print(f"  Total Questions: {result['total_questions']}")
            print(f"  Correct: {result['correct_count']}")
            print(f"  Score: {result['percentage']}%")
            print(f"  Grade: {result['grade']}")
            print(f"\n  Overall Feedback: {result['overall_feedback']}")
            
            print(f"\n📝 QUESTION-BY-QUESTION RESULTS:")
            for q_result in result['question_results']:
                print(f"\n  Question {q_result['question_number']}: {q_result['question'][:50]}...")
                print(f"    Student Answer: {q_result['student_answer'][:50]}")
                print(f"    Result: {q_result['correctness_level']} ({q_result['score']})")
                print(f"    Feedback: {q_result['feedback'][:100]}...")
            
            if result.get('areas_to_review'):
                print(f"\n📚 AREAS TO REVIEW:")
                for topic in result['areas_to_review']:
                    print(f"    - {topic}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    print("\n🎯 QUIZ FEEDBACK SYSTEM TEST\n")
    print("Make sure the server is running on localhost:8000")
    print("Press Ctrl+C to cancel, or Enter to start...")
    input()
    
    test_single_quiz_question()
    test_batch_quiz()
    
    print("\n\n" + "="*70)
    print("✅ ALL TESTS COMPLETE")
    print("="*70)
