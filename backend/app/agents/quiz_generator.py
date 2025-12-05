"""
Quiz Generator for COMP 237 AI Tutoring

Generates auto-graded quizzes based on concepts taught.
Quiz format follows the <quiz> XML structure defined in copilot-instructions.md
"""

import json
import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class QuizQuestion:
    """A single quiz question with multiple choice options."""
    question: str
    options: List[str]
    correct: int  # 0-indexed position of correct answer
    explanation: str
    concept: str  # The concept being tested
    difficulty: str = "medium"  # easy, medium, hard
    bloom_level: str = "understand"  # remember, understand, apply, analyze
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_xml(self) -> str:
        """Format as XML for embedding in responses."""
        return f"""<quiz>
{json.dumps(self.to_dict(), indent=2)}
</quiz>"""


# Pre-built quiz question bank for common COMP237 concepts
QUIZ_BANK = {
    "classification": [
        QuizQuestion(
            question="Which of the following is a classification problem?",
            options=[
                "Predicting house prices",
                "Predicting spam vs not-spam emails",
                "Predicting temperature tomorrow",
                "Predicting stock prices"
            ],
            correct=1,
            explanation="Classification predicts discrete categories (spam/not-spam). The others predict continuous values, making them regression problems.",
            concept="classification",
            bloom_level="understand"
        ),
        QuizQuestion(
            question="What does a classification model output?",
            options=[
                "A continuous number like 42.5",
                "A category or class label",
                "A probability distribution",
                "A list of features"
            ],
            correct=1,
            explanation="Classification models output discrete class labels (e.g., 'cat', 'dog', 'spam', 'not-spam').",
            concept="classification",
            bloom_level="remember"
        ),
    ],
    "regression": [
        QuizQuestion(
            question="Which algorithm is typically used for regression?",
            options=[
                "K-Nearest Neighbors (for classification)",
                "Linear Regression",
                "Naive Bayes",
                "Decision Tree (for classification)"
            ],
            correct=1,
            explanation="Linear Regression predicts continuous values by fitting a line to the data.",
            concept="regression",
            bloom_level="remember"
        ),
        QuizQuestion(
            question="What type of output does regression produce?",
            options=[
                "Categories like 'yes' or 'no'",
                "Continuous numerical values",
                "Binary 0 or 1",
                "Text labels"
            ],
            correct=1,
            explanation="Regression outputs continuous values (e.g., 23.5, 100.7), unlike classification which outputs discrete categories.",
            concept="regression",
            bloom_level="understand"
        ),
    ],
    "gradient_descent": [
        QuizQuestion(
            question="What is the purpose of gradient descent?",
            options=[
                "To increase the loss function",
                "To find the minimum of a function",
                "To add more features to the model",
                "To split the training data"
            ],
            correct=1,
            explanation="Gradient descent iteratively adjusts parameters to minimize the loss function, finding the optimal values.",
            concept="gradient_descent",
            bloom_level="understand"
        ),
        QuizQuestion(
            question="What happens if the learning rate is too large?",
            options=[
                "The model converges faster",
                "The model may overshoot and never converge",
                "The model becomes more accurate",
                "Nothing changes"
            ],
            correct=1,
            explanation="A large learning rate causes overshooting - the optimizer jumps past the minimum and may oscillate or diverge.",
            concept="gradient_descent",
            difficulty="medium",
            bloom_level="analyze"
        ),
    ],
    "backpropagation": [
        QuizQuestion(
            question="What is backpropagation used for?",
            options=[
                "Making predictions on new data",
                "Computing gradients to update weights",
                "Collecting training data",
                "Visualizing the neural network"
            ],
            correct=1,
            explanation="Backpropagation calculates gradients by propagating errors backward through the network, enabling weight updates.",
            concept="backpropagation",
            bloom_level="understand"
        ),
        QuizQuestion(
            question="Which mathematical concept is central to backpropagation?",
            options=[
                "Matrix multiplication",
                "The chain rule of calculus",
                "Euclidean distance",
                "Bayes' theorem"
            ],
            correct=1,
            explanation="The chain rule allows us to compute gradients through multiple layers by multiplying local gradients.",
            concept="backpropagation",
            difficulty="hard",
            bloom_level="analyze"
        ),
    ],
    "neural_networks": [
        QuizQuestion(
            question="What is an activation function in a neural network?",
            options=[
                "A function that initializes weights",
                "A function that introduces non-linearity",
                "A function that loads data",
                "A function that saves the model"
            ],
            correct=1,
            explanation="Activation functions like ReLU or sigmoid add non-linearity, allowing networks to learn complex patterns.",
            concept="neural_networks",
            bloom_level="understand"
        ),
    ],
    "supervised_learning": [
        QuizQuestion(
            question="What defines supervised learning?",
            options=[
                "The model learns without any data",
                "The training data includes input-output pairs (labels)",
                "The model clusters similar data points",
                "Human supervision during training"
            ],
            correct=1,
            explanation="In supervised learning, we provide labeled examples (input → correct output) for the model to learn from.",
            concept="supervised_learning",
            bloom_level="remember"
        ),
    ],
    "unsupervised_learning": [
        QuizQuestion(
            question="Which is an example of unsupervised learning?",
            options=[
                "Spam detection with labeled emails",
                "Image classification with labeled images",
                "Clustering customers by purchasing behavior",
                "Predicting house prices with historical data"
            ],
            correct=2,
            explanation="Clustering finds patterns without labels. The other options use labeled data (supervised learning).",
            concept="unsupervised_learning",
            bloom_level="apply"
        ),
    ],
    "clustering": [
        QuizQuestion(
            question="What does K-means clustering try to minimize?",
            options=[
                "The number of clusters",
                "The distance between cluster centers",
                "The within-cluster variance (inertia)",
                "The number of iterations"
            ],
            correct=2,
            explanation="K-means minimizes the sum of squared distances from points to their cluster centers (inertia).",
            concept="clustering",
            bloom_level="understand"
        ),
    ],
    "model_evaluation": [
        QuizQuestion(
            question="What does accuracy measure?",
            options=[
                "The speed of the model",
                "The proportion of correct predictions",
                "The size of the training set",
                "The number of features used"
            ],
            correct=1,
            explanation="Accuracy = (correct predictions) / (total predictions). It measures overall correctness.",
            concept="model_evaluation",
            bloom_level="remember"
        ),
        QuizQuestion(
            question="Why might accuracy be misleading for imbalanced datasets?",
            options=[
                "It's too slow to compute",
                "A model predicting only the majority class can have high accuracy",
                "It requires too much data",
                "It only works for regression"
            ],
            correct=1,
            explanation="With 99% negative samples, predicting all negative gives 99% accuracy but misses all positive cases!",
            concept="model_evaluation",
            difficulty="hard",
            bloom_level="analyze"
        ),
    ],
    "probability": [
        QuizQuestion(
            question="What does Bayes' theorem help us compute?",
            options=[
                "The gradient of a loss function",
                "The posterior probability given new evidence",
                "The accuracy of a model",
                "The number of training examples needed"
            ],
            correct=1,
            explanation="Bayes' theorem updates our belief (prior) to get a posterior probability after observing evidence.",
            concept="probability",
            bloom_level="understand"
        ),
    ],
}


def get_quiz_for_concept(concept: str, count: int = 1) -> List[QuizQuestion]:
    """
    Get quiz questions for a specific concept.
    
    Args:
        concept: The concept tag (e.g., 'classification', 'gradient_descent')
        count: Number of questions to return
        
    Returns:
        List of QuizQuestion objects
    """
    questions = QUIZ_BANK.get(concept, [])
    return questions[:count]


def format_quiz_for_response(questions: List[QuizQuestion]) -> str:
    """
    Format quiz questions for embedding in a tutor response.
    
    Returns formatted string with <quiz> XML tags.
    """
    if not questions:
        return ""
    
    parts = ["\n\n🧪 **Test Your Understanding:**"]
    
    for i, q in enumerate(questions, 1):
        parts.append(q.to_xml())
    
    return "\n".join(parts)


def evaluate_quiz_answer(
    question: QuizQuestion,
    selected_index: int
) -> Dict:
    """
    Evaluate a student's quiz answer.
    
    Args:
        question: The QuizQuestion object
        selected_index: The index (0-based) of the student's selected answer
        
    Returns:
        Dict with is_correct, feedback, and mastery_delta
    """
    is_correct = selected_index == question.correct
    
    if is_correct:
        feedback = f"✅ Correct! {question.explanation}"
        mastery_delta = 0.1  # Increase mastery by 10%
    else:
        correct_answer = question.options[question.correct]
        feedback = f"❌ Not quite. The correct answer is: **{correct_answer}**\n\n{question.explanation}"
        mastery_delta = -0.05  # Decrease mastery by 5%
    
    return {
        "is_correct": is_correct,
        "feedback": feedback,
        "correct_answer": question.options[question.correct],
        "selected_answer": question.options[selected_index] if 0 <= selected_index < len(question.options) else None,
        "explanation": question.explanation,
        "mastery_delta": mastery_delta,
        "concept": question.concept
    }


def parse_quiz_from_response(response: str) -> List[Dict]:
    """
    Extract quiz questions from a response containing <quiz> tags.
    
    Returns:
        List of quiz dictionaries
    """
    quizzes = []
    
    # Find all <quiz>...</quiz> blocks
    pattern = r'<quiz>\s*(.*?)\s*</quiz>'
    matches = re.findall(pattern, response, re.DOTALL)
    
    for match in matches:
        try:
            quiz_data = json.loads(match)
            quizzes.append(quiz_data)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse quiz JSON: {e}")
            continue
    
    return quizzes


def generate_quiz_prompt(concept: str, difficulty: str = "medium") -> str:
    """
    Generate a prompt for the LLM to create a quiz question.
    
    This is used when we don't have a pre-built question in QUIZ_BANK.
    """
    return f"""Generate a multiple-choice quiz question about {concept} in the context of COMP 237 Introduction to AI.

Difficulty: {difficulty}

Format your response as JSON inside <quiz> tags:
<quiz>
{{
  "question": "Your question here?",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct": 0,
  "explanation": "Brief explanation of why this answer is correct"
}}
</quiz>

Requirements:
- Question should test understanding, not just memorization
- Include 4 plausible options
- The correct answer index is 0-based
- Explanation should be educational and concise
"""
