"""
Quiz Feedback Agent for Educate Mode
Evaluates student quiz answers and provides personalized feedback.
"""

from typing import Dict, Any, List
from llm_config import get_llm
import json


FEEDBACK_PROMPT = """You are an AI tutor providing feedback on a student's quiz answer.

**Question:** {question}

**Question Type:** {question_type}

**Correct Answer:** {correct_answer}

**Student's Answer:** {student_answer}

**Context from Course Materials:**
{course_context}

Your task: Evaluate the student's answer and provide constructive feedback.

Instructions:
1. Determine if the answer is CORRECT, PARTIALLY_CORRECT, or INCORRECT
2. Explain WHY their answer is right or wrong
3. If incorrect or partial, provide hints WITHOUT giving away the full answer
4. Reference relevant course concepts
5. Encourage the student and suggest what to review

Respond ONLY with valid JSON in this format:
{{
  "is_correct": true or false,
  "correctness_level": "CORRECT" or "PARTIALLY_CORRECT" or "INCORRECT",
  "score": 1.0 (for correct), 0.5 (for partial), or 0.0 (for incorrect),
  "feedback": "Detailed explanation of why the answer is correct/incorrect...",
  "hints": [
    "Hint 1 if needed",
    "Hint 2 if needed"
  ],
  "what_to_review": [
    "Concept or topic they should review",
    "Another related concept"
  ],
  "encouragement": "Positive, motivating message",
  "next_step": "Specific action they should take next"
}}

Important:
- Be encouraging even when the answer is wrong
- Provide educational value, not just "correct" or "incorrect"
- Reference specific concepts from the course context
- Keep feedback clear and actionable"""


def quiz_feedback_agent(
    question: str,
    question_type: str,
    correct_answer: str,
    student_answer: str,
    course_context: str = ""
) -> Dict[str, Any]:
    """
    Evaluate a student's quiz answer and provide feedback.
    
    Args:
        question: The quiz question text
        question_type: Type of question (multiple_choice, short_answer, true_false)
        correct_answer: The correct answer
        student_answer: The student's submitted answer
        course_context: Relevant course material context
        
    Returns:
        Dictionary with feedback, score, hints, and suggestions
    """
    print(f"📝 Evaluating quiz answer...")
    print(f"   Question type: {question_type}")
    print(f"   Student answered: {student_answer[:50]}...")
    
    # Build prompt
    prompt = FEEDBACK_PROMPT.format(
        question=question,
        question_type=question_type,
        correct_answer=correct_answer,
        student_answer=student_answer,
        course_context=course_context or "No additional context available"
    )
    
    try:
        # Use Gemini with moderate temperature for thoughtful feedback
        llm = get_llm(temperature=0.4, model="gemini-2.0-flash-exp")
        
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        feedback_data = json.loads(response_text)
        
        correctness = feedback_data.get("correctness_level", "INCORRECT")
        score = feedback_data.get("score", 0.0)
        
        print(f"✅ Feedback generated: {correctness} (score: {score})")
        
        return {
            "is_correct": feedback_data.get("is_correct", False),
            "correctness_level": correctness,
            "score": score,
            "feedback": feedback_data.get("feedback", ""),
            "hints": feedback_data.get("hints", []),
            "what_to_review": feedback_data.get("what_to_review", []),
            "encouragement": feedback_data.get("encouragement", "Keep learning!"),
            "next_step": feedback_data.get("next_step", "Review the course materials and try again.")
        }
        
    except Exception as e:
        print(f"⚠️  Quiz feedback error: {e}")
        
        # Fallback: Basic comparison
        is_correct = _basic_answer_check(student_answer, correct_answer, question_type)
        
        return {
            "is_correct": is_correct,
            "correctness_level": "CORRECT" if is_correct else "INCORRECT",
            "score": 1.0 if is_correct else 0.0,
            "feedback": f"Your answer is {'correct' if is_correct else 'incorrect'}. The correct answer is: {correct_answer}",
            "hints": ["Review the course materials on this topic."],
            "what_to_review": ["This concept"],
            "encouragement": "Keep practicing!" if not is_correct else "Well done!",
            "next_step": "Continue to the next question."
        }


def _basic_answer_check(student_answer: str, correct_answer: str, question_type: str) -> bool:
    """
    Simple fallback answer checking.
    """
    student_lower = str(student_answer).lower().strip()
    correct_lower = str(correct_answer).lower().strip()
    
    if question_type == "true_false":
        # Check for true/false variations
        if "true" in correct_lower:
            return "true" in student_lower or "yes" in student_lower
        else:
            return "false" in student_lower or "no" in student_lower
    
    elif question_type == "multiple_choice":
        # Check if the choice letter matches or if the full answer matches
        return student_lower == correct_lower or student_lower in correct_lower
    
    else:  # short_answer
        # Check for keyword overlap (very basic)
        return correct_lower in student_lower or student_lower in correct_lower


def batch_quiz_feedback(
    questions: List[Dict[str, Any]],
    student_answers: List[str],
    course_context: str = ""
) -> Dict[str, Any]:
    """
    Evaluate multiple quiz answers at once.
    
    Args:
        questions: List of question dicts with {question, type, correct_answer}
        student_answers: List of student's answers (same order as questions)
        course_context: Relevant course material context
        
    Returns:
        Dictionary with overall results, feedback for each question, and summary
    """
    if len(questions) != len(student_answers):
        return {
            "error": "Number of questions and answers must match",
            "total_questions": len(questions),
            "answers_received": len(student_answers)
        }
    
    results = []
    total_score = 0.0
    correct_count = 0
    
    print(f"\n📊 Evaluating {len(questions)} quiz answers...")
    
    for i, (question_data, student_ans) in enumerate(zip(questions, student_answers), 1):
        print(f"\n  Question {i}/{len(questions)}:")
        
        feedback = quiz_feedback_agent(
            question=question_data.get("question", ""),
            question_type=question_data.get("type", "short_answer"),
            correct_answer=question_data.get("correct_answer", ""),
            student_answer=student_ans,
            course_context=course_context
        )
        
        results.append({
            "question_number": i,
            "question": question_data.get("question", ""),
            "student_answer": student_ans,
            "correct_answer": question_data.get("correct_answer", ""),
            **feedback
        })
        
        total_score += feedback.get("score", 0.0)
        if feedback.get("is_correct", False):
            correct_count += 1
    
    # Calculate overall metrics
    percentage = (total_score / len(questions)) * 100 if questions else 0
    
    # Determine overall feedback
    if percentage >= 90:
        overall_message = "🎉 Excellent work! You have a strong understanding of this material."
        grade = "A"
    elif percentage >= 80:
        overall_message = "👍 Great job! You're doing well with most concepts."
        grade = "B"
    elif percentage >= 70:
        overall_message = "✅ Good effort! Review the areas you missed to improve."
        grade = "C"
    elif percentage >= 60:
        overall_message = "📚 You're on the right track, but more study is needed."
        grade = "D"
    else:
        overall_message = "💪 Keep practicing! Review the course materials and try again."
        grade = "F"
    
    print(f"\n✅ Quiz evaluation complete!")
    print(f"   Score: {correct_count}/{len(questions)} ({percentage:.1f}%)")
    print(f"   Grade: {grade}")
    
    return {
        "total_questions": len(questions),
        "correct_count": correct_count,
        "total_score": total_score,
        "percentage": round(percentage, 2),
        "grade": grade,
        "overall_feedback": overall_message,
        "question_results": results,
        "areas_to_review": _collect_review_topics(results)
    }


def _collect_review_topics(results: List[Dict]) -> List[str]:
    """
    Collect unique topics the student should review based on incorrect answers.
    """
    topics = set()
    for result in results:
        if not result.get("is_correct", False):
            topics.update(result.get("what_to_review", []))
    return list(topics)


if __name__ == "__main__":
    # Test the feedback agent
    print("="*70)
    print("QUIZ FEEDBACK AGENT TEST")
    print("="*70)
    
    # Test single question
    test_question = "What is the Turing Test?"
    test_correct = "A test proposed by Alan Turing to determine if a machine can exhibit intelligent behavior indistinguishable from a human."
    test_student = "It's a test where you talk to a computer and see if it seems human"
    
    feedback = quiz_feedback_agent(
        question=test_question,
        question_type="short_answer",
        correct_answer=test_correct,
        student_answer=test_student,
        course_context="The Turing Test was proposed in 1950 by Alan Turing in his paper 'Computing Machinery and Intelligence'."
    )
    
    print("\n📝 FEEDBACK:")
    print(f"  Correct: {feedback['is_correct']}")
    print(f"  Level: {feedback['correctness_level']}")
    print(f"  Score: {feedback['score']}")
    print(f"  Feedback: {feedback['feedback']}")
    print(f"  Hints: {feedback['hints']}")
    print(f"  Review: {feedback['what_to_review']}")
