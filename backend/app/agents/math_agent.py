"""
Math Agent for COMP 237
Specialized agent for mathematical reasoning, derivations, and AI mathematics

Handles:
- Gradient Descent & Learning Rate
- Backpropagation & Chain Rule
- Loss Functions (MSE, Cross-Entropy)
- Probability (Bayes, Conditional)
- Linear Algebra operations
"""

from typing import Dict, List, Optional
import logging
import time
import re
from app.agents.state import AgentState, MathDerivation
from app.agents.supervisor import Supervisor
from app.observability.langfuse_client import update_observation_with_usage

logger = logging.getLogger(__name__)


# Math topic detection patterns
MATH_TOPICS = {
    "gradient_descent": [
        r"gradient\s*descent", r"learning\s*rate", r"optimization",
        r"minimize", r"gradient", r"step\s*size"
    ],
    "backpropagation": [
        r"backprop", r"back\s*propagation", r"backward\s*pass",
        r"chain\s*rule", r"error\s*propagation"
    ],
    "loss_functions": [
        r"loss\s*function", r"cost\s*function", r"mse", r"mean\s*squared",
        r"cross[\-\s]*entropy", r"error\s*function"
    ],
    "probability": [
        r"bayes", r"probability", r"conditional", r"prior", r"posterior",
        r"likelihood", r"naive\s*bayes"
    ],
    "linear_algebra": [
        r"matrix", r"vector", r"transpose", r"inverse", r"dot\s*product",
        r"eigenvalue", r"linear\s*regression"
    ],
    "derivatives": [
        r"derivative", r"partial\s*derivative", r"differentiate",
        r"calculus", r"slope", r"rate\s*of\s*change"
    ],
    "neural_networks": [
        r"activation", r"sigmoid", r"relu", r"softmax", r"weights",
        r"bias", r"neuron", r"layer"
    ]
}


MATH_AGENT_PROMPT = """You are a mathematical reasoning specialist for COMP 237: Introduction to AI.
Your role is to make AI mathematics accessible, intuitive, and memorable.

## Your Core Capabilities:

### 1. Step-by-Step Derivations
- Show EVERY step of mathematical proofs
- Use LaTeX notation for clarity (wrap in $...$ for inline, $$...$$ for display)
- Explain the "why" behind each step, not just the "what"
- Connect each step to the previous one explicitly

### 2. Visual Intuition FIRST
- ALWAYS start with a geometric or visual explanation
- Use analogies that stick (hill climbing, error surfaces, probability as area)
- Describe what the math "looks like" before the formulas
- Help students build mental models

### 3. Practice Generation
- After explaining, provide a scaffolded practice problem
- Make the practice problem slightly simpler than the explanation
- Include hints if the concept is difficult

## Common COMP 237 Math Topics:

### Gradient Descent
- The "hiker in fog" analogy: finding the valley
- Learning rate = step size
- Key formula: $\\theta_{{new}} = \\theta_{{old}} - \\alpha \\nabla J(\\theta)$

### Backpropagation  
- The "chain of responsibility" analogy
- Error flows backward through the network
- Chain rule makes it possible: $\\frac{{\\partial L}}{{\\partial w}} = \\frac{{\\partial L}}{{\\partial a}} \\cdot \\frac{{\\partial a}}{{\\partial z}} \\cdot \\frac{{\\partial z}}{{\\partial w}}$

### Loss Functions
- MSE: Average squared distance from the target
- Cross-Entropy: How "surprised" we are by wrong predictions
- Key insight: Loss tells us "how wrong" we are

### Probability (Bayes)
- Prior: What we believed before seeing evidence
- Likelihood: How likely is the evidence given our belief
- Posterior: Updated belief after seeing evidence
- Formula: $P(H|E) = \\frac{{P(E|H) \\cdot P(H)}}{{P(E)}}$

## Response Format:

<thinking>
[Identify: What specific mathematical concept is being asked about?]
[Plan: What's the best sequence of steps to explain this?]
[Intuition: What visual/geometric analogy will make this click?]
</thinking>

### 🎯 The Intuition

[Visual/geometric explanation that builds mental model]
[Use an analogy that's memorable and relatable]

### 📐 The Mathematics

**Step 1:** [First step with LaTeX and explanation]
$$
[formula]
$$
*Why this step:* [explanation]

**Step 2:** [Second step]
$$
[formula]
$$
*Why this step:* [explanation]

[Continue for all steps...]

### 💡 Key Insight

[The "aha" moment - what should really stick with the student]

### ✏️ Practice Problem

[A simpler version of the problem for the student to try]

<hints>
[Scaffolded hints if they get stuck]
</hints>

## Important Rules:
1. ALWAYS start with intuition, THEN move to formulas
2. Use correct LaTeX notation (inline: $...$, display: $$...$$)
3. Explain WHY each step happens, not just WHAT happens
4. Connect to course materials and cite sources when available
5. Be patient - math anxiety is real, and you're helping overcome it

## Retrieved Course Context:
{context}

## Student's Math Question:
{query}

## Detected Topic: {topic}
"""


def detect_math_topic(query: str) -> str:
    """
    Detect the specific math topic from the query
    
    Returns the most likely topic or 'general_math'
    """
    query_lower = query.lower()
    
    topic_scores = {}
    for topic, patterns in MATH_TOPICS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, query_lower):
                score += 1
        if score > 0:
            topic_scores[topic] = score
    
    if topic_scores:
        return max(topic_scores, key=topic_scores.get)
    
    return "general_math"


def create_derivation_structure(
    concept: str,
    steps: List[Dict],
    intuition: str,
    key_insight: str
) -> MathDerivation:
    """
    Create a structured MathDerivation object
    """
    return MathDerivation(
        concept=concept,
        intuition=intuition,
        steps=steps,
        key_insight=key_insight,
        practice_problem=None  # Will be filled by the model
    )


def math_agent_node(state: AgentState) -> Dict:
    """
    Math Agent node for LangGraph
    
    Specializes in mathematical explanations with step-by-step derivations
    """
    logger.info("🔢 Math Agent: Processing mathematical query")
    start_time = time.time()
    
    query = state.get("query", "")
    retrieved_context = state.get("retrieved_context", [])
    
    # Create observation for tracing
    observation = None
    trace_id = state.get("trace_id")
    if trace_id:
        from app.observability.langfuse_client import get_langfuse_client
        client = get_langfuse_client()
        if client:
            try:
                observation = client.start_span(
                    trace_context={"trace_id": trace_id},
                    name="math_reasoning_agent",
                    input={"query": query},
                    metadata={
                        "component": "math_agent",
                        "specialization": "ai_mathematics"
                    }
                )
            except Exception as e:
                logger.warning(f"Could not create math observation: {e}")
    
    # Detect the specific math topic
    math_topic = detect_math_topic(query)
    logger.info(f"🔢 Math Agent: Detected topic '{math_topic}'")
    
    # Build context from RAG results
    context_parts = []
    for doc in retrieved_context[:5]:
        content = doc.get("content") or doc.get("text") or doc.get("page_content", "")
        source = doc.get("source_file") or doc.get("metadata", {}).get("source_file", "")
        context_parts.append(f"[From {source}]\n{content}")
    
    context_str = "\n\n---\n\n".join(context_parts) if context_parts else "No course materials retrieved."
    
    # Build the prompt
    prompt = MATH_AGENT_PROMPT.format(
        context=context_str,
        query=query,
        topic=math_topic.replace("_", " ").title()
    )
    
    # Get the model - use Gemini Flash for math (good at reasoning)
    supervisor = Supervisor()
    model = supervisor.get_model("gemini-flash")
    
    try:
        response = model.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Create a structured derivation object for state
        math_derivation = MathDerivation(
            concept=math_topic,
            intuition="",  # Would be extracted from response
            steps=[],  # Would be parsed from response
            key_insight="",  # Would be extracted from response
            practice_problem=None
        )
        
        logger.info(f"🔢 Math Agent: Generated explanation for '{math_topic}'")
        
    except Exception as e:
        logger.error(f"Error in math agent: {e}")
        response_text = f"I'd be happy to help with the mathematics of {math_topic.replace('_', ' ')}. Could you be more specific about what aspect you'd like me to explain?"
        math_derivation = None
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000
    
    # Update observation
    if observation:
        update_observation_with_usage(
            observation,
            output_data={
                "math_topic": math_topic,
                "response_length": len(response_text),
                "response_preview": response_text[:200] + "..."
            },
            level="DEFAULT",
            latency_seconds=processing_time / 1000.0
        )
        observation.end()
    
    # Update processing times
    processing_times = state.get("processing_times", {}) or {}
    processing_times["math_agent"] = processing_time
    
    logger.info(f"🔢 Math Agent: Completed in {processing_time:.1f}ms")
    
    return {
        "response": response_text,
        "math_explanation": response_text,
        "math_derivation": math_derivation,
        "processing_times": processing_times
    }


class MathAgent:
    """
    Class-based Math Agent for external use
    """
    
    def __init__(self):
        self.supervisor = Supervisor()
    
    def detect_topic(self, query: str) -> str:
        """Detect the math topic from a query"""
        return detect_math_topic(query)
    
    def is_math_query(self, query: str) -> bool:
        """Check if a query is math-related"""
        topic = detect_math_topic(query)
        return topic != "general_math"
    
    def get_topic_primer(self, topic: str) -> str:
        """Get a brief primer on a math topic"""
        primers = {
            "gradient_descent": "Gradient descent is an optimization algorithm that iteratively adjusts parameters to minimize a function.",
            "backpropagation": "Backpropagation is the algorithm that calculates gradients by propagating errors backward through a neural network.",
            "loss_functions": "Loss functions measure how far our predictions are from the actual values - the lower the better.",
            "probability": "Probability in ML helps us quantify uncertainty and make predictions under incomplete information.",
            "linear_algebra": "Linear algebra provides the mathematical foundation for transforming and manipulating data in ML.",
            "derivatives": "Derivatives tell us the rate of change - essential for understanding how to adjust model parameters.",
            "neural_networks": "Neural networks are composed of layers of interconnected nodes that learn to transform inputs into outputs."
        }
        return primers.get(topic, "This is a fundamental concept in AI and machine learning.")
    
    def generate_practice_problem(self, topic: str, difficulty: str = "medium") -> dict:
        """Generate a practice problem for a topic"""
        problems = {
            "gradient_descent": {
                "easy": "If $\\theta = 5$ and the gradient is $2$, what is the new $\\theta$ with learning rate $\\alpha = 0.1$?",
                "medium": "Starting at $\\theta = 10$, apply 3 steps of gradient descent with $\\alpha = 0.5$ where $\\nabla J = 2\\theta$.",
                "hard": "Derive the gradient descent update rule for linear regression with MSE loss."
            },
            "backpropagation": {
                "easy": "If $\\frac{\\partial L}{\\partial a} = 2$ and $\\frac{\\partial a}{\\partial z} = 0.5$, what is $\\frac{\\partial L}{\\partial z}$?",
                "medium": "Calculate the gradient for a single neuron with sigmoid activation.",
                "hard": "Derive the full backpropagation equations for a 2-layer neural network."
            },
            "probability": {
                "easy": "If P(Rain) = 0.3, what is P(No Rain)?",
                "medium": "Apply Bayes' theorem: P(Disease) = 0.01, P(Positive|Disease) = 0.95, P(Positive|No Disease) = 0.05. What is P(Disease|Positive)?",
                "hard": "Derive the Naive Bayes classifier for text classification."
            }
        }
        
        topic_problems = problems.get(topic, {"medium": "Practice with the concepts from this topic."})
        return {
            "problem": topic_problems.get(difficulty, topic_problems.get("medium")),
            "topic": topic,
            "difficulty": difficulty
        }
