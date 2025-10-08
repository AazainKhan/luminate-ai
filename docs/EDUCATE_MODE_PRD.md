# Educate Mode - Product Requirements Document (PRD)

**Project**: Luminate AI - COMP-237 Intelligent Course Assistant  
**Document Version**: 1.0  
**Date**: October 7, 2025  
**Status**: Planning Phase  
**Authors**: Development Team

---

## Executive Summary

This document defines the requirements, architecture, and implementation plan for **Educate Mode** - an intelligent tutoring system (ITS) that provides adaptive, personalized learning support for **COMP-237: Artificial Intelligence** students at Centennial College. Built on evidence-based pedagogical research, Educate Mode uses a multi-agent LangGraph workflow to deliver scaffolded hints, Socratic dialogue, misconception detection, and adaptive assessment specifically tailored to AI/ML course content.

### Key Objectives

1. **Domain-Specific Tutoring**: Provide COMP-237-specific explanations for search algorithms, machine learning, NLP, and computer vision
2. **Math Translation**: Dedicated agent to explain mathematical concepts (gradient descent, loss functions, probability) in accessible terms
3. **Code + Theory Integration**: Connect mathematical formulas to Python implementations
4. **Scaffolded Learning**: Implement 3-tier hint system (light → medium → full) for problem-solving
5. **Misconception Detection**: Identify and correct 50+ COMP-237-specific errors (DFS/BFS confusion, classification/regression, overfitting)
6. **Algorithm Visualization**: Describe step-by-step execution of search algorithms and ML models
7. **Assessment Generation**: Create contextual quizzes aligned with weekly course topics
8. **Student Modeling**: Track mastery across 8 major course topics (agents, search, ML, NLP, computer vision)

---

## 1. Problem Statement

### Current State (Navigate Mode Only)

**What Students Have**:
- ✅ Semantic search for course materials
- ✅ Direct links to Blackboard content
- ✅ External resources (YouTube, Wikipedia, OER Commons)

**What Students Need**:
- ❌ Conceptual explanations and learning support
- ❌ Step-by-step problem-solving assistance
- ❌ Adaptive hints when stuck
- ❌ Personalized feedback on understanding
- ❌ Practice questions and assessments
- ❌ Learning progress tracking

### Target Users

### Target Users

**Primary**: COMP-237 students who need:
- **Search Algorithms Help**: Understanding DFS, BFS, UCS, Greedy, A* algorithms
- **Machine Learning Concepts**: Linear regression, logistic regression, neural networks
- **Math Translation**: Converting mathematical formulas to intuitive understanding
- **Code Implementation**: Translating theory to Python scikit-learn/NLTK/OpenCV code
- **NLP Understanding**: Text preprocessing, Naive Bayes, TF-IDF
- **Computer Vision Basics**: Image processing, clustering, mean shift algorithm
- **Algorithm Visualization**: Step-by-step execution traces
- **Exam Preparation**: Practice problems for Tests #1 and #2

**Course Context**:
- 14-week course covering 8 major topics
- Mix of theory (search algorithms, AI concepts) and implementation (Python, scikit-learn)
- Two major tests (Week 8 and Week 14)
- Weekly labs requiring both understanding and coding
- Heavy mathematical content (gradient descent, probability, loss functions)

---

## 2. Goals & Success Metrics

### Primary Goals

| Goal | Success Metric | Target |
|------|----------------|--------|
| **Effective Scaffolding** | Students solve problems after receiving hints | 70%+ success rate |
| **Misconception Detection** | Correctly identify common errors | 80%+ accuracy |
| **Engagement** | Multi-turn conversations maintained | 5+ turns average |
| **Learning Outcomes** | Quiz performance improvement over time | 15%+ increase |
| **Response Quality** | Student satisfaction ratings | 4.0+ / 5.0 |

### Secondary Goals

- **Response Time**: < 3 seconds for tutoring responses
- **Context Retention**: Maintain conversation history across sessions
- **Citation Quality**: 100% of answers include source references
- **Adaptive Accuracy**: Correct mastery level estimation within 10%

---

## 3. User Stories & Use Cases

### Core Use Cases

#### UC-1: Conceptual Explanation
**Actor**: Student  
**Goal**: Understand a complex AI concept  
**Flow**:
1. Student asks: "Explain how backpropagation works"
2. System retrieves relevant course materials
3. Intent agent classifies as "concept explanation"
4. System provides layered explanation:
   - High-level intuition
   - Mathematical formulation (if appropriate for mastery level)
   - Visual description
   - Course material citations
5. Socratic agent asks: "Can you explain why we need the chain rule here?"
6. Student responds, system detects understanding/misconception
7. System provides targeted feedback

**Success Criteria**: Student demonstrates understanding in follow-up questions

#### UC-2: Problem-Solving Assistance
**Actor**: Student  
**Goal**: Solve an assignment problem with scaffolded help  
**Flow**:
1. Student asks: "How do I implement gradient descent?"
2. System classifies as "problem-solving"
3. Scaffolding agent determines current hint level (checks session history)
4. **Light Hint**: "Think about how we update parameters to minimize loss"
5. Student attempts, gets stuck
6. **Medium Hint**: "Remember the formula: θ = θ - α * ∇L. What does each term represent?"
7. Student still stuck
8. **Full Explanation**: Complete worked example with code
9. System generates similar practice problem

**Success Criteria**: Student solves similar problems independently

#### UC-3: Misconception Correction
**Actor**: Student  
**Goal**: Identify and correct misunderstanding  
**Flow**:
1. Student explains: "Linear regression is for classification, right?"
2. Misconception agent detects: confusion between regression/classification
3. System provides tailored feedback:
   - Acknowledges partial understanding
   - Explains key difference with examples
   - Provides comparative visualization description
   - Links to course materials on both topics
4. System asks verification question
5. Student demonstrates corrected understanding

**Success Criteria**: Misconception not repeated in future sessions

#### UC-4: Self-Assessment
**Actor**: Student  
**Goal**: Test understanding before exam  
**Flow**:
1. Student requests: "Quiz me on neural networks"
2. Assessment agent generates 5 contextual questions based on:
   - Recent course topics
   - Student's mastery level
   - Previously weak areas
3. Student answers each question
4. System provides immediate feedback with explanations
5. Updates student mastery profile
6. Suggests topics for further review

**Success Criteria**: Student demonstrates improved quiz performance over time

#### UC-5: Contextual Learning Path
**Actor**: Student  
**Goal**: Learn a topic with proper prerequisites  
**Flow**:
1. Student asks: "I want to learn about transformers"
2. System checks student mastery of prerequisites:
   - Attention mechanisms (60% mastery) ❌
   - Neural networks (85% mastery) ✅
3. System recommends: "Let's review attention mechanisms first"
4. Provides targeted learning materials
5. After mastery checkpoint, proceeds to transformers
6. Updates student knowledge graph

**Success Criteria**: Student learns more efficiently with fewer gaps

---

## 4. Functional Requirements

### 4.1 Intent Classification Agent

**Purpose**: Route student queries to appropriate tutoring strategy for COMP-237 content

**Requirements**:

- **FR-1.1**: Classify query intent into COMP-237-specific categories:
  - `concept_explanation`: "What is gradient descent?" or "Explain the A* algorithm"
  - `problem_solving`: "How do I implement BFS?" or "Walk me through this neural network code"
  - `math_translation`: "What does this loss function formula mean?" or "Explain Bayes theorem in simple terms"
  - `algorithm_trace`: "Show me A* step-by-step on this graph" or "Trace DFS execution"
  - `code_theory_bridge`: "How does the math connect to the sklearn code?" or "Show me gradient descent in Python"
  - `clarification`: "I don't understand why we use ReLU" or "Why is A* better than Greedy?"
  - `misconception_check`: Student statement to verify (e.g., "Linear regression is for classification")
  - `assessment_request`: "Quiz me on Week 6 topics" or "Test me on search algorithms"
  
- **FR-1.2**: Extract query metadata:
  - Main COMP-237 topic (agents, search, ML, neural networks, NLP, computer vision, ethics)
  - Course week (1-14) if identifiable
  - Difficulty level (introductory, intermediate, advanced)
  - Specific algorithm/concept (DFS, gradient descent, Naive Bayes, etc.)
  
- **FR-1.3**: Route to appropriate sub-agent based on intent:
  - `math_translation` → Math Translation Agent (FR-8)
  - `algorithm_trace` → Algorithm Visualization Agent (FR-9)
  - `code_theory_bridge` → Code-Theory Bridge Agent (FR-10)
  - `concept_explanation` → Concept Explanation Agent (FR-2)
  - `problem_solving` → Scaffolding Agent (FR-3)
  - `misconception_check` → Misconception Agent (FR-4)
  - `assessment_request` → Assessment Agent (FR-6)

**Acceptance Criteria**:

- Classification accuracy > 90% on COMP-237 queries
- Processing time < 200ms
- Handles ambiguous queries gracefully
- Correctly routes math-related queries to Math Translation Agent

### 4.2 Concept Explanation Agent

**Purpose**: Provide layered conceptual understanding

**Requirements**:
- **FR-2.1**: Retrieve relevant course materials from ChromaDB
- **FR-2.2**: Adapt explanation depth to student mastery level:
  - Beginner (< 30%): High-level intuition, analogies
  - Intermediate (30-70%): Add mathematical formulation
  - Advanced (> 70%): Deep technical details, edge cases
  
- **FR-2.3**: Structure explanations with:
  - Definition/overview
  - Key components
  - Visual descriptions (when applicable)
  - Real-world examples
  - Common misconceptions to avoid
  
- **FR-2.4**: Include citations with live Blackboard URLs
- **FR-2.5**: Connect to related topics in knowledge graph

**Acceptance Criteria**:
- All explanations cite ≥ 2 course materials
- Explanation depth matches student mastery level
- Related topics suggested accurately

### 4.3 Scaffolding Agent

**Purpose**: Provide tiered hints for problem-solving

**Requirements**:
- **FR-3.1**: Implement 3-tier hint system:
  
  **Tier 1 - Light Hint** (First attempt):
  - Prompt for recall of related concept
  - Ask guiding question
  - Don't reveal solution steps
  - Example: "Remember what we learned about loss functions. How might that apply here?"
  
  **Tier 2 - Medium Hint** (After failed attempt):
  - Point to specific step/approach
  - Provide partial example
  - Still require student completion
  - Example: "Start by defining your loss function: L = (y - ŷ)². Now, what's the next step?"
  
  **Tier 3 - Full Explanation** (After 2+ failed attempts):
  - Complete worked example
  - Step-by-step solution
  - Explanation of WHY each step works
  - Common mistakes to avoid
  - Similar practice problem
  
- **FR-3.2**: Track hint escalation in session history
- **FR-3.3**: Reset hint level for new problems
- **FR-3.4**: Detect when student is genuinely stuck vs. not trying

**Acceptance Criteria**:

- 70%+ students solve after hints
- Hint level adapts correctly to student attempts
- Full explanations always include practice problem

### 4.4 Misconception Detection Agent

**Purpose**: Identify and correct common COMP-237 student errors

**Requirements**:

- **FR-4.1**: Maintain database of 50+ common COMP-237 misconceptions aligned with course weeks:

**Week 3-5: Search Algorithms**
  - `dfs_bfs_confusion`: Thinking DFS is complete or optimal
  - `greedy_optimal`: Believing Greedy search always finds optimal solution
  - `heuristic_admissibility`: Not understanding h(n) ≤ true cost requirement for A*
  - `a_star_complexity`: Confusing time complexity O(b^d) with space complexity
  - `data_structure_choice`: Using wrong structure (stack vs queue) for BFS/DFS

**Week 6-8: Machine Learning**
  - `classification_regression`: "Linear regression is for classification"
  - `regression_classification`: "Logistic regression predicts continuous values"
  - `overfitting_good`: Thinking 100% training accuracy means good model
  - `underfitting_complexity`: Not recognizing when model is too simple
  - `gradient_descent_direction`: Confusing gradient ascent vs descent
  - `learning_rate_size`: "Larger learning rate always converges faster"
  - `loss_function_choice`: Using wrong loss (MSE for classification, cross-entropy for regression)
  - `train_test_split`: Training and testing on same data
  - `feature_scaling_ignored`: Not normalizing features for gradient descent
  - `confusion_matrix_metrics`: Confusing precision, recall, accuracy, F1

**Week 9: Neural Networks**
  - `perceptron_linearity`: Not understanding perceptron only learns linearly separable functions
  - `backprop_direction`: Confusing forward pass vs backward pass
  - `activation_function_purpose`: Not knowing why we need non-linear activations
  - `relu_vs_sigmoid`: Using sigmoid for hidden layers (outdated practice)
  - `gradient_vanishing`: Not recognizing vanishing gradient problem
  - `weight_initialization`: Initializing all weights to zero

**Week 10-11: NLP**
  - `bayes_conditional`: Confusing P(A|B) with P(B|A)
  - `naive_assumption`: Not understanding "naive" independence assumption
  - `tf_idf_interpretation`: Thinking higher TF-IDF always means more important
  - `bag_of_words_order`: Expecting BoW to preserve word order
  - `n_gram_size`: Not understanding tradeoff between n-gram size and sparsity

**Week 12: Computer Vision**
  - `rgb_hsv_confusion`: Not knowing when to use RGB vs HSV color space
  - `clustering_k_choice`: Thinking K-means can automatically find optimal K
  - `mean_shift_bandwidth`: Not understanding bandwidth parameter's impact
  - `frame_difference_motion`: Confusing simple frame difference with optical flow

**Week 6-14: Statistics & Math**
  - `p_value_interpretation`: "p < 0.05 means the null hypothesis is false"
  - `correlation_causation`: "Correlation implies causation"
  - `sample_size_effect`: Ignoring importance of sample size in statistics
  - `z_test_t_test`: Using z-test when sample size is small
  - `chi_square_application`: Applying chi-square to continuous data

**General COMP-237 Concepts**
  - `ai_ml_confusion`: Using "AI" and "machine learning" interchangeably
  - `supervised_unsupervised`: Confusing supervised vs unsupervised learning
  - `model_algorithm_confusion`: Confusing model (decision tree) with algorithm (ID3)
  - `code_theory_disconnect`: Not connecting mathematical formulas to Python code
  - `sklearn_parameter_meaning`: Not understanding what sklearn parameters do

- **FR-4.2**: Detect misconceptions from:
  - Direct student statements (pattern matching + semantic similarity)
  - Incorrect problem-solving approaches
  - Quiz answer patterns (repeated errors)
  - Code implementation errors
  
- **FR-4.3**: Provide tailored feedback that:
  - Acknowledges partial understanding ("You're right that gradient descent optimizes, but...")
  - Explains the specific error clearly
  - Provides correct understanding with examples
  - Offers comparative examples (e.g., DFS vs BFS side-by-side)
  - Links to relevant course materials (week-specific slides/videos)
  - Suggests practice problem to reinforce
  
- **FR-4.4**: Track resolved vs. persistent misconceptions
  - Mark misconception as "resolved" after 3 consecutive correct demonstrations
  - Flag for review after 5+ detections without resolution
  
- **FR-4.5**: Flag persistent misconceptions for instructor review (future feature)

**Acceptance Criteria**:

- Detection accuracy > 80% on COMP-237 misconceptions
- Database contains 50+ misconceptions with detection patterns
- Feedback leads to correction in 70%+ cases
- Misconceptions logged in student profile with week context

### 4.5 Socratic Dialogue Agent

**Purpose**: Guide students to discover answers through questioning

**Requirements**:

- **FR-5.1**: Implement Socratic techniques:
  - **Pumping**: "Can you say more about that?"
  - **Hinting**: "Consider what happens at each step of the BFS algorithm..."
  - **Reframing**: "How would you approach this differently if you used A* instead?"
  - **Verification**: "Why do you think backpropagation works that way?"
  - **Celebration**: "Exactly! You've identified that A* uses both g(n) and h(n)."
  
- **FR-5.2**: Maintain multi-turn dialogue (5+ turns)
- **FR-5.3**: Build on student's prior responses
- **FR-5.4**: Avoid giving direct answers prematurely
- **FR-5.5**: Recognize when to transition to explanation mode

**Acceptance Criteria**:
- Average dialogue length > 5 turns
- Student satisfaction with dialogue quality > 4.0/5
- Successful knowledge construction in 60%+ cases

### 4.6 Assessment Agent

**Purpose**: Generate quizzes and track mastery

**Requirements**:
- **FR-6.1**: Generate quiz questions based on:
  - Current course topic
  - Student mastery level
  - Previously weak areas
  - Spaced repetition schedule
  
- **FR-6.2**: Question types:
  - Multiple choice (4 options)
  - True/False with explanation
  - Short answer (concept recall)
  - Problem-solving (code or calculation)
  
- **FR-6.3**: Provide immediate feedback with:
  - Correct/incorrect indication
  - Explanation of correct answer
  - References to course materials
  - Related concepts to review
  
- **FR-6.4**: Calculate and update mastery levels:
  - Initial: Based on course progress
  - Updated: After each quiz (Bayesian update)
  - Range: 0-100%
  
- **FR-6.5**: Implement spaced repetition:
  - Review schedule based on Ebbinghaus forgetting curve
  - Increase intervals for mastered topics
  - Decrease intervals for weak topics

**Acceptance Criteria**:
- Questions contextually relevant to student level
- Mastery calculations accurate within ±10%
- Spaced repetition improves long-term retention

### 4.7 Student Model

**Purpose**: Track and personalize learning

**Requirements**:
- **FR-7.1**: Maintain student profile with:
  - Unique student ID (browser-based, no auth for MVP)
  - Session history (all queries and responses)
  - Topic mastery levels (per concept)
  - Detected misconceptions (active and resolved)
  - Quiz performance history
  - Learning preferences
  
- **FR-7.2**: Update profile after each interaction:
  - Increment topic exposure count
  - Update mastery based on quiz performance
  - Log new misconceptions
  - Track hint escalation patterns
  
- **FR-7.3**: Persist across browser sessions (localStorage + Supabase)
- **FR-7.4**: Provide progress dashboard (future enhancement)

**Acceptance Criteria**:

- Profile persists across sessions
- Mastery updates reflect actual learning
- History retrievable for context

### 4.8 Math Translation Agent

**Purpose**: Translate mathematical formulas and concepts into intuitive, accessible language for COMP-237 students

**Requirements**:

- **FR-8.1**: Identify mathematical content in queries:
  - Formulas (gradient descent, loss functions, Bayes theorem, tf-idf, perceptron learning rule)
  - Statistical concepts (PDF, z-test, p-test, chi-square, correlation)
  - Linear algebra (vectors, matrices, dot products)
  - Calculus (derivatives, chain rule for backpropagation)
  
- **FR-8.2**: Provide multi-level explanations:
  - **Level 1 - Intuition**: Plain language explanation with analogies
  - **Level 2 - Components**: Break down each term/variable in the formula
  - **Level 3 - Example**: Worked numerical example with actual values
  - **Level 4 - Visual**: Describe what a graph/plot would show
  
- **FR-8.3**: Cover COMP-237 math-heavy topics:
  - **Week 4**: Heuristic functions (admissibility, consistency)
  - **Week 6**: Linear regression (least squares, residuals, R²)
  - **Week 6**: Statistical tests (z-test, p-values, chi-square)
  - **Week 7**: Logistic regression (sigmoid function, log-odds)
  - **Weeks 6-9**: Gradient descent (partial derivatives, learning rate, convergence)
  - **Week 6**: Loss functions (L1, L2, cross-entropy, mean squared error)
  - **Week 7**: Confusion matrix metrics (precision, recall, F1-score, accuracy)
  - **Week 9**: Perceptron learning (weight updates, bias term)
  - **Week 9**: Backpropagation (chain rule, gradient flow)
  - **Week 10**: Bayes theorem (prior, likelihood, posterior)
  - **Week 10**: tf-idf (term frequency, inverse document frequency, normalization)
  - **Week 12**: Mean shift clustering (kernel density, mode seeking)
  
- **FR-8.4**: Bridge to code implementation:
  - Show how mathematical formula maps to scikit-learn/NumPy code
  - Explain what each parameter in the code corresponds to in the math
  
- **FR-8.5**: Address common student struggles:
  - "What does this symbol mean?" (∇, Σ, ∂, θ, α, etc.)
  - "Why do we need this term in the formula?"
  - "What happens if I change this parameter?"
  - "How do I calculate this by hand?"

**Acceptance Criteria**:

- 90%+ of math queries receive intuitive explanation + formula breakdown
- All COMP-237 mathematical concepts covered (30+ formulas)
- Examples use real course-aligned data
- Code-math bridge provided when applicable

### 4.9 Algorithm Visualization Agent

**Purpose**: Provide step-by-step execution traces for search algorithms and ML models

**Requirements**:

- **FR-9.1**: Generate textual step-by-step traces for search algorithms:
  - **DFS**: Show stack state, visited nodes, current path, backtracking
  - **BFS**: Show queue state, frontier expansion, level-by-level traversal
  - **UCS**: Show priority queue, path costs, node expansion order
  - **Greedy**: Show heuristic values, node selection, final path
  - **A\***: Show f(n) = g(n) + h(n) calculation, open/closed lists, path reconstruction
  
- **FR-9.2**: Visualize tree/graph state at each step:
  - Current node (highlighted)
  - Visited nodes (marked)
  - Frontier/fringe nodes (indicated)
  - Final path (when found)
  - Dead ends (when applicable)
  
- **FR-9.3**: Explain decision points:
  - "Why was node X chosen over node Y?"
  - "What is the heuristic value at this state?"
  - "Why did we backtrack here?"
  - "How does the priority queue ordering work?"
  
- **FR-9.4**: Support ML algorithm traces:
  - **Gradient Descent**: Show iteration-by-iteration weight updates
  - **Perceptron**: Show training examples, weight adjustments, decision boundary
  - **Naive Bayes**: Show probability calculations, class predictions
  - **K-Means**: Show cluster assignment iterations, centroid updates
  
- **FR-9.5**: Handle student-provided examples:
  - Accept graph/tree structure from student
  - Execute algorithm on their specific problem
  - Generate custom trace

**Acceptance Criteria**:

- All Week 3-5 search algorithms fully traceable
- Traces include 8+ steps showing complete execution
- Decision rationale provided at each step
- Handles graphs up to 20 nodes efficiently

### 4.10 Code-Theory Bridge Agent

**Purpose**: Connect mathematical formulas to Python implementations, helping students understand the relationship between theory and code

**Requirements**:

- **FR-10.1**: Provide side-by-side formula-to-code mappings:
  - Mathematical notation on left
  - Corresponding Python code on right
  - Annotations explaining the connection
  
- **FR-10.2**: Cover COMP-237 implementation topics:
  - **Linear Regression**: sklearn `LinearRegression()` vs. least squares formula
  - **Logistic Regression**: sklearn `LogisticRegression()` vs. sigmoid + log-loss
  - **Gradient Descent**: NumPy implementation vs. ∇J(θ) formula
  - **Neural Networks**: Manual backprop vs. TensorFlow/Keras
  - **Naive Bayes**: sklearn `MultinomialNB()` vs. Bayes theorem
  - **TF-IDF**: sklearn `TfidfVectorizer()` vs. mathematical definition
  
- **FR-10.3**: Explain parameter mappings:
  - Formula: "learning rate α" → Code: `learning_rate=0.01`
  - Formula: "weight vector θ" → Code: `model.coef_`
  - Formula: "bias term b" → Code: `model.intercept_`
  - Formula: "loss function J" → Code: `model.score()`
  
- **FR-10.4**: Show worked examples with code:
  - Small dataset (5-10 points)
  - Manual calculation step-by-step
  - Same calculation using scikit-learn
  - Compare results to verify understanding
  
- **FR-10.5**: Debugging help:
  - "Why doesn't my code match the expected output?"
  - "What sklearn parameter corresponds to this math term?"
  - "How do I extract the learned weights from the model?"

**Acceptance Criteria**:

- 15+ formula-to-code mappings for COMP-237 topics
- All major sklearn models covered (LinearRegression, LogisticRegression, MultinomialNB, KMeans)
- Parameter mappings documented for each model
- Worked examples use COMP-237 lab-style datasets

---

## 5. Non-Functional Requirements

### 5.1 Performance

- **NFR-1.1**: Response generation time < 3 seconds (p95) using Gemini 2.5 Flash
- **NFR-1.2**: Intent classification < 200ms
- **NFR-1.3**: Supabase queries < 100ms
- **NFR-1.4**: Support concurrent users (10+ simultaneous)
- **NFR-1.5**: Math Translation Agent response < 2 seconds (p95)
- **NFR-1.6**: Algorithm trace generation < 4 seconds for 20-node graphs

### 5.2 Usability

- **NFR-2.1**: Seamless mode switching (Navigate ↔ Educate)
- **NFR-2.2**: Math formulas rendered in LaTeX when possible
- **NFR-2.3**: Algorithm traces presented in readable, indented format
- **NFR-2.2**: Clear visual distinction between modes
- **NFR-2.3**: Conversation history visible in UI
- **NFR-2.4**: Mobile-responsive design
- **NFR-2.5**: Accessibility (WCAG 2.1 Level AA)

### 5.3 Reliability

- **NFR-3.1**: Graceful degradation if LLM unavailable
- **NFR-3.2**: Automatic retry for failed requests (max 3 attempts)
- **NFR-3.3**: Error messages user-friendly and actionable
- **NFR-3.4**: Session recovery after network interruption

### 5.4 Privacy & Security

- **NFR-4.1**: All data processing local (no external API calls)
- **NFR-4.2**: Student data encrypted at rest (Postgres)
- **NFR-4.3**: No PII collection (anonymous browser ID)
- **NFR-4.4**: Clear data retention policy (90 days)

### 5.5 Maintainability

- **NFR-5.1**: Modular agent architecture (easy to add/remove agents)
- **NFR-5.2**: Comprehensive logging for debugging
- **NFR-5.3**: Configuration-driven (prompts, thresholds)
- **NFR-5.4**: Monitoring dashboards for agent performance

---

## 6. System Architecture

### 6.1 LangGraph Multi-Agent Workflow

**Agent Count**: 10 agents (6 original + 3 COMP-237-specific + 1 updated intent)

```
┌─────────────────────────────────────────────────────────────┐
│           EDUCATE MODE GRAPH (COMP-237 SPECIFIC)            │
└─────────────────────────────────────────────────────────────┘

[Student Query + Week Context (1-14)]
      ↓
┌──────────────────────┐
│ 1. Intent            │  Input: query, student_context, week_number
│    Classification    │  Output: 8 intent types (including math, alg_trace, code)
│    Agent             │  LLM: Gemini 2.5 Flash
└──────────────────────┘
│    Classification    │  Output: intent category
│    Agent             │  LLM: Fast model (gemini-flash)
└──────────────────────┘
      ↓
   ┌──┴─────┬─────────┬──────────┐
   ↓        ↓         ↓          ↓
┌───────┐ ┌──────┐ ┌─────────┐ ┌────────┐
│Concept│ │Problem│ │Socratic │ │Assess- │
│Explain│ │Solving│ │Dialogue │ │ment    │
└───────┘ └──────┘ └─────────┘ └────────┘
   │        │         │          │
   └────────┴────┬────┴──────────┘
                 ↓
      ┌──────────────────────┐
      │ 2. Retrieval         │  ChromaDB semantic search
      │    Agent             │  Context enrichment
      └──────────────────────┘
                 ↓
      ┌──────────────────────┐
      │ 3. Scaffolding       │  Determine hint level
      │    Agent             │  Light → Medium → Full
      └──────────────────────┘
                 ↓
      ┌──────────────────────┐
      │ 4. Misconception     │  Detect common errors
      │    Detection         │  Provide tailored feedback
      └──────────────────────┘
                 ↓
      ┌──────────────────────┐
      │ 5. Response          │  LLM: Complex model
      │    Generation        │  (gemini-pro/claude)
      │    Agent             │  Format with citations
      └──────────────────────┘
                 ↓
      ┌──────────────────────┐
      │ 6. Student Model     │  Update mastery levels
      │    Update            │  Log session history
      └──────────────────────┘
                 ↓
      [Formatted Response to UI]
```

### 6.2 State Schema

```python
class EducateState(TypedDict):
    # Input
    query: str
    student_id: str
    session_id: str
    
    # Student Context
    student_context: dict  # mastery levels, history, misconceptions
    topic_mastery: dict    # {topic: mastery_percentage}
    session_history: list  # previous turns in conversation
    
    # Intent Classification
    intent: str           # concept, problem, clarification, assessment
    topic: str            # main topic/concept
    difficulty_level: str # beginner, intermediate, advanced
    
    # Retrieval
    retrieved_chunks: list  # relevant course materials
    citations: list         # source URLs
    
    # Scaffolding
    hint_level: str        # light, medium, full
    attempt_count: int     # number of student attempts
    
    # Misconception Detection
    detected_misconception: str
    misconception_category: str
    
    # Response
    response: dict         # final formatted response
    follow_up_questions: list
    
    # Assessment
    quiz_questions: list   # if assessment intent
    expected_mastery_update: dict
```

### 6.3 Agent Implementations

#### 6.3.1 Intent Classification Agent

**Input**: query, student_context  
**Output**: intent, topic, difficulty_level

**Logic**:
```python
def classify_intent_agent(state: EducateState) -> EducateState:
    prompt = f"""
    Analyze this student query for COMP-237 (Artificial Intelligence).
    
    Query: {state["query"]}
    Student mastery levels: {state["student_context"]["topic_mastery"]}
    
    Classify into:
    - "concept": Asking for explanation (What is X? Explain Y)
    - "problem": Asking for help solving (How do I implement X?)
    - "clarification": Confused about concept (I don't understand why...)
    - "assessment": Requesting quiz/test (Quiz me on X, Test my understanding)
    
    Also identify:
    - Main topic/concept
    - Appropriate difficulty level for response
    
    Output JSON:
    {{
        "intent": "...",
        "topic": "...",
        "difficulty_level": "beginner|intermediate|advanced"
    }}
    """
    
    response = llm.invoke(prompt)  # Fast LLM (gemini-flash)
    result = json.loads(response)
    
    state["intent"] = result["intent"]
    state["topic"] = result["topic"]
    state["difficulty_level"] = result["difficulty_level"]
    
    return state
```

#### 6.3.2 Scaffolding Agent

**Input**: query, attempt_count, session_history  
**Output**: hint_level, scaffolding_prompt

**Logic**:
```python
def scaffolding_agent(state: EducateState) -> EducateState:
    # Determine hint level based on attempts
    if state["attempt_count"] == 0:
        hint_level = "light"
    elif state["attempt_count"] == 1:
        hint_level = "medium"
    else:
        hint_level = "full"
    
    state["hint_level"] = hint_level
    
    # Generate appropriate hint
    if hint_level == "light":
        prompt = f"""Provide a LIGHT hint for: {state["query"]}
        - Don't reveal solution
        - Ask guiding question
        - Prompt recall of related concept
        Example: "Remember what we learned about {state['topic']}. How might that apply here?"
        """
    elif hint_level == "medium":
        prompt = f"""Provide a MEDIUM hint for: {state["query"]}
        - Point to specific step
        - Provide partial example
        - Still require student to complete
        Example: "Start with step 1: [partial]. Now try the next step."
        """
    else:  # full
        prompt = f"""Provide FULL explanation for: {state["query"]}
        - Complete worked example
        - Step-by-step solution
        - Explain WHY each step works
        - Common mistakes to avoid
        - Generate similar practice problem
        """
    
    return state
```

#### 6.3.3 Misconception Detection Agent

**Input**: query, student response  
**Output**: detected_misconception, feedback

**Logic**:
```python
def misconception_detection_agent(state: EducateState) -> EducateState:
    # Common COMP-237 misconceptions database
    misconceptions = {
        "classification_regression": {
            "pattern": "regression.*classification|classification.*predict numbers",
            "feedback": "Linear regression predicts continuous values, while classification predicts discrete categories..."
        },
        "overfitting_memorization": {
            "pattern": "overfitting.*good|memorizing.*better",
            "feedback": "Overfitting means the model memorized training data but can't generalize..."
        },
        # ... 50+ more patterns
    }
    
    # Check for misconceptions
    for key, misconception in misconceptions.items():
        if re.search(misconception["pattern"], state["query"], re.IGNORECASE):
            state["detected_misconception"] = key
            state["misconception_feedback"] = misconception["feedback"]
            
            # Log to student profile
            log_misconception(state["student_id"], key)
            break
    
    return state
```

### 6.4 Database Schema (Supabase PostgreSQL)

**Setup**: Create Supabase project at [supabase.com](https://supabase.com)

**Configuration**:

```python
# Backend connection
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")  # e.g., https://your-project.supabase.co
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # Public anon key for client

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

**SQL Schema** (Execute in Supabase SQL Editor):

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students table
CREATE TABLE students (
    student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    browser_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_fingerprint UNIQUE (browser_fingerprint)
);

-- Create index for faster fingerprint lookups
CREATE INDEX idx_students_fingerprint ON students(browser_fingerprint);

-- Session history
CREATE TABLE session_history (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('navigate', 'educate')),
    query TEXT NOT NULL,
    response JSONB,
    feedback_rating INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
    conversation_turn INTEGER DEFAULT 1,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14)
);

-- Create indexes for session queries
CREATE INDEX idx_session_student ON session_history(student_id, timestamp DESC);
CREATE INDEX idx_session_mode ON session_history(mode);

-- Topic mastery tracking (aligned with COMP-237 weeks)
CREATE TABLE topic_mastery (
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    topic_name VARCHAR(255) NOT NULL,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14),
    mastery_level INTEGER DEFAULT 0 CHECK (mastery_level BETWEEN 0 AND 100),
    last_practiced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    practice_count INTEGER DEFAULT 1,
    PRIMARY KEY (student_id, topic_name)
);

-- COMP-237 topics enum for consistency
DO $$ BEGIN
    CREATE TYPE comp237_topic AS ENUM (
        'agents', 'search_algorithms', 'machine_learning', 
        'neural_networks', 'nlp', 'computer_vision', 'ai_ethics'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Misconceptions tracking (COMP-237 specific)
CREATE TABLE misconceptions (
    misconception_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    misconception_type VARCHAR(255) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    detection_count INTEGER DEFAULT 1,
    week_context INTEGER CHECK (week_context BETWEEN 1 AND 14)
);

-- Create index for unresolved misconceptions
CREATE INDEX idx_misconceptions_unresolved ON misconceptions(student_id, resolved) 
WHERE resolved = FALSE;

-- Quiz responses
CREATE TABLE quiz_responses (
    response_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    question_id VARCHAR(255),
    topic VARCHAR(255) NOT NULL,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14),
    question_text TEXT NOT NULL,
    student_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for quiz analytics
CREATE INDEX idx_quiz_student_topic ON quiz_responses(student_id, topic, timestamp DESC);

-- Spaced repetition schedule
CREATE TABLE spaced_repetition (
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14),
    next_review_date DATE NOT NULL,
    interval_days INTEGER DEFAULT 1,
    ease_factor FLOAT DEFAULT 2.5 CHECK (ease_factor >= 1.3),
    PRIMARY KEY (student_id, topic)
);

-- Create index for upcoming reviews
CREATE INDEX idx_spaced_rep_next_review ON spaced_repetition(next_review_date);

-- Row Level Security (RLS) Policies
-- Enable RLS on all tables
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE misconceptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE spaced_repetition ENABLE ROW LEVEL SECURITY;

-- Policies: Students can only access their own data
CREATE POLICY "Students can view own data" ON students
    FOR SELECT USING (browser_fingerprint = current_setting('request.jwt.claims', true)::json->>'fingerprint');

CREATE POLICY "Students can view own sessions" ON session_history
    FOR SELECT USING (student_id IN (
        SELECT student_id FROM students 
        WHERE browser_fingerprint = current_setting('request.jwt.claims', true)::json->>'fingerprint'
    ));

-- Similar policies for other tables...
-- (Add more RLS policies for INSERT/UPDATE/DELETE as needed)

-- Helper function to get or create student by fingerprint
CREATE OR REPLACE FUNCTION get_or_create_student(fingerprint VARCHAR)
RETURNS UUID AS $$
DECLARE
    student_uuid UUID;
BEGIN
    -- Try to find existing student
    SELECT student_id INTO student_uuid 
    FROM students 
    WHERE browser_fingerprint = fingerprint;
    
    -- If not found, create new student
    IF student_uuid IS NULL THEN
        INSERT INTO students (browser_fingerprint)
        VALUES (fingerprint)
        RETURNING student_id INTO student_uuid;
    ELSE
        -- Update last active timestamp
        UPDATE students 
        SET last_active = NOW() 
        WHERE student_id = student_uuid;
    END IF;
    
    RETURN student_uuid;
END;
$$ LANGUAGE plpgsql;
```

**Supabase Realtime** (Optional - for live leaderboards):

```sql
-- Enable realtime for topic mastery (future feature)
ALTER PUBLICATION supabase_realtime ADD TABLE topic_mastery;
```

**Backend Query Examples**:

```python
from supabase import create_client

# Get or create student
def get_student_id(fingerprint: str) -> str:
    result = supabase.rpc('get_or_create_student', {'fingerprint': fingerprint}).execute()
    return result.data

# Log session
def log_session(student_id: str, query: str, response: dict, mode: str = 'educate'):
    supabase.table('session_history').insert({
        'student_id': student_id,
        'query': query,
        'response': response,
        'mode': mode
    }).execute()

# Update topic mastery
def update_mastery(student_id: str, topic: str, new_level: int, week: int):
    supabase.table('topic_mastery').upsert({
        'student_id': student_id,
        'topic_name': topic,
        'week_number': week,
        'mastery_level': new_level,
        'last_practiced': 'NOW()',
        'practice_count': 'practice_count + 1'
    }, on_conflict='student_id,topic_name').execute()

# Get unresolved misconceptions
def get_misconceptions(student_id: str):
    result = supabase.table('misconceptions').select('*').eq(
        'student_id', student_id
    ).eq('resolved', False).execute()
    return result.data
```

---

## 7. API Endpoints

### 7.1 Educate Mode Endpoint

**POST** `/api/educate`

**Request**:

```json
{
  "query": "Can you explain how backpropagation works?",
  "student_id": "browser-fingerprint-hash",
  "session_id": "uuid-v4",
  "week_number": 9,
  "conversation_history": [
    {
      "role": "user",
      "content": "What is a neural network?"
    },
    {
      "role": "assistant",
      "content": "A neural network is..."
    }
  ]
}
```

**Response**:

```json
{
  "response": {
    "content": "Backpropagation is the algorithm used to train neural networks...",
    "intent": "concept",
    "hint_level": null,
    "citations": [
      {
        "title": "Neural Networks - Lecture 5",
        "url": "https://luminate.centennialcollege.ca/...",
        "module": "Week 5",
        "relevance": "Covers backpropagation algorithm in detail"
      }
    ],
    "follow_up_questions": [
      "Can you explain why we use the chain rule in backpropagation?",
      "How does the learning rate affect convergence?"
    ],
    "detected_misconception": null,
    "mastery_update": {
      "neural_networks": 75,  // +5 from previous
      "backpropagation": 60    // new topic introduced
    }
  },
  "session_id": "uuid-v4",
  "timestamp": "2025-10-07T14:30:00Z"
}
```

### 7.2 Assessment Endpoint

**POST** `/api/educate/quiz`

**Request**:
```json
{
  "student_id": "browser-fingerprint-hash",
  "topic": "neural_networks",
  "question_count": 5,
  "difficulty": "intermediate"
}
```

**Response**:
```json
{
  "quiz_id": "uuid-v4",
  "questions": [
    {
      "question_id": "q1",
      "type": "multiple_choice",
      "question": "What is the purpose of the activation function in a neural network?",
      "options": [
        "To introduce non-linearity",
        "To speed up training",
        "To reduce overfitting",
        "To normalize inputs"
      ],
      "correct_answer": "To introduce non-linearity",
      "topic": "neural_networks"
    },
    // ... 4 more questions
  ]
}
```

### 7.3 Student Profile Endpoint

**GET** `/api/student/profile/{student_id}`

**Response**:
```json
{
  "student_id": "browser-fingerprint-hash",
  "created_at": "2025-09-15T10:00:00Z",
  "last_active": "2025-10-07T14:30:00Z",
  "topic_mastery": {
    "neural_networks": 75,
    "backpropagation": 60,
    "gradient_descent": 80,
    "cnn": 45
  },
  "active_misconceptions": [
    {
      "type": "classification_regression",
      "detected_count": 2,
      "last_detected": "2025-10-05T12:00:00Z"
    }
  ],
  "total_sessions": 24,
  "total_queries": 156,
  "average_rating": 4.3
}
```

---

## 8. UI/UX Design

### 8.1 Mode Indicator

**Visual Changes for Educate Mode**:
- Header color: Purple gradient (vs blue for Navigate)
- Icon: 🎓 Mortarboard (vs 🧭 Compass for Navigate)
- Placeholder: "Ask me anything about COMP-237 concepts..."

### 8.2 Message Components

**User Message** (same as Navigate):
- Left-aligned
- Light background
- User icon

**Assistant Message (Educate-specific)**:

```
┌─────────────────────────────────────────────┐
│ 🎓 Luminate AI (Educate Mode)               │
├─────────────────────────────────────────────┤
│                                             │
│ [Response content with formatting]          │
│                                             │
│ 📚 Sources:                                 │
│ • Neural Networks - Lecture 5 [Open →]     │
│ • Backpropagation Tutorial [Open →]        │
│                                             │
│ 💡 Follow-up questions:                     │
│ • Can you explain the chain rule? [Ask]    │
│ • How does learning rate affect this? [Ask]│
│                                             │
│ ─────────────────────────────────────────  │
│ 📊 Your mastery: Neural Networks 75% ↑     │
└─────────────────────────────────────────────┘
```

### 8.3 Hint UI (Scaffolding)

For problem-solving queries:

```
┌─────────────────────────────────────────────┐
│ 💡 Light Hint (1/3)                         │
├─────────────────────────────────────────────┤
│ Remember what we learned about loss         │
│ functions. How might gradient descent       │
│ help minimize it?                           │
│                                             │
│ [Still Stuck? Get Medium Hint →]           │
└─────────────────────────────────────────────┘
```

### 8.4 Misconception Alert

```
┌─────────────────────────────────────────────┐
│ ⚠️ Common Misconception Detected            │
├─────────────────────────────────────────────┤
│ It seems you might be confusing regression  │
│ with classification. Let me clarify...      │
│                                             │
│ [Learn More] [I Understand]                │
└─────────────────────────────────────────────┘
```

### 8.5 Quiz Interface

```
┌─────────────────────────────────────────────┐
│ 📝 Quick Quiz: Neural Networks              │
├─────────────────────────────────────────────┤
│ Question 1 of 5                             │
│                                             │
│ What is the purpose of the activation       │
│ function in a neural network?               │
│                                             │
│ ○ To introduce non-linearity               │
│ ○ To speed up training                     │
│ ○ To reduce overfitting                    │
│ ○ To normalize inputs                      │
│                                             │
│ [Submit Answer]                             │
└─────────────────────────────────────────────┘
```

---

## 9. Pedagogical Principles

### 9.1 Scaffolding (Wood et al., 1976)

**Definition**: Temporary support structures that help learners accomplish tasks beyond their current ability, gradually removed as competence increases.

**Implementation**:
- Start with minimal hints
- Escalate only when student demonstrates need
- Remove scaffolding as mastery increases
- Track scaffold dependency per topic

### 9.2 Socratic Method (Graesser et al., 2014)

**Definition**: Teaching through questioning that guides discovery rather than direct instruction.

**Implementation**:
- Ask probing questions before giving answers
- Build on student's prior responses
- Encourage independent reasoning
- Celebrate insights and breakthroughs

### 9.3 Retrieval Practice (Roediger & Karpicke, 2006)

**Definition**: Testing enhances long-term retention more than repeated study.

**Implementation**:
- Generate contextual quizzes
- Space repetitions using forgetting curve
- Provide immediate feedback
- Track performance over time

### 9.4 Misconception-Tailored Feedback (AutoTutor)

**Definition**: Identify specific errors in mental models and provide targeted corrections.

**Implementation**:
- Database of common COMP-237 misconceptions
- Pattern matching in student responses
- Comparative explanations (correct vs. incorrect)
- Track resolution and persistence

### 9.5 Adaptive Personalization (Aleven et al., 2006)

**Definition**: Adjust difficulty and support based on individual learner needs.

**Implementation**:
- Track mastery levels per topic
- Adjust explanation depth dynamically
- Route to appropriate learning materials
- Personalize practice problems

---

## 10. LLM Configuration

### 10.1 Model Selection

**All Operations** (Intent Classification, Retrieval, Explanations, Socratic Dialogue, Math Translation):

- **Primary Model**: `gemini-2.5-flash` (Google AI Studio / Vertex AI)
  - Extremely fast response times (< 2 seconds)
  - 1M token context window for course materials
  - Excellent at mathematical reasoning and explanations
  - Cost-effective for educational use
  - Multimodal capabilities (future: handle equation images)
  - Strong code generation for Python examples
  
- **Configuration**:
  ```python
  import google.generativeai as genai
  
  genai.configure(api_key=GOOGLE_API_KEY)
  
  model = genai.GenerativeModel(
      model_name='gemini-2.5-flash',
      generation_config={
          'temperature': 0.7,  # Balanced creativity
          'top_p': 0.95,
          'top_k': 40,
          'max_output_tokens': 2048,
      },
      safety_settings={
          'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
          'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
          'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
          'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
      }
  )
  ```

**Fallback Options** (if Gemini 2.5 Flash unavailable):

- `gpt-4o-mini` - Fast, affordable, good reasoning
- `claude-3-5-sonnet-20241022` - Superior pedagogy and Socratic dialogue
- `llama3.2:latest` (local) - Privacy-first option

### 10.2 Prompt Templates

**Socratic Tutor** (Gemini 2.5 Flash):

```
You are a Socratic tutor for COMP-237: Artificial Intelligence at Centennial College.

Goal: Guide the student to discover the answer through questioning, not direct explanation.

Techniques:
1. Ask guiding questions that build on prior knowledge
2. Encourage active reasoning ("What would happen if...?")
3. Probe for understanding ("Why do you think that works?")
4. Provide hints only after 2-3 failed attempts
5. Celebrate breakthroughs ("Exactly! You've identified the key insight.")

Student context:
- Course Week: {week_number} (1-14)
- Course Week: {week_number} (1-14)
- Topic: {topic}
- Mastery level: {mastery_level}%
- Previous misconceptions: {misconceptions}

Student question: {query}

Your response (ask 1-2 guiding questions):
```

**Math Translation** (Gemini 2.5 Flash):

```
You are a Math Translation Agent for COMP-237: Artificial Intelligence.

Goal: Convert mathematical formulas and concepts into intuitive, accessible language.

Student query: {query}

Mathematical content identified: {formula}

Provide a 4-level explanation:

1. INTUITION (Plain Language):
   - Explain what the formula does in everyday terms
   - Use analogies (e.g., "Gradient descent is like finding the lowest point in a valley by taking small steps downhill")
   - No math symbols allowed in this section

2. COMPONENTS (Term Breakdown):
   - List each variable/term in the formula
   - Explain what it represents
   - Example: "θ (theta) = model parameters/weights we're learning"

3. EXAMPLE (Worked Calculation):
   - Provide a simple numerical example
   - Show step-by-step calculation with actual values
   - Use 2-3 data points max to keep it simple

4. VISUAL (Graph/Plot Description):
   - Describe what a visualization would show
   - Example: "The loss function graph is U-shaped, with the minimum at the optimal weights"

Course context: Week {week_number} - {topic_name}
Student mastery: {mastery_level}%

Your explanation:
```

**Algorithm Trace** (Gemini 2.5 Flash):

```
You are an Algorithm Visualization Agent for COMP-237.

Task: Generate step-by-step execution trace for {algorithm_name}.

Graph/Tree structure:
{graph_definition}

Start node: {start}
Goal node: {goal}
Heuristic values: {heuristic_values}

Generate a trace showing:

For each step:
1. Current state (which node is being explored)
2. Data structure state (stack/queue/priority queue contents)
3. Visited nodes so far
4. Frontier nodes
5. Decision rationale ("Selected node B because it has lowest f(n) = 5")

Format example:
```
Step 1: Start at node A
  - Queue: [A]
  - Visited: []
  - Action: Dequeue A
  
Step 2: Expand node A
  - Neighbors: [B, C]
  - Queue: [B, C]
  - Visited: [A]
  - Decision: Added neighbors in alphabetical order
```

Continue until goal found or search exhausted.
At the end, show the final path and total cost.

Your trace:
```

**Concept Explainer** (Gemini 2.5 Flash):

```
You are an expert AI educator for COMP-237: Artificial Intelligence at Centennial College.

Task: Explain "{concept}" to a student with {mastery_level}% mastery in Week {week_number}.

Structure your explanation:

1. High-level intuition (use analogies)
2. Key components and how they interact
3. {math_depth} mathematical formulation (use Math Translation approach if needed)
4. Visual description (if applicable)
5. Real-world example from COMP-237 course materials
6. Common COMP-237 student misconceptions to avoid

Course materials retrieved:
{retrieved_chunks}

Adapt depth to student level:
- Beginner (< 30%): Focus on intuition and examples, minimal math
- Intermediate (30-70%): Add technical details and formulas with explanations
- Advanced (> 70%): Include edge cases, optimizations, and implementation details

Your explanation:
```

---

## 11. Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

**Deliverables**:

- [ ] Supabase database setup and configuration
- [ ] Student model CRUD operations (get_or_create_student function)
- [ ] Session history logging with week_number tracking
- [ ] Browser fingerprinting for student ID
- [ ] Basic Educate mode UI shell (purple theme vs blue Navigate)
- [ ] Gemini 2.5 Flash API integration
- [ ] Week 1-14 topic mapping data structure

**Success Criteria**:

- Supabase stores student sessions with COMP-237 week context
- Student ID persists across browser sessions via fingerprint
- UI toggles between Navigate/Educate modes smoothly
- Gemini 2.5 Flash responds in < 2 seconds

### Phase 2: Intent & Retrieval (Weeks 3-4)

**Deliverables**:

- [ ] Intent classification agent (updated for 8 intent types including math_translation, algorithm_trace, code_theory_bridge)
- [ ] Retrieval agent (ChromaDB integration with COMP-237 course materials)
- [ ] Basic concept explanation agent with week-aware context
- [ ] Citation formatting with live Blackboard URLs

**Success Criteria**:

- Intent classification > 90% accuracy on COMP-237 queries
- Retrieval returns relevant course materials from correct week
- Explanations include 2+ citations from course documents

### Phase 3: COMP-237-Specific Agents (Weeks 5-7)

**Deliverables**:

- [ ] Math Translation Agent (FR-8)
  - 4-level explanation system (intuition, components, example, visual)
  - Coverage for 30+ COMP-237 formulas
  - Integration with Concept Explanation Agent
  
- [ ] Algorithm Visualization Agent (FR-9)
  - Step-by-step traces for DFS, BFS, UCS, Greedy, A*
  - Tree/graph state visualization (textual)
  - Decision rationale at each step
  
- [ ] Code-Theory Bridge Agent (FR-10)
  - Formula-to-code mappings for 15+ COMP-237 topics
  - Parameter explanations (sklearn model attributes)
  - Worked examples with small datasets

**Success Criteria**:

- Math Translation Agent handles 90%+ of math-related queries successfully
- Algorithm traces complete in < 4 seconds for 20-node graphs
- Code-theory mappings cover all major sklearn models used in COMP-237

### Phase 4: Scaffolding (Weeks 8-9)

**Deliverables**:

- [ ] 3-tier hint system implementation (light, medium, full)
- [ ] Attempt tracking and escalation logic
- [ ] Problem-solving agent with COMP-237 problem types
- [ ] Practice problem generation aligned with weekly topics

**Success Criteria**:

- Hint level adapts correctly to student attempts
- 70%+ students solve after hints
- Practice problems contextually relevant to current week

### Phase 5: Misconception Detection (Weeks 10-11)

**Deliverables**:

- [ ] COMP-237 misconceptions database (50+ patterns organized by week)
- [ ] Detection agent with pattern matching + semantic similarity
- [ ] Tailored feedback generation for each misconception type
- [ ] Misconception tracking in student profile with week context
- [ ] Resolved/persistent misconception tracking

**Success Criteria**:

- Detection accuracy > 80% on COMP-237-specific misconceptions
- Database contains 50+ misconceptions mapped to course weeks
- Feedback leads to correction in 70%+ cases
- Misconceptions marked resolved after 3 consecutive correct demonstrations

### Phase 6: Socratic Dialogue (Weeks 12-13)

**Deliverables**:

- [ ] Socratic dialogue agent with COMP-237 context
- [ ] Multi-turn conversation handling
- [ ] Context retention across turns
- [ ] Dialogue quality metrics
- [ ] COMP-237-specific guiding questions

**Success Criteria**:

- Average dialogue length > 5 turns
- Student satisfaction > 4.0/5
- Knowledge construction success rate > 60%
- Questions reference course-specific concepts

### Phase 7: Assessment (Weeks 14-15)

**Deliverables**:

- [ ] Quiz question generation aligned with 14-week course structure
- [ ] Question database (100+ questions covering Weeks 1-14)
- [ ] Mastery level calculation per topic (8 major topics)
- [ ] Spaced repetition scheduling with week-aware prerequisites
- [ ] Week-specific topic mastery tracking

**Success Criteria**:

- Questions appropriate for mastery level AND current week
- Mastery calculations accurate within ±10%
- Spaced repetition improves retention by 20%+
- Quiz covers all 8 major COMP-237 topics

### Phase 8: Polish & Testing (Week 16)

**Deliverables**:

- [ ] Performance optimization (Gemini 2.5 Flash response times)
- [ ] Error handling and graceful degradation
- [ ] Comprehensive testing (unit, integration, end-to-end)
- [ ] User documentation
- [ ] Supabase query optimization (indexing, connection pooling)
- [ ] COMP-237 instructor demo

**Success Criteria**:

- Response time < 3 seconds (p95) with Gemini 2.5 Flash
- All edge cases handled gracefully
- 90%+ test coverage
- Supabase queries < 100ms

### Phase 8: Pilot Study (Weeks 15-16)

**Deliverables**:
- [ ] Deploy to 10-20 students
- [ ] Collect usage analytics
- [ ] Gather qualitative feedback
- [ ] Measure learning outcomes

**Success Criteria**:
- System uptime > 99%
- Positive student feedback
- Measurable learning improvements

---

## 12. Success Metrics & KPIs

### 12.1 Adoption Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Active Users** | 50+ students | Weekly active users |
| **Session Length** | 10+ min | Average time per session |
| **Return Rate** | 60%+ | Students returning within 7 days |
| **Mode Usage** | 40% Educate | % of sessions in Educate mode |

### 12.2 Learning Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Mastery Improvement** | 15%+ | Average topic mastery increase |
| **Quiz Performance** | 70%+ | Correct answer rate |
| **Problem Solving** | 70%+ | Success after hints |
| **Concept Retention** | 80%+ | Spaced repetition performance |

### 12.3 Engagement Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Conversation Turns** | 5+ | Average turns per dialogue |
| **Satisfaction Rating** | 4.0+ / 5.0 | User feedback ratings |
| **Citation Clicks** | 30%+ | % of citations clicked |
| **Follow-up Questions** | 50%+ | % asking follow-up |

### 12.4 Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Response Time** | < 3 sec (p95) | LangGraph execution time |
| **Intent Accuracy** | 90%+ | Manual validation sample |
| **Misconception Detection** | 80%+ | Expert review of detections |
| **System Uptime** | 99%+ | Availability monitoring |

---

## 13. Risks & Mitigation

### 13.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **LLM Hallucinations** | High | Medium | Always cite sources, fact-check against course materials |
| **Slow Response Times** | Medium | Medium | Use fast models for classification, cache common queries |
| **Database Scalability** | Medium | Low | Implement connection pooling, add indexes |
| **Browser Compatibility** | Low | Low | Test on Chrome, Firefox, Safari |

### 13.2 Pedagogical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Over-reliance on AI** | High | Medium | Emphasize tool is supplement, not replacement |
| **Incorrect Explanations** | High | Low | Validate against course materials, instructor review |
| **Inappropriate Hints** | Medium | Medium | Multi-tier system, don't give answers too early |
| **Missed Misconceptions** | Medium | Medium | Continuously update misconception database |

### 13.3 User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Confusion Between Modes** | Medium | Medium | Clear visual distinction, mode-specific prompts |
| **Privacy Concerns** | High | Low | Clear data policy, local-first processing |
| **Frustration with Socratic Method** | Medium | Medium | Detect frustration, offer to switch to direct explanation |
| **Low Adoption** | High | Medium | User onboarding, instructor endorsement |

---

## 14. Future Enhancements

### 14.1 Short-term (3-6 months)

- **Visual Learning**: Diagram generation for concepts
- **Code Execution**: Run student code in sandbox
- **Voice Interface**: Speech-to-text for queries
- **Mobile App**: Native iOS/Android apps
- **Progress Dashboard**: Visual learning analytics

### 14.2 Medium-term (6-12 months)

- **Multi-course Support**: Expand beyond COMP-237
- **Peer Comparison**: Anonymous benchmarking
- **Instructor Dashboard**: Analytics for TAs/professors
- **Collaborative Learning**: Study groups and peer tutoring
- **Advanced Assessment**: Project evaluation, code review

### 14.3 Long-term (12+ months)

- **Adaptive Curriculum**: Personalized learning paths
- **Predictive Analytics**: Early intervention for at-risk students
- **Research Platform**: A/B testing pedagogical strategies
- **Integration**: LMS-wide deployment (Canvas, Moodle)
- **Open Source**: Community-driven improvement

---

## 15. Appendices

### 15.1 Research References

1. **VanLehn, K. (2011)**. "The Relative Effectiveness of Human Tutoring, Intelligent Tutoring Systems, and Other Tutoring Systems." *Educational Psychologist*

2. **Graesser, A. C., et al. (2014)**. "AutoTutor: A Tutor with Dialogue in Natural Language." *Behavior Research Methods*

3. **Wood, D., Bruner, J. S., & Ross, G. (1976)**. "The Role of Tutoring in Problem Solving." *Journal of Child Psychology and Psychiatry*

4. **Roediger, H. L., & Karpicke, J. D. (2006)**. "The Power of Testing Memory: Basic Research and Implications for Educational Practice." *Perspectives on Psychological Science*

5. **Aleven, V., et al. (2006)**. "A New Paradigm for Intelligent Tutoring Systems: Example-Tracing Tutors." *International Journal of Artificial Intelligence in Education*

6. **Koedinger, K. R., et al. (2013)**. "New Potentials for Data-Driven Intelligent Tutoring System Development." *AI Magazine*

### 15.2 Misconception Database (Sample)

| Misconception | Pattern | Correct Understanding |
|---------------|---------|----------------------|
| **Classification = Regression** | "regression.*classification\|classification.*numbers" | Regression predicts continuous values; classification predicts discrete categories |
| **Overfitting = Good Memorization** | "overfitting.*good\|memorize.*better" | Overfitting hurts generalization; model must balance training accuracy with test performance |
| **More Layers = Always Better** | "more layers.*better\|deeper.*accurate" | Deep networks can overfit or have vanishing gradients; architecture depends on problem |
| **Learning Rate = Speed** | "learning rate.*faster" | Learning rate controls step size in optimization, not execution speed |
| **Accuracy = Best Metric** | "accuracy.*always\|only.*accuracy" | Accuracy misleading for imbalanced datasets; consider F1, precision, recall |

### 15.3 Example Quiz Questions

**Topic: Neural Networks**

1. **Multiple Choice**: What is the primary purpose of the activation function?
   - A) To normalize inputs
   - B) To introduce non-linearity ✓
   - C) To speed up training
   - D) To prevent overfitting

2. **True/False**: Adding more hidden layers always improves model performance.
   - False ✓ (Can lead to overfitting and vanishing gradients)

3. **Short Answer**: Explain the difference between forward propagation and backpropagation in one sentence.
   - Forward: Input → output prediction; Backward: Calculate gradients and update weights

4. **Problem-Solving**: Given a learning rate that's too high, what symptoms would you observe during training?
   - Loss oscillates or increases; model fails to converge; unstable training

---

## Document Control

**Version History**:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2025-10-07 | Development Team | Initial draft |
| 1.0 | 2025-10-07 | Development Team | Complete PRD |

**Approvals**:

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Lead | [Name] | [Date] | [Signature] |
| Technical Lead | [Name] | [Date] | [Signature] |
| Pedagogy Advisor | [Name] | [Date] | [Signature] |

**Next Review Date**: 2025-11-07

---

**END OF DOCUMENT**

---

**Total Pages**: 30  
**Word Count**: ~12,500  
**Reading Time**: ~45 minutes
