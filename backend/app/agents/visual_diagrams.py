"""
Visual Diagram Generator for COMP 237 AI Tutoring

Generates visual representations of AI/ML concepts using:
1. ASCII art diagrams for terminal/text display
2. Mermaid.js syntax for rich frontend rendering

These visuals help students understand abstract concepts.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ASCII Art Diagrams for Common Concepts
ASCII_DIAGRAMS = {
    "neural_network": """
```
    Input Layer      Hidden Layer      Output Layer
    
       (x₁) ─────────┐
              ╲      │
               ╲     ▼
       (x₂) ────────(h₁)─────────┐
              ╱      │            ╲
             ╱       │             ╲
       (x₃) ─────────┤              ────▶ (ŷ)
              ╲      │             ╱
               ╲     ▼            ╱
       (x₄) ────────(h₂)─────────┘
              ╱
             ╱
    
    Each connection has a weight (w)
    Each neuron applies: output = activation(Σ wᵢxᵢ + b)
```
""",

    "gradient_descent": """
```
    Loss
      │
      │    ╭─╮
      │   ╱   ╲
      │  ╱     ╲        Current
      │ ╱       ╲       Position
      │╱    ●────╲──────────▶ Move in direction
      │      ╲    ╲           of steepest descent
      │       ╲    ╲
      │        ╲    ╲
      │         ╲    ★ Minimum (goal)
      │          ╲
      └───────────────────────▶ Parameters (w)
      
    Step size = learning_rate × gradient
    w_new = w_old - α × ∂Loss/∂w
```
""",

    "backpropagation": """
```
    Forward Pass (→)              Backward Pass (←)
    
    Input ──▶ Hidden ──▶ Output   ∂L/∂w = ∂L/∂y × ∂y/∂w
      x        h          ŷ            ↑
      │        │          │            │
      ▼        ▼          ▼            │
    ┌───┐    ┌───┐    ┌───────┐        │
    │ w₁│───▶│ w₂│───▶│  Loss │────────┘
    └───┘    └───┘    │   L   │
                      └───────┘
                          │
                          ▼
                    Compute error
                    Propagate back
                    Update weights
    
    Chain Rule: ∂L/∂w₁ = ∂L/∂ŷ × ∂ŷ/∂h × ∂h/∂w₁
```
""",

    "classification_vs_regression": """
```
    CLASSIFICATION                    REGRESSION
    (Discrete output)                 (Continuous output)
    
       ●                                    ●
       ●  ▲                                ●   ──────
      ●●  ▲▲▲                           ●●  ────
     ●●●  ▲▲▲▲                        ●●●──── 
    ●●●●  ▲▲▲▲▲                     ●●●────
                                   ●────
    Classes: A, B, C              Output: 0.0 to ∞
    
    Examples:                     Examples:
    - Spam detection              - House price
    - Image recognition           - Temperature
    - Disease diagnosis           - Stock price
```
""",

    "decision_tree": """
```
                    ┌─────────────────┐
                    │  Is it raining? │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
         ┌────────┐                    ┌────────┐
         │  Yes   │                    │   No   │
         └────┬───┘                    └────┬───┘
              │                             │
              ▼                             ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ Bring umbrella  │          │ Is it sunny?    │
    └─────────────────┘          └────────┬────────┘
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                         ┌────────┐              ┌────────┐
                         │  Yes   │              │   No   │
                         └────┬───┘              └────┬───┘
                              ▼                       ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │ Wear sunglasses │    │ Just go outside │
                    └─────────────────┘    └─────────────────┘
```
""",

    "kmeans_clustering": """
```
    Initial State          After K-Means (K=3)
    
        ●  ●                   ▲  ▲
      ●  ●   ●               ▲  ▲   ▲
        ●  ●                   ▲  ▲
                   ──────▶
      ●    ●                 ●    ●
        ●   ●                  ●   ●
      ●                      ●
                    
          ●  ●                   ■  ■
        ●   ●                  ■   ■
                    
    Random points          Grouped by nearest centroid
                           (●, ▲, ■ = different clusters)
    
    Algorithm: 1. Pick K random centroids
               2. Assign points to nearest centroid
               3. Move centroids to cluster mean
               4. Repeat until converged
```
""",

    "confusion_matrix": """
```
                      Predicted
                   Positive  Negative
                  ┌─────────┬─────────┐
    Actual   Pos  │   TP    │   FN    │  ← Recall = TP/(TP+FN)
    Class         ├─────────┼─────────┤
             Neg  │   FP    │   TN    │
                  └─────────┴─────────┘
                      ↑
              Precision = TP/(TP+FP)
    
    Accuracy = (TP + TN) / Total
    F1 Score = 2 × (Precision × Recall) / (Precision + Recall)
    
    TP = True Positive   (Correct positive prediction)
    TN = True Negative   (Correct negative prediction)
    FP = False Positive  (Incorrect positive - Type I Error)
    FN = False Negative  (Incorrect negative - Type II Error)
```
""",

    "overfitting": """
```
    Training Data (●)        Underfitting    Good Fit    Overfitting
    
    ●     ●                    ────────      ╭──────╮    ╭╮ ╭╮ ╭╮
      ●       ●               /              │      │   ╱  ╲╱  ╲╱  ╲
        ● ●                  ────────        ╰──────╯  ╱            ╲
           ●  ●                                       
                            High Bias       Balanced   High Variance
                            Low Variance               Low Bias
    
    Test Error:              High            Low        High
    Training Error:          High            Low        Very Low
    
    Solution: Regularization, more data, simpler model
```
""",

    "activation_functions": """
```
    Sigmoid                 ReLU                    Tanh
    
    1 ─────────────╮       │                  1 ──────────╮
                   │       │   ╱              │           │
    0.5 ──────────●│       │  ╱               0 ──────────●
                   │       │ ╱                │           │
    0 ╭────────────┘       │╱                -1 ──────────╯
      ───────────────      ───────────        ───────────────
           x                    x                   x
    
    σ(x) = 1/(1+e⁻ˣ)      max(0, x)          (eˣ - e⁻ˣ)/(eˣ + e⁻ˣ)
    Range: (0, 1)         Range: [0, ∞)      Range: (-1, 1)
    Use: Output layer     Use: Hidden        Use: Hidden layers
         (probability)    layers (default)   (centered)
```
""",

    "train_test_split": """
```
    Full Dataset (100%)
    ┌────────────────────────────────────────────────────┐
    │ ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● ● │
    └────────────────────────────────────────────────────┘
                            │
                            ▼ Random Split
    ┌────────────────────────────────┐ ┌───────────────┐
    │ Training Set (70-80%)          │ │ Test Set      │
    │ ● ● ● ● ● ● ● ● ● ● ● ● ● ● ●  │ │ (20-30%)      │
    │                                │ │ ● ● ● ● ● ●   │
    │ Used to LEARN parameters       │ │ Used to       │
    │                                │ │ EVALUATE      │
    └────────────────────────────────┘ └───────────────┘
    
    Never train on test data! (Data Leakage = Cheating)
```
""",
}


# Mermaid.js Diagrams for Frontend Rendering
MERMAID_DIAGRAMS = {
    "neural_network": """
```mermaid
graph LR
    subgraph Input
        x1((x₁))
        x2((x₂))
        x3((x₃))
    end
    subgraph Hidden
        h1((h₁))
        h2((h₂))
    end
    subgraph Output
        y((ŷ))
    end
    x1 --> h1
    x1 --> h2
    x2 --> h1
    x2 --> h2
    x3 --> h1
    x3 --> h2
    h1 --> y
    h2 --> y
```
""",

    "gradient_descent": """
```mermaid
flowchart TD
    A[Initialize weights randomly] --> B[Forward pass: compute prediction]
    B --> C[Compute loss/error]
    C --> D[Compute gradient ∂L/∂w]
    D --> E[Update weights: w = w - α × ∂L/∂w]
    E --> F{Converged?}
    F -->|No| B
    F -->|Yes| G[Done! Optimal weights found]
```
""",

    "decision_tree": """
```mermaid
graph TD
    A{Feature 1 > threshold?} -->|Yes| B{Feature 2 > threshold?}
    A -->|No| C{Feature 3 > threshold?}
    B -->|Yes| D[Class A]
    B -->|No| E[Class B]
    C -->|Yes| F[Class B]
    C -->|No| G[Class C]
```
""",

    "supervised_learning": """
```mermaid
flowchart LR
    subgraph Training
        A[Labeled Data] --> B[Model learns patterns]
        B --> C[Trained Model]
    end
    subgraph Prediction
        D[New Data] --> C
        C --> E[Prediction]
    end
```
""",

    "classification_pipeline": """
```mermaid
flowchart LR
    A[Raw Data] --> B[Preprocessing]
    B --> C[Feature Engineering]
    C --> D[Train/Test Split]
    D --> E[Model Training]
    E --> F[Evaluation]
    F --> G{Good enough?}
    G -->|No| H[Tune hyperparameters]
    H --> E
    G -->|Yes| I[Deploy Model]
```
""",
}


def get_ascii_diagram(concept: str) -> Optional[str]:
    """
    Get ASCII art diagram for a concept.
    
    Args:
        concept: The concept to visualize (e.g., 'neural_network', 'gradient_descent')
        
    Returns:
        ASCII diagram string or None if not available
    """
    return ASCII_DIAGRAMS.get(concept)


def get_mermaid_diagram(concept: str) -> Optional[str]:
    """
    Get Mermaid.js diagram for a concept.
    
    Args:
        concept: The concept to visualize
        
    Returns:
        Mermaid diagram string or None if not available
    """
    return MERMAID_DIAGRAMS.get(concept)


def get_visual_for_concept(concept: str, prefer_mermaid: bool = False) -> Optional[str]:
    """
    Get the best available visual for a concept.
    
    Args:
        concept: The concept to visualize
        prefer_mermaid: If True, prefer Mermaid over ASCII when both available
        
    Returns:
        Visual diagram string or None
    """
    if prefer_mermaid:
        return get_mermaid_diagram(concept) or get_ascii_diagram(concept)
    else:
        return get_ascii_diagram(concept) or get_mermaid_diagram(concept)


def list_available_visuals() -> Dict[str, List[str]]:
    """
    List all available visual diagrams.
    
    Returns:
        Dict with 'ascii' and 'mermaid' keys listing available concepts
    """
    return {
        "ascii": list(ASCII_DIAGRAMS.keys()),
        "mermaid": list(MERMAID_DIAGRAMS.keys()),
    }


# Concept name to diagram key mapping
CONCEPT_TO_DIAGRAM = {
    "neural_networks": "neural_network",
    "neural_network": "neural_network",
    "perceptron": "neural_network",
    "deep_learning": "neural_network",
    "gradient_descent": "gradient_descent",
    "optimization": "gradient_descent",
    "learning_rate": "gradient_descent",
    "backpropagation": "backpropagation",
    "chain_rule": "backpropagation",
    "classification": "classification_vs_regression",
    "regression": "classification_vs_regression",
    "supervised_learning": "supervised_learning",
    "decision_trees": "decision_tree",
    "decision_tree": "decision_tree",
    "clustering": "kmeans_clustering",
    "kmeans": "kmeans_clustering",
    "k_means": "kmeans_clustering",
    "model_evaluation": "confusion_matrix",
    "confusion_matrix": "confusion_matrix",
    "accuracy": "confusion_matrix",
    "precision": "confusion_matrix",
    "recall": "confusion_matrix",
    "overfitting": "overfitting",
    "underfitting": "overfitting",
    "regularization": "overfitting",
    "activation_functions": "activation_functions",
    "sigmoid": "activation_functions",
    "relu": "activation_functions",
    "tanh": "activation_functions",
    "train_test_split": "train_test_split",
    "data_preprocessing": "train_test_split",
}


def get_diagram_for_detected_concept(detected_concept: str) -> Optional[str]:
    """
    Get a diagram based on a detected concept from query.
    
    Args:
        detected_concept: The concept detected from user query
        
    Returns:
        ASCII diagram string or None
    """
    diagram_key = CONCEPT_TO_DIAGRAM.get(detected_concept)
    if diagram_key:
        return get_ascii_diagram(diagram_key)
    return None


def format_diagram_for_response(diagram: str, title: str = "Visual") -> str:
    """
    Format a diagram for embedding in a tutor response.
    """
    return f"\n\n📊 **{title}:**\n{diagram}"
