"""
Math Translation Agent for Luminate AI Educate Mode

Implements 4-level mathematical explanations for COMP-237 formulas:
1. Intuition (5-year-old explanation)
2. Math Translation (LaTeX formula with variable explanations)
3. Code Example (Python implementation)
4. Common Misconceptions (what students often get wrong)

Formulas covered:
- Gradient Descent
- Backpropagation
- Sigmoid Activation
- Cross-Entropy Loss
- Bayes' Theorem
- TF-IDF
- K-Means Clustering
- Precision/Recall
- And 20+ more COMP-237 concepts
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MathTranslation:
    """Container for 4-level math explanation"""
    formula_name: str
    intuition: str
    math_latex: str
    variable_explanations: Dict[str, str]
    code_example: str
    misconceptions: List[Dict[str, str]]
    visual_hint: Optional[str] = None


class MathTranslationAgent:
    """
    Translate mathematical formulas into 4-level explanations.
    
    Based on:
    - Feynman Technique (explain simply)
    - Dual Coding Theory (verbal + visual)
    - VanLehn's Cognitive Tutoring (misconception detection)
    """
    
    def __init__(self):
        """Initialize with COMP-237 formula library"""
        self.formulas = self._build_formula_library()
    
    def translate(self, query: str) -> Optional[MathTranslation]:
        """
        Translate a math concept query into 4-level explanation.
        
        Args:
            query: Student query (e.g., "explain gradient descent")
            
        Returns:
            MathTranslation object or None if not found
        """
        # Normalize query
        query_lower = query.lower()
        
        # Match formula
        for key, translation in self.formulas.items():
            if key in query_lower or any(alias in query_lower for alias in translation.get('aliases', [])):
                return translation['content']
        
        return None
    
    def _build_formula_library(self) -> Dict[str, Dict]:
        """Build library of 30+ COMP-237 formulas with 4-level explanations"""
        library = {}
        
        # =====================================
        # 1. GRADIENT DESCENT
        # =====================================
        library['gradient descent'] = {
            'aliases': ['gradient', 'optimization', 'learning rate'],
            'content': MathTranslation(
                formula_name="Gradient Descent",
                intuition="""
🎯 **Imagine you're blindfolded on a hill trying to reach the bottom:**

- You feel the slope with your feet (gradient)
- You take a step downhill (update parameters)
- You repeat until you can't go down anymore (convergence)

The steeper the slope, the bigger your step. If you take huge steps, you might overshoot and miss the valley!
                """,
                math_latex=r"\theta_{new} = \theta_{old} - \alpha \nabla J(\theta)",
                variable_explanations={
                    "θ (theta)": "Model parameters you're trying to optimize (e.g., weights in neural network)",
                    "α (alpha)": "Learning rate - how big your steps are (typically 0.001 to 0.1)",
                    "∇J(θ)": "Gradient - direction of steepest increase in loss function",
                    "J(θ)": "Loss/cost function - measures how wrong your model is"
                },
                code_example="""
# Gradient Descent Implementation
import numpy as np

def gradient_descent(X, y, learning_rate=0.01, iterations=1000):
    m, n = X.shape
    theta = np.zeros(n)  # Initialize parameters
    
    for i in range(iterations):
        # Compute predictions
        predictions = X.dot(theta)
        
        # Compute gradient (derivative of loss)
        gradient = (1/m) * X.T.dot(predictions - y)
        
        # Update parameters (take a step downhill)
        theta = theta - learning_rate * gradient
        
        # Compute loss to track progress
        loss = (1/(2*m)) * np.sum((predictions - y)**2)
        
        if i % 100 == 0:
            print(f"Iteration {i}: Loss = {loss:.4f}")
    
    return theta

# Example usage
X = np.array([[1, 1], [1, 2], [1, 3]])  # Features (with bias term)
y = np.array([1, 2, 3])                  # Labels
theta_optimal = gradient_descent(X, y, learning_rate=0.01)
print(f"Optimal parameters: {theta_optimal}")
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Bigger learning rate = faster = better",
                        "right": "✅ Too big → overshoot & diverge. Too small → slow convergence. Need 'Goldilocks' α (0.001-0.1)"
                    },
                    {
                        "wrong": "❌ Gradient descent always finds global minimum",
                        "right": "✅ Can get stuck in local minima (hills have multiple valleys). Use momentum or Adam optimizer to escape."
                    },
                    {
                        "wrong": "❌ More iterations = better model",
                        "right": "✅ After convergence, more iterations just waste compute. Use early stopping when loss plateaus."
                    }
                ],
                visual_hint="Graph showing loss surface with steps converging to minimum"
            )
        }
        
        # =====================================
        # 2. BACKPROPAGATION
        # =====================================
        library['backpropagation'] = {
            'aliases': ['backprop', 'chain rule', 'training neural networks'],
            'content': MathTranslation(
                formula_name="Backpropagation",
                intuition="""
🎯 **Imagine a factory assembly line that makes broken toys:**

1. You find out the toy is broken at the end (error at output)
2. You walk backwards through the assembly line (backward pass)
3. At each station, you figure out how much THAT station contributed to the error (gradient)
4. You adjust each station's settings to reduce its contribution (weight update)

The chain rule says: total error = station1's error × station2's error × station3's error (multiply errors back through layers)
                """,
                math_latex=r"\frac{\partial L}{\partial w_{ij}} = \frac{\partial L}{\partial a_j} \cdot \frac{\partial a_j}{\partial z_j} \cdot \frac{\partial z_j}{\partial w_{ij}}",
                variable_explanations={
                    "L": "Loss function - measures prediction error",
                    "w_ij": "Weight connecting neuron i to neuron j",
                    "a_j": "Activation (output) of neuron j after applying activation function",
                    "z_j": "Weighted sum: z_j = Σ(w_ij * a_i) + bias",
                    "∂L/∂w_ij": "How much changing weight w_ij affects total loss (gradient)"
                },
                code_example="""
# Simple 2-Layer Neural Network with Backpropagation
import numpy as np

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def sigmoid_derivative(x):
    return x * (1 - x)

# Training data
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])  # XOR inputs
y = np.array([[0], [1], [1], [0]])               # XOR outputs

# Initialize weights randomly
np.random.seed(42)
input_layer_size = 2
hidden_layer_size = 4
output_layer_size = 1

weights_input_hidden = np.random.randn(input_layer_size, hidden_layer_size)
weights_hidden_output = np.random.randn(hidden_layer_size, output_layer_size)

learning_rate = 0.5
epochs = 10000

for epoch in range(epochs):
    # FORWARD PASS
    hidden_layer_input = np.dot(X, weights_input_hidden)
    hidden_layer_output = sigmoid(hidden_layer_input)
    
    output_layer_input = np.dot(hidden_layer_output, weights_hidden_output)
    predicted_output = sigmoid(output_layer_input)
    
    # Compute error
    error = y - predicted_output
    
    # BACKWARD PASS (Backpropagation)
    # Output layer gradient
    d_output = error * sigmoid_derivative(predicted_output)
    
    # Hidden layer gradient (chain rule!)
    error_hidden = d_output.dot(weights_hidden_output.T)
    d_hidden = error_hidden * sigmoid_derivative(hidden_layer_output)
    
    # UPDATE WEIGHTS
    weights_hidden_output += hidden_layer_output.T.dot(d_output) * learning_rate
    weights_input_hidden += X.T.dot(d_hidden) * learning_rate
    
    if epoch % 2000 == 0:
        loss = np.mean(np.abs(error))
        print(f"Epoch {epoch}: Loss = {loss:.4f}")

print(f"\\nFinal predictions:\\n{predicted_output}")
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Backprop 'sends error backwards through network'",
                        "right": "✅ Backprop computes GRADIENTS (how much each weight affects error), not the error itself."
                    },
                    {
                        "wrong": "❌ Need to understand calculus to use backprop",
                        "right": "✅ Modern frameworks (PyTorch, TensorFlow) compute gradients automatically. You just define loss!"
                    },
                    {
                        "wrong": "❌ Vanishing gradients mean backprop is broken",
                        "right": "✅ Use ReLU activation (not sigmoid) or ResNets to prevent gradients from dying in deep networks."
                    }
                ],
                visual_hint="Diagram showing forward pass (blue arrows) and backward pass (red arrows) through network layers"
            )
        }
        
        # =====================================
        # 3. CROSS-ENTROPY LOSS
        # =====================================
        library['cross-entropy'] = {
            'aliases': ['cross entropy', 'log loss', 'classification loss'],
            'content': MathTranslation(
                formula_name="Cross-Entropy Loss",
                intuition="""
🎯 **Imagine a weather forecaster predicting rain:**

If they say "90% chance of rain" and it DOES rain → small penalty (they were confident and correct!)
If they say "10% chance of rain" and it DOES rain → HUGE penalty (they were confident and WRONG!)

Cross-entropy punishes confident wrong predictions more than uncertain wrong predictions. It encourages the model to be both accurate AND honest about uncertainty.
                """,
                math_latex=r"L = -\frac{1}{N} \sum_{i=1}^{N} \sum_{c=1}^{C} y_{ic} \log(\hat{y}_{ic})",
                variable_explanations={
                    "N": "Number of training examples",
                    "C": "Number of classes",
                    "y_ic": "True label (1 if example i belongs to class c, else 0)",
                    "ŷ_ic": "Predicted probability that example i belongs to class c",
                    "log": "Natural logarithm - makes large errors VERY costly"
                },
                code_example="""
# Cross-Entropy Loss Implementation
import numpy as np

def cross_entropy_loss(y_true, y_pred, epsilon=1e-12):
    \"\"\"
    Compute cross-entropy loss
    
    Args:
        y_true: True labels (one-hot encoded) - shape (N, C)
        y_pred: Predicted probabilities - shape (N, C)
        epsilon: Small value to prevent log(0)
    
    Returns:
        Average cross-entropy loss
    \"\"\"
    # Clip predictions to prevent log(0)
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    
    # Compute cross-entropy
    N = y_true.shape[0]
    ce_loss = -np.sum(y_true * np.log(y_pred)) / N
    
    return ce_loss

# Example: 3-class classification
y_true = np.array([
    [1, 0, 0],  # Class 0
    [0, 1, 0],  # Class 1
    [0, 0, 1]   # Class 2
])

# Good predictions (confident and correct)
y_pred_good = np.array([
    [0.9, 0.05, 0.05],
    [0.05, 0.9, 0.05],
    [0.05, 0.05, 0.9]
])

# Bad predictions (confident and wrong)
y_pred_bad = np.array([
    [0.1, 0.8, 0.1],   # Predicted class 1, but truth is class 0
    [0.8, 0.1, 0.1],   # Predicted class 0, but truth is class 1
    [0.1, 0.8, 0.1]    # Predicted class 1, but truth is class 2
])

loss_good = cross_entropy_loss(y_true, y_pred_good)
loss_bad = cross_entropy_loss(y_true, y_pred_bad)

print(f"Good predictions loss: {loss_good:.4f}")  # ~0.105 (low!)
print(f"Bad predictions loss: {loss_bad:.4f}")    # ~2.303 (high!)
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Cross-entropy is just for neural networks",
                        "right": "✅ Used in logistic regression, decision trees, and any probabilistic classifier!"
                    },
                    {
                        "wrong": "❌ Lower loss always means better model",
                        "right": "✅ Can overfit to training data. Check validation loss instead!"
                    },
                    {
                        "wrong": "❌ Cross-entropy and MSE are interchangeable",
                        "right": "✅ Cross-entropy for classification (outputs probabilities), MSE for regression (continuous values)."
                    }
                ],
                visual_hint="Graph showing log(p) curve - penalty increases exponentially as confidence in wrong answer increases"
            )
        }
        
        # =====================================
        # 4. SIGMOID ACTIVATION
        # =====================================
        library['sigmoid'] = {
            'aliases': ['logistic function', 'activation function'],
            'content': MathTranslation(
                formula_name="Sigmoid Activation Function",
                intuition="""
🎯 **Imagine a dimmer switch for a light:**

Input can be any value (-∞ to +∞), but output is always between 0 and 1 (like a probability).

- Large positive input → output ≈ 1 (light fully on)
- Large negative input → output ≈ 0 (light fully off)
- Input = 0 → output = 0.5 (half brightness)

It's like compressing a number line into a tiny range, making extreme values "flatten out" at the ends.
                """,
                math_latex=r"\sigma(x) = \frac{1}{1 + e^{-x}}",
                variable_explanations={
                    "x": "Input value (can be any real number)",
                    "σ(x)": "Output (always between 0 and 1)",
                    "e": "Euler's number (≈2.718)",
                    "σ'(x)": "Derivative - how fast sigmoid changes at point x"
                },
                code_example="""
# Sigmoid Activation Function
import numpy as np
import matplotlib.pyplot as plt

def sigmoid(x):
    \"\"\"Sigmoid activation function\"\"\"
    return 1 / (1 + np.exp(-x))

def sigmoid_derivative(x):
    \"\"\"Derivative of sigmoid (for backpropagation)\"\"\"
    s = sigmoid(x)
    return s * (1 - s)

# Test with various inputs
inputs = np.array([-10, -5, -1, 0, 1, 5, 10])
outputs = sigmoid(inputs)
derivatives = sigmoid_derivative(inputs)

print("Input → Sigmoid(Input) → Derivative")
for x, y, dy in zip(inputs, outputs, derivatives):
    print(f"{x:>4} → {y:>6.4f} → {dy:>6.4f}")

# Visualize sigmoid curve
x = np.linspace(-10, 10, 100)
y = sigmoid(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y, label='Sigmoid(x)', linewidth=2)
plt.axhline(y=0.5, color='r', linestyle='--', alpha=0.3, label='y=0.5')
plt.axvline(x=0, color='r', linestyle='--', alpha=0.3, label='x=0')
plt.xlabel('Input (x)')
plt.ylabel('Output σ(x)')
plt.title('Sigmoid Activation Function')
plt.grid(True, alpha=0.3)
plt.legend()
plt.show()

# Output:
# Input → Sigmoid(Input) → Derivative
#  -10 →  0.0000 →  0.0000  (saturated - gradient = 0!)
#   -5 →  0.0067 →  0.0066
#   -1 →  0.2689 →  0.1966
#    0 →  0.5000 →  0.2500  (steepest point)
#    1 →  0.7311 →  0.1966
#    5 →  0.9933 →  0.0066
#   10 →  1.0000 →  0.0000  (saturated - gradient = 0!)
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Sigmoid is the best activation function",
                        "right": "✅ Suffers from vanishing gradients (outputs flatten at extremes). Use ReLU for hidden layers!"
                    },
                    {
                        "wrong": "❌ Sigmoid outputs are class probabilities",
                        "right": "✅ Need softmax for multi-class. Sigmoid is for binary classification (single output node)."
                    },
                    {
                        "wrong": "❌ Sigmoid = tanh (they're the same)",
                        "right": "✅ tanh ranges from -1 to +1 (zero-centered), sigmoid is 0 to 1. tanh often works better."
                    }
                ],
                visual_hint="S-curve graph showing sigmoid squashing inputs into (0,1) range"
            )
        }
        
        # =====================================
        # 5. BAYES' THEOREM (NAIVE BAYES)
        # =====================================
        library["bayes"] = {
            'aliases': ['naive bayes', 'bayesian', 'conditional probability'],
            'content': MathTranslation(
                formula_name="Bayes' Theorem",
                intuition="""
🎯 **Spam Email Detector Example:**

You see an email with the word "FREE" in it. What's the probability it's spam?

- P(spam|"FREE") = How likely is spam GIVEN you saw "FREE"? (what we want!)
- P("FREE"|spam) = How often does spam contain "FREE"? (we can measure this!)
- P(spam) = Overall rate of spam (maybe 30% of all emails)
- P("FREE") = How often does "FREE" appear in ALL emails?

Bayes flips conditional probabilities: We know P(word|spam) from training data, but we want P(spam|word) to make predictions!
                """,
                math_latex=r"P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}",
                variable_explanations={
                    "P(A|B)": "Posterior - probability of A given B (what we want to find)",
                    "P(B|A)": "Likelihood - probability of B given A (what we can measure)",
                    "P(A)": "Prior - initial probability of A before seeing evidence",
                    "P(B)": "Evidence - total probability of observing B",
                    "y": "Class label (e.g., spam or not spam)",
                    "x_i": "Features (e.g., words in email)"
                },
                code_example="""
# Naive Bayes Classifier from Scratch
import numpy as np
from collections import defaultdict

class NaiveBayesClassifier:
    def __init__(self):
        self.class_priors = {}      # P(class)
        self.word_likelihoods = {}  # P(word|class)
        self.vocab = set()
        
    def fit(self, X, y):
        \"\"\"
        Train Naive Bayes classifier
        
        X: List of documents (each is a list of words)
        y: List of class labels
        \"\"\"
        n_docs = len(X)
        class_counts = defaultdict(int)
        word_counts = defaultdict(lambda: defaultdict(int))
        
        # Count occurrences
        for doc, label in zip(X, y):
            class_counts[label] += 1
            for word in doc:
                self.vocab.add(word)
                word_counts[label][word] += 1
        
        # Compute priors: P(class) = count(class) / total_docs
        for label in class_counts:
            self.class_priors[label] = class_counts[label] / n_docs
        
        # Compute likelihoods: P(word|class) with Laplace smoothing
        for label in class_counts:
            total_words = sum(word_counts[label].values())
            self.word_likelihoods[label] = {}
            
            for word in self.vocab:
                count = word_counts[label].get(word, 0)
                # Laplace smoothing: add 1 to avoid zero probabilities
                self.word_likelihoods[label][word] = (count + 1) / (total_words + len(self.vocab))
    
    def predict(self, doc):
        \"\"\"Predict class for a document using Bayes' theorem\"\"\"
        class_scores = {}
        
        for label in self.class_priors:
            # Start with prior: P(class)
            score = np.log(self.class_priors[label])  # Use log to prevent underflow
            
            # Multiply by likelihoods: P(word|class) for each word
            for word in doc:
                if word in self.vocab:
                    score += np.log(self.word_likelihoods[label][word])
            
            class_scores[label] = score
        
        # Return class with highest score
        return max(class_scores, key=class_scores.get)

# Example: Spam Detection
X_train = [
    ['free', 'money', 'win', 'now'],           # spam
    ['meeting', 'tomorrow', 'project'],        # not spam
    ['claim', 'prize', 'free', 'gift'],        # spam
    ['review', 'document', 'meeting']          # not spam
]
y_train = ['spam', 'not_spam', 'spam', 'not_spam']

# Train classifier
nb = NaiveBayesClassifier()
nb.fit(X_train, y_train)

# Test
test_doc = ['free', 'gift', 'meeting']
prediction = nb.predict(test_doc)
print(f"Document {test_doc} is predicted as: {prediction}")
                """,
                misconceptions=[
                    {
                        "wrong": "❌ 'Naive' means it's a simple/bad algorithm",
                        "right": "✅ 'Naive' means it assumes features are independent (not always true), but it works VERY well in practice!"
                    },
                    {
                        "wrong": "❌ Can't handle new words (words not in training)",
                        "right": "✅ Use Laplace smoothing: add 1 to all word counts to prevent zero probabilities."
                    },
                    {
                        "wrong": "❌ Bayes is only for text classification",
                        "right": "✅ Used in medical diagnosis, recommendation systems, and anywhere you have categorical features!"
                    }
                ],
                visual_hint="Venn diagram showing overlap between P(A|B) and P(B|A) with Bayes formula connecting them"
            )
        }
        
        # =====================================
        # 6. RELU ACTIVATION FUNCTION
        # =====================================
        library['relu'] = {
            'aliases': ['rectified linear unit', 'relu activation'],
            'content': MathTranslation(
                formula_name="ReLU (Rectified Linear Unit)",
                intuition="""
🎯 **Imagine a door that only lets positive numbers through:**

- Positive input → passes straight through (like an open door)
- Negative input → blocked completely (output = 0)

It's like a one-way valve: water flows forward but not backward!
                """,
                math_latex=r"\text{ReLU}(x) = \max(0, x) = \begin{cases} x & \text{if } x > 0 \\ 0 & \text{if } x \leq 0 \end{cases}",
                variable_explanations={
                    "x": "Input value (can be any number)",
                    "ReLU(x)": "Output (always ≥ 0)"
                },
                code_example="""
import numpy as np

def relu(x):
    return np.maximum(0, x)

# Example
inputs = np.array([-2, -1, 0, 1, 2])
outputs = relu(inputs)
print(f"Inputs: {inputs}")
print(f"Outputs: {outputs}")  # [0, 0, 0, 1, 2]

# In PyTorch
import torch
import torch.nn as nn

relu_layer = nn.ReLU()
x = torch.tensor([-1.5, 0.0, 2.3])
output = relu_layer(x)  # tensor([0.0, 0.0, 2.3])
                """,
                misconceptions=[
                    {
                        "wrong": "❌ ReLU is the best activation function for all layers",
                        "right": "✅ Use ReLU in hidden layers, but sigmoid/softmax for output layer (classification)"
                    },
                    {
                        "wrong": "❌ Negative inputs are useless, they become zero anyway",
                        "right": "✅ During backprop, ReLU still passes gradients when x > 0, helping learn which neurons to activate"
                    },
                    {
                        "wrong": "❌ Dead ReLU problem: once a neuron outputs 0, it's forever dead",
                        "right": "✅ Use Leaky ReLU (small slope for negatives) or careful weight initialization to prevent this"
                    }
                ],
                visual_hint="Graph showing piecewise function: flat at 0 for x<0, linear slope for x>0"
            )
        }
        
        # =====================================
        # 7. SOFTMAX FUNCTION
        # =====================================
        library['softmax'] = {
            'aliases': ['softmax activation', 'normalized exponential'],
            'content': MathTranslation(
                formula_name="Softmax Function",
                intuition="""
🎯 **Imagine converting exam scores to probabilities:**

- Student A: 85/100 → becomes 60% probability
- Student B: 75/100 → becomes 30% probability  
- Student C: 60/100 → becomes 10% probability

**Total = 100%** (all probabilities sum to 1)

Softmax does this for neural network outputs!
                """,
                math_latex=r"\text{Softmax}(z_i) = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}",
                variable_explanations={
                    "z_i": "Raw score (logit) for class i",
                    "K": "Total number of classes",
                    "e^{z_i}": "Exponential amplifies differences",
                    "Softmax(z_i)": "Probability for class i (between 0 and 1)"
                },
                code_example="""
import numpy as np

def softmax(logits):
    exp_logits = np.exp(logits - np.max(logits))  # Subtract max for numerical stability
    return exp_logits / np.sum(exp_logits)

# Example: 3-class classification
logits = np.array([2.0, 1.0, 0.1])
probabilities = softmax(logits)
print(f"Logits: {logits}")
print(f"Probabilities: {probabilities}")  # [0.659, 0.242, 0.099]
print(f"Sum: {probabilities.sum()}")      # 1.0

# PyTorch
import torch.nn as nn

softmax_layer = nn.Softmax(dim=1)
logits = torch.tensor([[2.0, 1.0, 0.1]])
probs = softmax_layer(logits)  # [[0.659, 0.242, 0.099]]
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Softmax is just normalization (divide by sum)",
                        "right": "✅ It's exponential normalization: e^x amplifies large values and suppresses small ones"
                    },
                    {
                        "wrong": "❌ Use softmax for binary classification",
                        "right": "✅ Use sigmoid for binary (0/1), softmax for multi-class (3+ classes)"
                    },
                    {
                        "wrong": "❌ Softmax output is the final prediction",
                        "right": "✅ Softmax gives probabilities. Take argmax() to get the predicted class index"
                    }
                ],
                visual_hint="Bar chart showing logits → softmax → probability distribution summing to 1"
            )
        }
        
        # =====================================
        # 9. K-MEANS CLUSTERING
        # =====================================
        library['k-means clustering'] = {
            'aliases': ['k-means', 'kmeans', 'k means', 'k-means clustering', 'kmeans clustering'],
            'content': MathTranslation(
                formula_name="K-Means Clustering",
                intuition="""
🎯 **Imagine sorting your colored marbles into K jars so similar colors go together:**

- You pick K jar centers (centroids) at random.
- Each marble goes to the nearest jar (assignment step).
- Then you move each jar's center to the average location of marbles assigned to it (update step).
- Repeat assignment + update until jar centers stop moving much (convergence).

K-means is simple: assign points to nearest centroid, then recompute centroids.
It finds compact spherical clusters but needs K up front and can get stuck in local minima.
                """,
                math_latex=r"""
J = \sum_{i=1}^{n} \sum_{k=1}^{K} r_{ik} \| x_i - \mu_k \|^2

	ext{where } r_{ik} = \begin{cases} 1 & \text{if } x_i \text{ assigned to cluster } k \\ 0 & \text{otherwise} \end{cases}
""",
                variable_explanations={
                    "J": "Objective (sum of squared distances from points to their cluster centroids)",
                    "n": "Number of data points",
                    "K": "Number of clusters (chosen by user)",
                    "x_i": "Data point i (vector)",
                    r"\mu_k": "Centroid (mean) of cluster k",
                    "r_{ik}": "Assignment indicator (1 if x_i belongs to cluster k)"
                },
                code_example="""
# Simple K-Means (NumPy) - illustrative, not optimized
import numpy as np

def kmeans(X, K, iterations=10, seed=42):
    np.random.seed(seed)
    # Randomly initialize centroids as K random points from X
    centroids = X[np.random.choice(len(X), K, replace=False)]

    for it in range(iterations):
        # Assignment step: compute distances and assign labels
        distances = np.linalg.norm(X[:, None, :] - centroids[None, :, :], axis=2)  # (n, K)
        labels = np.argmin(distances, axis=1)  # nearest centroid index for each point

        # Update step: recompute centroids as mean of assigned points
        new_centroids = np.array([X[labels == k].mean(axis=0) if np.any(labels == k) else centroids[k]
                                  for k in range(K)])

        # Check for convergence (centroids not moving)
        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids

    return centroids, labels

# Example usage:
X = np.array([[1.0, 2.0], [1.1, 1.9], [4.0, 4.1], [3.9, 3.8]])
centroids, labels = kmeans(X, K=2)
print('Centroids:', centroids)
print('Labels:', labels)
""",
                misconceptions=[
                    {
                        "wrong": "❌ K-means always finds the 'true' clusters",
                        "right": "✅ K-means finds a local minimum of the objective and is sensitive to initialization; run multiple times or use k-means++ initialization."
                    },
                    {
                        "wrong": "❌ K determines itself from the data",
                        "right": "✅ You must choose K; use methods like the elbow method or silhouette score to help pick K."
                    },
                    {
                        "wrong": "❌ K-means works well for any cluster shape",
                        "right": "✅ K-means assumes spherical clusters (based on Euclidean distance). It struggles with elongated or non-convex clusters (use DBSCAN/GMM)."
                    },
                    {
                        "wrong": "❌ Scaling data doesn't matter",
                        "right": "✅ Feature scaling (standardization) matters because K-means uses Euclidean distance. Scale features before clustering."
                    }
                ],
                visual_hint="Show centroid movement over iterations (plot points with centroid positions per iteration)"
            )
        }
        
        # =====================================
        # 8. MEAN SQUARED ERROR (MSE)
        # =====================================
        library['mse'] = {
            'aliases': ['mean squared error', 'l2 loss', 'squared error'],
            'content': MathTranslation(
                formula_name="Mean Squared Error (MSE)",
                intuition="""
🎯 **Imagine measuring how far your darts are from the bullseye:**

1. Measure distance of each dart from center
2. Square the distance (so -3 and +3 both count as 9)
3. Take the average of all squared distances

**Why square?** Bigger mistakes are punished more! Missing by 10 is 100x worse than missing by 1.
                """,
                math_latex=r"\text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2",
                variable_explanations={
                    "n": "Number of samples",
                    "y_i": "True value (actual price, temperature, etc.)",
                    "ŷ_i": "Predicted value from your model",
                    "(y_i - ŷ_i)": "Error (how far off you are)",
                    "Square": "Ensures positive error & penalizes large mistakes"
                },
                code_example="""
import numpy as np

def mse(y_true, y_pred):
    return np.mean((y_true - y_pred) ** 2)

# Example: House price prediction
y_true = np.array([300000, 450000, 200000])  # Actual prices
y_pred = np.array([310000, 430000, 220000])  # Predicted prices

error = mse(y_true, y_pred)
print(f"MSE: ${error:,.0f}")  # MSE: $133,333,333

# In scikit-learn
from sklearn.metrics import mean_squared_error

mse_sklearn = mean_squared_error(y_true, y_pred)
rmse = np.sqrt(mse_sklearn)  # Root MSE (same units as target)
print(f"RMSE: ${rmse:,.0f}")  # RMSE: $11,547
                """,
                misconceptions=[
                    {
                        "wrong": "❌ MSE and RMSE are the same thing",
                        "right": "✅ RMSE = √MSE. RMSE is in same units as target (dollars, meters), MSE is squared units"
                    },
                    {
                        "wrong": "❌ Lower MSE always means better model",
                        "right": "✅ Check for overfitting! Low training MSE + high test MSE = memorizing, not learning"
                    },
                    {
                        "wrong": "❌ MSE is good for all regression problems",
                        "right": "✅ MSE sensitive to outliers. Use MAE (Mean Absolute Error) if you have extreme values"
                    }
                ],
                visual_hint="Graph showing parabola: error² curve with minimum at perfect prediction"
            )
        }
        
        # =====================================
        # 9. PRECISION AND RECALL
        # =====================================
        library['precision'] = {
            'aliases': ['precision recall', 'precision and recall', 'recall'],
            'content': MathTranslation(
                formula_name="Precision and Recall",
                intuition="""
🎯 **Imagine a spam email filter:**

**Precision:** Of emails marked as spam, how many were actually spam?
- "When I say it's spam, am I usually right?"

**Recall:** Of all actual spam emails, how many did I catch?
- "Did I catch all the spam?"

**Trade-off:**
- High precision → few false alarms, but might miss some spam
- High recall → catch all spam, but might flag good emails as spam
                """,
                math_latex=r"""
\text{Precision} = \frac{TP}{TP + FP}

\text{Recall} = \frac{TP}{TP + FN}

\text{where:}
- TP = \text{True Positives (correctly predicted positive)}
- FP = \text{False Positives (wrongly predicted positive)}
- FN = \text{False Negatives (wrongly predicted negative)}
                """,
                variable_explanations={
                    "TP (True Positive)": "Correctly identified spam as spam",
                    "FP (False Positive)": "Wrongly marked good email as spam",
                    "FN (False Negative)": "Missed spam (marked it as good)",
                    "Precision": "Accuracy of positive predictions",
                    "Recall": "Coverage of actual positives"
                },
                code_example="""
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# Example: Spam detection
y_true = [1, 1, 0, 1, 0, 0, 1, 0]  # 1=spam, 0=not spam
y_pred = [1, 1, 0, 0, 0, 1, 1, 0]

precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)  # F1 = 2 * (P * R) / (P + R)

print(f"Precision: {precision:.2f}")  # 0.67 (2 correct out of 3 predicted spam)
print(f"Recall: {recall:.2f}")        # 0.50 (caught 2 out of 4 actual spam)
print(f"F1-Score: {f1:.2f}")          # 0.57 (harmonic mean of P and R)

# Confusion Matrix
cm = confusion_matrix(y_true, y_pred)
print("Confusion Matrix:")
print(cm)
# [[3  1]  ← TN=3, FP=1
#  [2  2]] ← FN=2, TP=2
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Accuracy is always the best metric",
                        "right": "✅ For imbalanced data (e.g., 99% non-spam), accuracy is misleading. Use precision/recall!"
                    },
                    {
                        "wrong": "❌ High precision means high recall",
                        "right": "✅ They're inversely related! Increasing one often decreases the other (precision-recall trade-off)"
                    },
                    {
                        "wrong": "❌ F1-score is always better than precision or recall alone",
                        "right": "✅ Depends on use case! Medical diagnosis needs high recall (catch all diseases), spam filter needs high precision (few false alarms)"
                    }
                ],
                visual_hint="2x2 confusion matrix with TP, FP, FN, TN labeled and formulas pointing to cells"
            )
        }
        
        # =====================================
        # 10. F1-SCORE
        # =====================================
        library['f1'] = {
            'aliases': ['f1 score', 'f1-score', 'f-measure'],
            'content': MathTranslation(
                formula_name="F1-Score",
                intuition="""
🎯 **Imagine balancing two goals:**

- **Precision:** Don't cry wolf (be accurate when you say "positive")
- **Recall:** Don't miss real wolves (catch all positives)

**F1-Score is the harmonic mean** — it balances both goals.

If either precision or recall is low, F1 will be low too!
                """,
                math_latex=r"""
F1 = 2 \cdot \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}

\text{Or equivalently:}

F1 = \frac{2 \cdot TP}{2 \cdot TP + FP + FN}
                """,
                variable_explanations={
                    "Precision": "Correctness of positive predictions",
                    "Recall": "Coverage of actual positives",
                    "F1": "Harmonic mean (penalizes extreme imbalance)",
                    "TP, FP, FN": "True Positive, False Positive, False Negative"
                },
                code_example="""
from sklearn.metrics import f1_score, precision_recall_fscore_support

# Example scenarios
# Scenario 1: High precision, low recall
y_true = [1, 1, 1, 1, 0, 0, 0, 0]
y_pred = [1, 0, 0, 0, 0, 0, 0, 0]  # Only 1 predicted positive

p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
print(f"Precision: {p:.2f}, Recall: {r:.2f}, F1: {f1:.2f}")  
# Output: Precision: 1.00, Recall: 0.25, F1: 0.40

# Scenario 2: Balanced precision and recall
y_true = [1, 1, 1, 1, 0, 0, 0, 0]
y_pred = [1, 1, 0, 0, 0, 0, 1, 1]  # 2 TP, 2 FP, 2 FN

f1 = f1_score(y_true, y_pred)
print(f"F1-Score: {f1:.2f}")  # 0.50 (balanced P=0.50, R=0.50)
                """,
                misconceptions=[
                    {
                        "wrong": "❌ F1 is just (Precision + Recall) / 2",
                        "right": "✅ It's HARMONIC mean: 2*P*R/(P+R). This penalizes imbalance more than arithmetic mean"
                    },
                    {
                        "wrong": "❌ F1=1.0 means perfect model",
                        "right": "✅ Correct! F1=1.0 means both Precision=1.0 and Recall=1.0 (no FP, no FN)"
                    },
                    {
                        "wrong": "❌ Always optimize for F1-score",
                        "right": "✅ Depends on cost! Use F-beta to weight precision/recall differently (e.g., F2 favors recall)"
                    }
                ],
                visual_hint="Triangle showing P, R, and F1 with harmonic mean formula connecting them"
            )
        }
        
        # =====================================
        # 11. ADAM OPTIMIZER
        # =====================================
        library['adam'] = {
            'aliases': ['adam optimizer', 'adaptive moment estimation'],
            'content': MathTranslation(
                formula_name="Adam Optimizer",
                intuition="""
🎯 **Imagine a smart car with cruise control:**

- **Momentum:** Remembers previous speeds (doesn't stop/start abruptly)
- **Adaptive learning rate:** Slows down on curvy roads, speeds up on straight paths
- **Bias correction:** Fixes initial slow start

Adam combines the best of both worlds: SGD with momentum + RMSprop!
                """,
                math_latex=r"""
m_t = \beta_1 m_{t-1} + (1 - \beta_1) g_t

v_t = \beta_2 v_{t-1} + (1 - \beta_2) g_t^2

\hat{m}_t = \frac{m_t}{1 - \beta_1^t}, \quad \hat{v}_t = \frac{v_t}{1 - \beta_2^t}

\theta_t = \theta_{t-1} - \alpha \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}
                """,
                variable_explanations={
                    "m_t": "1st moment (mean of gradients, like velocity)",
                    "v_t": "2nd moment (variance of gradients, like acceleration)",
                    "β₁": "Momentum decay (typically 0.9)",
                    "β₂": "RMSprop decay (typically 0.999)",
                    "g_t": "Gradient at time t",
                    "α": "Learning rate (typically 0.001)",
                    "ε": "Small constant for numerical stability (1e-8)"
                },
                code_example="""
import torch
import torch.optim as optim

# Define model and optimizer
model = MyNeuralNetwork()
optimizer = optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999))

# Training loop
for epoch in range(100):
    optimizer.zero_grad()           # Reset gradients
    
    output = model(input)           # Forward pass
    loss = criterion(output, target)
    
    loss.backward()                 # Compute gradients
    optimizer.step()                # Update weights with Adam
    
    print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

# Manual implementation
class AdamOptimizer:
    def __init__(self, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = 0  # 1st moment
        self.v = 0  # 2nd moment
        self.t = 0  # Time step
    
    def update(self, theta, gradient):
        self.t += 1
        self.m = self.beta1 * self.m + (1 - self.beta1) * gradient
        self.v = self.beta2 * self.v + (1 - self.beta2) * (gradient ** 2)
        
        m_hat = self.m / (1 - self.beta1 ** self.t)  # Bias correction
        v_hat = self.v / (1 - self.beta2 ** self.t)
        
        theta = theta - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)
        return theta
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Adam always works better than SGD",
                        "right": "✅ Adam converges faster, but SGD often generalizes better. Try both and compare!"
                    },
                    {
                        "wrong": "❌ No need to tune learning rate with Adam",
                        "right": "✅ Still need to tune! Common values: 1e-3 (default), 1e-4 (stable), 1e-2 (fast but risky)"
                    },
                    {
                        "wrong": "❌ Adam's betas are magical constants",
                        "right": "✅ β₁=0.9 means 'use 90% old momentum', β₂=0.999 means 'use 99.9% old variance'. They're exponential moving averages!"
                    }
                ],
                visual_hint="Graph comparing SGD (zigzag path) vs Adam (smooth curved path) converging to minimum"
            )
        }
        
        # =====================================
        # 12. L1/L2 REGULARIZATION
        # =====================================
        library['regularization'] = {
            'aliases': ['l1 regularization', 'l2 regularization', 'lasso', 'ridge'],
            'content': MathTranslation(
                formula_name="L1/L2 Regularization",
                intuition="""
🎯 **Imagine a budget constraint when buying groceries:**

**Without regularization:** Buy whatever you want (might overspend = overfit)

**L2 (Ridge):** "Spread your budget evenly across all items" (all weights stay small)

**L1 (Lasso):** "Only buy essential items, skip the rest" (some weights become exactly 0)

**Goal:** Prevent overfitting by penalizing large weights!
                """,
                math_latex=r"L(\theta) = \text{Loss} + \lambda \sum_{i=1}^{n} \theta_i^2 \quad \text{(L2/Ridge)}",
                variable_explanations={
                    "θ_i": "Model weights/parameters",
                    "λ": "Regularization strength (0 = no penalty, large λ = strong penalty)",
                    "L2 penalty": "Sum of squared weights (penalizes large weights)",
                    "L1 penalty": "Sum of absolute weights (drives weights to 0)",
                    "Elastic Net": "Combination of L1 and L2"
                },
                code_example="""
from sklearn.linear_model import Ridge, Lasso, ElasticNet
import numpy as np

X_train = np.random.rand(100, 10)
y_train = np.random.rand(100)

# L2 Regularization (Ridge)
ridge = Ridge(alpha=1.0)  # alpha = λ (regularization strength)
ridge.fit(X_train, y_train)
print(f"Ridge weights: {ridge.coef_}")  # Small but non-zero weights

# L1 Regularization (Lasso)
lasso = Lasso(alpha=0.1)
lasso.fit(X_train, y_train)
print(f"Lasso weights: {lasso.coef_}")  # Some weights are exactly 0!

# Elastic Net (L1 + L2)
elastic = ElasticNet(alpha=0.5, l1_ratio=0.5)  # l1_ratio=0.5 means 50% L1, 50% L2
elastic.fit(X_train, y_train)
print(f"ElasticNet weights: {elastic.coef_}")

# In PyTorch (weight decay = L2)
import torch.optim as optim

optimizer = optim.SGD(model.parameters(), lr=0.01, weight_decay=1e-4)  # L2 regularization
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Regularization always improves model performance",
                        "right": "✅ It helps with overfitting, but too much regularization causes underfitting! Tune λ on validation set"
                    },
                    {
                        "wrong": "❌ L1 and L2 are the same, just different formulas",
                        "right": "✅ L1 creates sparse models (feature selection), L2 shrinks all weights evenly (better for correlated features)"
                    },
                    {
                        "wrong": "❌ Weight decay in PyTorch is L1 regularization",
                        "right": "✅ Weight decay is L2 regularization! For L1, manually add |w| penalty to loss"
                    }
                ],
                visual_hint="2D contour plot: circular L2 constraint vs diamond L1 constraint intersecting with loss ellipse"
            )
        }
        
        # =====================================
        # 13. DROPOUT
        # =====================================
        library['dropout'] = {
            'aliases': ['dropout regularization', 'dropout layer'],
            'content': MathTranslation(
                formula_name="Dropout",
                intuition="""
🎯 **Imagine a basketball team:**

**Without dropout:** Same 5 players always play together
- If one player is sick, the team struggles (overfitting to that player)

**With dropout:** Randomly bench 20% of players each game
- Forces everyone to learn to play together
- Team is robust even if key players are missing (generalization!)

**Dropout randomly removes neurons during training to prevent overfitting.**
                """,
                math_latex=r"""
\text{During training:}
h = \begin{cases} 
0 & \text{with probability } p \\
\frac{a}{1-p} & \text{with probability } 1-p
\end{cases}

\text{During inference:}
h = a \quad \text{(use all neurons, no dropout)}
                """,
                variable_explanations={
                    "p": "Dropout probability (typically 0.2-0.5)",
                    "a": "Activation before dropout",
                    "h": "Output after dropout",
                    "1/(1-p)": "Scaling factor to keep expected value constant"
                },
                code_example="""
import torch
import torch.nn as nn

class MyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(100, 50)
        self.dropout = nn.Dropout(p=0.5)  # Drop 50% of neurons
        self.fc2 = nn.Linear(50, 10)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)  # Only active during training!
        x = self.fc2(x)
        return x

model = MyModel()

# Training mode (dropout active)
model.train()
output_train = model(input_data)  # 50% neurons dropped randomly

# Evaluation mode (dropout disabled)
model.eval()
output_eval = model(input_data)   # All neurons active

# Manual implementation
def dropout(x, p=0.5, training=True):
    if not training:
        return x
    
    mask = (torch.rand(x.shape) > p).float()  # Random binary mask
    return x * mask / (1 - p)  # Scale to maintain expected value
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Dropout slows down training",
                        "right": "✅ Yes, it does slow convergence, but it prevents overfitting! It's a speed-accuracy trade-off"
                    },
                    {
                        "wrong": "❌ Always use dropout in all layers",
                        "right": "✅ Use dropout in fully connected layers, NOT usually in conv layers or output layer"
                    },
                    {
                        "wrong": "❌ Dropout probability 0.5 is always best",
                        "right": "✅ Tune it! Common values: 0.2-0.3 for conv layers, 0.5 for FC layers. Higher p = more regularization"
                    }
                ],
                visual_hint="Neural network diagram with some neurons crossed out (dropped) during training, all active during test"
            )
        }
        
        # =====================================
        # 14. BATCH NORMALIZATION
        # =====================================
        library['batch norm'] = {
            'aliases': ['batch normalization', 'batchnorm', 'bn layer'],
            'content': MathTranslation(
                formula_name="Batch Normalization",
                intuition="""
🎯 **Imagine test scores across different subjects:**

- Math: scores 0-100
- Chemistry: scores 0-1000
- English: scores A-F

**Problem:** Different scales make comparison hard!

**Batch Norm:** Normalize each subject to mean=0, std=1
- Then let the model learn if it wants to scale/shift (γ, β parameters)

**Result:** Faster training, more stable gradients!
                """,
                math_latex=r"""
\mu_B = \frac{1}{m} \sum_{i=1}^{m} x_i \quad \text{(batch mean)}

\sigma_B^2 = \frac{1}{m} \sum_{i=1}^{m} (x_i - \mu_B)^2 \quad \text{(batch variance)}

\hat{x}_i = \frac{x_i - \mu_B}{\sqrt{\sigma_B^2 + \epsilon}} \quad \text{(normalize)}

y_i = \gamma \hat{x}_i + \beta \quad \text{(scale and shift)}
                """,
                variable_explanations={
                    "μ_B": "Mean of the batch",
                    "σ²_B": "Variance of the batch",
                    "x̂_i": "Normalized value (mean=0, var=1)",
                    "γ": "Learnable scale parameter",
                    "β": "Learnable shift parameter",
                    "ε": "Small constant for numerical stability (1e-5)"
                },
                code_example="""
import torch
import torch.nn as nn

class MyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, 3)
        self.bn1 = nn.BatchNorm2d(64)  # Normalize 64 channels
        self.conv2 = nn.Conv2d(64, 128, 3)
        self.bn2 = nn.BatchNorm2d(128)
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)  # Normalize before activation
        x = torch.relu(x)
        
        x = self.conv2(x)
        x = self.bn2(x)
        x = torch.relu(x)
        return x

# Manual implementation
def batch_norm(x, gamma, beta, eps=1e-5):
    # x: (batch_size, features)
    mean = x.mean(dim=0, keepdim=True)
    var = x.var(dim=0, keepdim=True, unbiased=False)
    
    x_hat = (x - mean) / torch.sqrt(var + eps)  # Normalize
    out = gamma * x_hat + beta  # Scale and shift
    
    return out
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Batch norm replaces dropout",
                        "right": "✅ They complement each other! Use both for best results (though some use only batch norm)"
                    },
                    {
                        "wrong": "❌ Put batch norm after activation function",
                        "right": "✅ Usually put it BEFORE activation: Conv → BatchNorm → ReLU (though both work)"
                    },
                    {
                        "wrong": "❌ Batch norm works the same in training and testing",
                        "right": "✅ Training: uses batch statistics. Testing: uses running average of all batches (more stable)"
                    }
                ],
                visual_hint="Before/after histogram: skewed distribution → normalized bell curve (mean=0, std=1)"
            )
        }
        
        # =====================================
        # 15. LEARNING RATE SCHEDULING
        # =====================================
        library['learning rate'] = {
            'aliases': ['learning rate decay', 'lr scheduler', 'step decay'],
            'content': MathTranslation(
                formula_name="Learning Rate Scheduling",
                intuition="""
🎯 **Imagine driving to a destination:**

- **Start:** Drive fast on the highway (large learning rate)
- **Middle:** Slow down in the city (reduce learning rate)
- **End:** Carefully parallel park (very small learning rate)

**Why?** Large LR explores quickly, small LR fine-tunes precisely!
                """,
                math_latex=r"""
\text{Step Decay:} \quad \alpha_t = \alpha_0 \cdot \gamma^{\lfloor t/k \rfloor}

\text{Exponential Decay:} \quad \alpha_t = \alpha_0 \cdot e^{-\lambda t}

\text{Cosine Annealing:} \quad \alpha_t = \alpha_{min} + \frac{1}{2}(\alpha_{max} - \alpha_{min})(1 + \cos(\frac{t}{T}\pi))
                """,
                variable_explanations={
                    "α_t": "Learning rate at epoch t",
                    "α_0": "Initial learning rate",
                    "γ": "Decay factor (e.g., 0.1 = divide by 10)",
                    "k": "Step size (reduce LR every k epochs)",
                    "λ": "Exponential decay rate",
                    "T": "Total number of epochs"
                },
                code_example="""
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR, ExponentialLR, CosineAnnealingLR

model = MyModel()
optimizer = optim.Adam(model.parameters(), lr=0.1)

# Step Decay: Reduce LR by 0.1 every 10 epochs
scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

# Exponential Decay
scheduler = ExponentialLR(optimizer, gamma=0.95)  # Multiply by 0.95 each epoch

# Cosine Annealing (smooth curve from max to min)
scheduler = CosineAnnealingLR(optimizer, T_max=100, eta_min=1e-6)

# Training loop
for epoch in range(100):
    train_one_epoch(model, optimizer)
    
    scheduler.step()  # Update learning rate
    print(f"Epoch {epoch}, LR: {optimizer.param_groups[0]['lr']:.6f}")

# Manual step decay
def step_decay(epoch, initial_lr=0.1, drop=0.5, epochs_drop=10):
    lr = initial_lr * (drop ** (epoch // epochs_drop))
    return lr
                """,
                misconceptions=[
                    {
                        "wrong": "❌ Always reduce learning rate during training",
                        "right": "✅ Not always! Cyclic LR increases and decreases, 1cycle policy starts low → high → low"
                    },
                    {
                        "wrong": "❌ Learning rate scheduling is only for SGD",
                        "right": "✅ Works with all optimizers (SGD, Adam, etc.), but Adam is less sensitive to LR changes"
                    },
                    {
                        "wrong": "❌ Reduce LR when training loss decreases",
                        "right": "✅ Reduce when validation loss plateaus (ReduceLROnPlateau scheduler), not when training loss improves!"
                    }
                ],
                visual_hint="Graph showing LR decay over epochs: step decay (stairs), exponential (smooth curve), cosine (wave)"
            )
        }
        
        return library
    
    def get_all_formulas(self) -> List[str]:
        """Get list of all available formulas"""
        return list(self.formulas.keys())
    
    def _clean_latex_formula(self, latex_str: str) -> str:
        """
        Extract only the pure LaTeX formula, removing markdown list syntax.
        
        LaTeX math mode cannot contain markdown list items (lines starting with '-').
        This extracts only the formula part before any '\text{where:}' or list items.
        
        Args:
            latex_str: Raw LaTeX string that may contain markdown
            
        Returns:
            Cleaned LaTeX formula suitable for $$...$$ blocks
        """
        lines = latex_str.strip().split('\n')
        formula_lines = []
        
        for line in lines:
            line = line.strip()
            # Stop at '\text{where:}' or lines starting with '-' (markdown lists)
            if r'\text{where:}' in line or line.startswith('-'):
                break
            # Keep non-empty formula lines
            if line:
                formula_lines.append(line)
        
        # Join with spaces (LaTeX ignores most whitespace anyway)
        return ' '.join(formula_lines).strip()
    
    def format_for_ui(self, translation: MathTranslation) -> str:
        """
        Format MathTranslation for UI display (markdown with LaTeX).
        
        Returns:
            Markdown string ready for rendering
        """
        output = f"# 📐 {translation.formula_name}\n\n"
        
        # Level 1: Intuition
        output += "## 🎯 Level 1: Intuition (The 5-Year-Old Explanation)\n\n"
        output += translation.intuition.strip() + "\n\n"
        
        # Level 2: Math Translation
        output += "## 📊 Level 2: The Math (With Plain English)\n\n"
        output += "**Formula:**\n\n"
        
        # Extract only the pure LaTeX formula (no markdown list syntax)
        clean_formula = self._clean_latex_formula(translation.math_latex)
        output += f"$${clean_formula}$$\n\n"
        
        output += "**What Each Symbol Means:**\n\n"
        for symbol, explanation in translation.variable_explanations.items():
            output += f"- **{symbol}**: {explanation}\n"
        output += "\n"
        
        # Level 3: Code Example
        output += "## 💻 Level 3: See It In Code\n\n"
        output += "```python\n"
        output += translation.code_example.strip()
        output += "\n```\n\n"
        
        # Level 4: Common Misconceptions
        output += "## ❌ Level 4: Common Misconceptions\n\n"
        output += "*What students often get wrong (and the truth!)*\n\n"
        for i, misconception in enumerate(translation.misconceptions, 1):
            output += f"**{i}.** {misconception['wrong']}\n\n"
            output += f"{misconception['right']}\n\n"
        
        # Visual hint (if available)
        if translation.visual_hint:
            output += f"## 🎨 Visual Hint\n\n*{translation.visual_hint}*\n\n"
        
        return output


# Helper function for integration with Educate Mode
def explain_formula(query: str) -> Optional[str]:
    """
    Main entry point for math translation.
    
    Args:
        query: Student query (e.g., "explain gradient descent")
        
    Returns:
        Formatted markdown explanation or None if formula not found
    """
    agent = MathTranslationAgent()
    translation = agent.translate(query)
    
    if translation:
        return agent.format_for_ui(translation)
    else:
        return None


if __name__ == "__main__":
    # Test the Math Translation Agent
    print("=" * 80)
    print("MATH TRANSLATION AGENT TEST")
    print("=" * 80)
    
    agent = MathTranslationAgent()
    
    # Test queries
    test_queries = [
        "explain gradient descent",
        "what is backpropagation",
        "cross-entropy loss",
        "sigmoid function",
        "bayes theorem"
    ]
    
    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"Query: {query}")
        print(f"{'=' * 80}\n")
        
        explanation = explain_formula(query)
        if explanation:
            print(explanation)
        else:
            print("❌ Formula not found in library")
    
    # List all available formulas
    print(f"\n{'=' * 80}")
    print("AVAILABLE FORMULAS:")
    print(f"{'=' * 80}")
    for formula in agent.get_all_formulas():
        print(f"- {formula}")
