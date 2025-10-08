# COMP-237 Educate Mode Customization Summary

**Date**: October 7, 2024  
**Course**: COMP-237 - Artificial Intelligence (Centennial College)  
**Status**: PRD Updated with Domain-Specific Agents

---

## Overview

The Educate Mode PRD has been customized for **COMP-237: Artificial Intelligence** students with domain-specific agents, tools, and content aligned with the 14-week course structure.

### Key Customizations

1. **Three New COMP-237-Specific Agents**
2. **Math Translation Focus** (primary student pain point)
3. **50+ Course-Specific Misconceptions Database**
4. **Week-by-Week Topic Alignment** (Weeks 1-14)
5. **Technology Stack Updates** (Gemini 2.5 Flash, Supabase)

---

## New COMP-237-Specific Agents

### 1. Math Translation Agent (FR-8) ⭐ **Priority 1**

**Purpose**: Convert mathematical formulas and concepts into intuitive, accessible language

**Student Need**: "Students struggle translating the math in the theoretical areas" (user quote)

**Capabilities**:
- **4-Level Explanation System**:
  1. **Intuition**: Plain language with analogies
  2. **Components**: Break down each term in formula
  3. **Example**: Worked numerical calculation
  4. **Visual**: Describe what graph/plot shows

**Coverage** (30+ formulas):
- Week 4: Heuristic functions (admissibility)
- Week 6: Linear regression (least squares, R²)
- Week 6: Statistical tests (z-test, p-values, chi-square)
- Week 7: Logistic regression (sigmoid, log-odds)
- Weeks 6-9: Gradient descent (partial derivatives, learning rate)
- Week 6: Loss functions (L1, L2, cross-entropy, MSE)
- Week 7: Confusion matrix metrics (precision, recall, F1)
- Week 9: Perceptron learning, backpropagation
- Week 10: Bayes theorem, tf-idf
- Week 12: Mean shift clustering

**Example Query**:
> "What does this gradient descent formula mean?"

**Response**:
```
1. INTUITION:
   Gradient descent is like finding the lowest point in a valley by taking 
   small steps downhill. At each step, you look around to see which direction 
   goes down the steepest, then take a step that way.

2. COMPONENTS:
   - θ (theta) = model parameters/weights we're learning
   - α (alpha) = learning rate, controls step size (e.g., 0.01)
   - ∇J(θ) = gradient, tells us which direction increases the loss
   - Minus sign = go OPPOSITE direction to decrease loss

3. EXAMPLE:
   Let's say θ = 10, α = 0.1, ∇J(θ) = 4
   New θ = 10 - (0.1 × 4) = 10 - 0.4 = 9.6
   We moved from 10 → 9.6 to reduce the loss

4. VISUAL:
   The loss function graph is U-shaped. We start at some random point
   on the U and follow the slope downward until we reach the bottom.
```

### 2. Algorithm Visualization Agent (FR-9)

**Purpose**: Step-by-step execution traces for search algorithms and ML models

**Capabilities**:
- **Search Algorithms** (Weeks 3-5):
  - DFS: Stack state, backtracking
  - BFS: Queue state, level-by-level traversal
  - UCS: Priority queue, path costs
  - Greedy: Heuristic values, node selection
  - A*: f(n) = g(n) + h(n) calculation, open/closed lists

- **ML Algorithms** (Weeks 6-9):
  - Gradient Descent: Iteration-by-iteration weight updates
  - Perceptron: Training examples, weight adjustments
  - Naive Bayes: Probability calculations
  - K-Means: Cluster assignments, centroid updates

**Example Query**:
> "Show me A* step-by-step on this graph"

**Response**:
```
Step 1: Start at node A
  - Open list: [A] with f(A) = 0 + 5 = 5
  - Closed list: []
  - Action: Expand A

Step 2: Expand node A (neighbors: B, C)
  - Calculate f(B) = g(B) + h(B) = 2 + 3 = 5
  - Calculate f(C) = g(C) + h(C) = 4 + 4 = 8
  - Open list: [B(5), C(8)]
  - Closed list: [A]
  - Decision: Select B (lowest f-value)

Step 3: Expand node B
  ...
```

### 3. Code-Theory Bridge Agent (FR-10)

**Purpose**: Connect mathematical formulas to Python implementations

**Capabilities**:
- **Side-by-side mappings**: Formula ↔ sklearn code
- **Parameter explanations**: What each sklearn parameter means
- **Worked examples**: Manual calculation + sklearn code comparison

**Coverage** (15+ mappings):
- Linear Regression: `sklearn.LinearRegression()` vs least squares formula
- Logistic Regression: `sklearn.LogisticRegression()` vs sigmoid + log-loss
- Gradient Descent: NumPy implementation vs ∇J(θ) formula
- Naive Bayes: `sklearn.MultinomialNB()` vs Bayes theorem
- TF-IDF: `sklearn.TfidfVectorizer()` vs mathematical definition

**Example Query**:
> "How does the linear regression math connect to sklearn code?"

**Response**:
```python
# MATHEMATICAL FORMULA:
# ŷ = θ₀ + θ₁x₁ + θ₂x₂ + ... + θₙxₙ
# θ* = argmin Σ(y - ŷ)²

# SKLEARN CODE:
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_train, y_train)

# PARAMETER MAPPINGS:
# θ₀ (intercept/bias) → model.intercept_
# θ₁, θ₂, ..., θₙ (weights) → model.coef_
# X (features) → X_train (your data matrix)
# y (target) → y_train (actual values)

# PREDICTIONS:
y_pred = model.predict(X_test)  # ŷ = θ₀ + θ₁x₁ + ...

# WORKED EXAMPLE:
X = [[1], [2], [3]]
y = [2, 4, 6]
model.fit(X, y)

print(f"Intercept (θ₀): {model.intercept_}")  # ~0
print(f"Slope (θ₁): {model.coef_[0]}")        # ~2
# Formula: ŷ = 0 + 2x
```

---

## COMP-237 Misconceptions Database

**Count**: 50+ misconceptions organized by course week

### Week 3-5: Search Algorithms
- `dfs_bfs_confusion`: Thinking DFS is complete or optimal
- `greedy_optimal`: Believing Greedy always finds optimal solution
- `heuristic_admissibility`: Not understanding h(n) ≤ true cost for A*
- `a_star_complexity`: Confusing time vs space complexity
- `data_structure_choice`: Using wrong structure (stack vs queue)

### Week 6-8: Machine Learning
- `classification_regression`: "Linear regression is for classification"
- `regression_classification`: "Logistic regression predicts continuous values"
- `overfitting_good`: Thinking 100% training accuracy means good model
- `gradient_descent_direction`: Confusing ascent vs descent
- `learning_rate_size`: "Larger learning rate always converges faster"
- `loss_function_choice`: Using MSE for classification
- `train_test_split`: Training and testing on same data
- `confusion_matrix_metrics`: Confusing precision, recall, F1

### Week 9: Neural Networks
- `perceptron_linearity`: Not understanding linearly separable limitation
- `backprop_direction`: Confusing forward vs backward pass
- `activation_function_purpose`: Not knowing why we need non-linear activations
- `relu_vs_sigmoid`: Using sigmoid for hidden layers
- `gradient_vanishing`: Not recognizing vanishing gradient problem

### Week 10-11: NLP
- `bayes_conditional`: Confusing P(A|B) with P(B|A)
- `naive_assumption`: Not understanding "naive" independence assumption
- `tf_idf_interpretation`: Thinking higher TF-IDF always means more important
- `bag_of_words_order`: Expecting BoW to preserve word order

### Week 12: Computer Vision
- `rgb_hsv_confusion`: Not knowing when to use RGB vs HSV
- `clustering_k_choice`: Thinking K-means finds optimal K automatically
- `mean_shift_bandwidth`: Not understanding bandwidth impact

### Statistics & Math (Cross-Week)
- `p_value_interpretation`: "p < 0.05 means null hypothesis is false"
- `correlation_causation`: "Correlation implies causation"
- `z_test_t_test`: Using z-test with small sample size

**Detection Methods**:
- Pattern matching (regex)
- Semantic similarity (embeddings)
- Code error analysis
- Quiz answer patterns

**Feedback Structure**:
1. Acknowledge partial understanding
2. Explain the specific error
3. Provide correct understanding with example
4. Link to relevant course materials
5. Suggest practice problem

---

## Week-by-Week Topic Alignment

**Database Schema Enhancement**:
- All tables now include `week_number` field (1-14)
- Topic mastery tracked per week
- Quiz questions aligned with weekly learning outcomes
- Misconceptions mapped to week context

**14-Week Course Structure**:

| Week | Topics | Agent Focus |
|------|--------|-------------|
| 1-2  | Intelligent agents, environments | Concept Explanation |
| 3-5  | Search algorithms (DFS, BFS, UCS, Greedy, A*) | **Algorithm Visualization** |
| 6-8  | Machine learning, regression, gradient descent | **Math Translation**, Code-Theory Bridge |
| 9    | Neural networks, backpropagation | **Math Translation**, Misconception Detection |
| 10-11| NLP, Naive Bayes, TF-IDF | **Math Translation**, Code-Theory Bridge |
| 12   | Computer vision, clustering | Algorithm Visualization |
| 13   | AI ethics | Socratic Dialogue |
| 14   | Comprehensive review | Assessment Agent |

---

## Technology Stack Updates

### Before (Generic PRD)
- **LLM**: Multiple options (Gemini Pro, Claude, Mixtral, local Ollama)
- **Database**: Local PostgreSQL setup
- **Deployment**: Self-hosted

### After (COMP-237 Specific)
- **LLM**: **Gemini 2.5 Flash** (Google AI Studio / Vertex AI)
  - Extremely fast (< 2 seconds)
  - 1M token context window
  - Excellent mathematical reasoning
  - Cost-effective for education
  - Strong code generation
  
- **Database**: **Supabase** (PostgreSQL cloud)
  - No local setup needed
  - Built-in authentication
  - Real-time capabilities
  - Row-level security
  - Free tier: 500MB database, 2GB bandwidth
  
- **Configuration**:
  ```python
  # Gemini 2.5 Flash
  import google.generativeai as genai
  genai.configure(api_key=GOOGLE_API_KEY)
  model = genai.GenerativeModel('gemini-2.5-flash')
  
  # Supabase
  from supabase import create_client
  supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
  ```

---

## Updated Agent Architecture

**Total Agents**: 10 (6 original + 3 COMP-237-specific + 1 enhanced intent)

```
Student Query + Week Context
    ↓
1. Intent Classification (8 types now, including math_translation)
    ↓
2. Retrieval Agent (week-aware context)
    ↓
3. Math Translation Agent (NEW) ⭐
    ↓
4. Algorithm Visualization Agent (NEW) ⭐
    ↓
5. Code-Theory Bridge Agent (NEW) ⭐
    ↓
6. Scaffolding Agent (3-tier hints)
    ↓
7. Misconception Detection (50+ COMP-237 patterns)
    ↓
8. Response Generation (Gemini 2.5 Flash)
    ↓
9. Student Model Update (Supabase)
    ↓
Response to UI
```

### Intent Types (8 total)

1. `concept_explanation`: "What is gradient descent?"
2. `problem_solving`: "How do I implement BFS?"
3. **`math_translation`**: "What does this loss function mean?" ⭐ **NEW**
4. **`algorithm_trace`**: "Show me A* step-by-step" ⭐ **NEW**
5. **`code_theory_bridge`**: "How does the math connect to sklearn?" ⭐ **NEW**
6. `clarification`: "Why is A* better than Greedy?"
7. `misconception_check`: "Linear regression is for classification"
8. `assessment_request`: "Quiz me on Week 6 topics"

---

## Implementation Plan Updates

**Duration**: 16 weeks (was 14 weeks)

**New Phase**: Phase 3 - COMP-237-Specific Agents (Weeks 5-7)
- Math Translation Agent (Priority 1)
- Algorithm Visualization Agent
- Code-Theory Bridge Agent

**Updated Timeline**:
- Phase 1: Foundation (Weeks 1-2) - Supabase + Gemini setup
- Phase 2: Intent & Retrieval (Weeks 3-4)
- **Phase 3: COMP-237 Agents (Weeks 5-7)** ⭐ **NEW**
- Phase 4: Scaffolding (Weeks 8-9)
- Phase 5: Misconception Detection (Weeks 10-11) - 50+ COMP-237 patterns
- Phase 6: Socratic Dialogue (Weeks 12-13)
- Phase 7: Assessment (Weeks 14-15) - Week-aligned quizzes
- Phase 8: Polish & Testing (Week 16) - Instructor demo

---

## Success Metrics (COMP-237-Specific)

### Learning Outcomes
- **Math Translation Success**: 90%+ of math queries receive 4-level explanation
- **Algorithm Trace Completeness**: 8+ steps showing full execution
- **Code-Theory Bridge Coverage**: 15+ formula-to-code mappings
- **Misconception Detection**: 80%+ accuracy on COMP-237 patterns
- **Week Alignment**: All responses reference correct week context

### Technical Performance
- **Gemini 2.5 Flash Response Time**: < 2 seconds (p95)
- **Math Translation Agent**: < 2 seconds (p95)
- **Algorithm Trace Generation**: < 4 seconds for 20-node graphs
- **Supabase Queries**: < 100ms
- **Intent Classification**: > 90% accuracy on 8 types

### Student Engagement
- **Math Query Volume**: Track % of queries requiring Math Translation Agent
- **Algorithm Visualization Requests**: Track DFS/BFS/A* trace requests
- **Code-Theory Bridge Usage**: Track sklearn-related queries
- **Week-by-Week Progress**: Mastery levels for each of 14 weeks

---

## Database Schema Enhancements

### New Fields (Supabase PostgreSQL)

**session_history table**:
```sql
week_number INTEGER CHECK (week_number BETWEEN 1 AND 14)
```

**topic_mastery table**:
```sql
week_number INTEGER CHECK (week_number BETWEEN 1 AND 14)
```

**misconceptions table**:
```sql
week_context INTEGER CHECK (week_context BETWEEN 1 AND 14)
```

**quiz_responses table**:
```sql
week_number INTEGER CHECK (week_number BETWEEN 1 AND 14)
```

**spaced_repetition table**:
```sql
week_number INTEGER CHECK (week_number BETWEEN 1 AND 14)
```

### New Enum Type
```sql
CREATE TYPE comp237_topic AS ENUM (
    'agents', 
    'search_algorithms', 
    'machine_learning', 
    'neural_networks', 
    'nlp', 
    'computer_vision', 
    'ai_ethics'
);
```

### Helper Function
```sql
CREATE OR REPLACE FUNCTION get_or_create_student(fingerprint VARCHAR)
RETURNS UUID AS $$
-- Automatically creates student on first visit
-- Updates last_active timestamp on subsequent visits
$$;
```

---

## Prompt Template Enhancements

### Math Translation Prompt (Gemini 2.5 Flash)
```
You are a Math Translation Agent for COMP-237: Artificial Intelligence.

Goal: Convert mathematical formulas into intuitive, accessible language.

Student query: {query}
Mathematical content: {formula}

Provide 4-level explanation:
1. INTUITION (plain language, analogies)
2. COMPONENTS (term breakdown)
3. EXAMPLE (worked calculation)
4. VISUAL (graph/plot description)

Course context: Week {week_number} - {topic_name}
```

### Algorithm Trace Prompt (Gemini 2.5 Flash)
```
You are an Algorithm Visualization Agent for COMP-237.

Task: Generate step-by-step execution trace for {algorithm_name}.

Show for each step:
1. Current state (node being explored)
2. Data structure state (stack/queue/priority queue)
3. Visited nodes
4. Frontier nodes
5. Decision rationale

Continue until goal found or search exhausted.
```

### Code-Theory Bridge Prompt (Gemini 2.5 Flash)
```
You are a Code-Theory Bridge Agent for COMP-237.

Task: Show how {concept} mathematical formula maps to sklearn code.

Provide:
1. Mathematical notation
2. Corresponding Python code
3. Parameter mappings (θ → model.coef_)
4. Worked example with small dataset
```

---

## Next Steps

### Immediate (Week 1)
1. ✅ Complete COMP-237 PRD customization
2. ⏳ Set up Supabase project
3. ⏳ Configure Gemini 2.5 Flash API
4. ⏳ Create COMP-237 topic data structures

### Short-term (Weeks 2-3)
1. ⏳ Implement Math Translation Agent (Priority 1)
2. ⏳ Build 50+ misconceptions database
3. ⏳ Test Math Translation with sample formulas
4. ⏳ Create week-by-week topic mapping

### Medium-term (Weeks 4-7)
1. ⏳ Implement Algorithm Visualization Agent
2. ⏳ Implement Code-Theory Bridge Agent
3. ⏳ Integrate with existing Navigate Mode
4. ⏳ Test with COMP-237 lab problems

### Long-term (Weeks 8-16)
1. ⏳ Complete all 10 agents
2. ⏳ Deploy to 10-20 COMP-237 students (beta)
3. ⏳ Collect feedback and iterate
4. ⏳ Instructor demo and approval

---

## Files Updated

1. **`docs/EDUCATE_MODE_PRD.md`** (1,857 lines)
   - Updated executive summary with 8 COMP-237 objectives
   - Added target users section (COMP-237 specific)
   - Added 3 new agents (FR-8, FR-9, FR-10)
   - Expanded misconceptions database to 50+ patterns
   - Updated technology stack (Gemini 2.5 Flash, Supabase)
   - Enhanced database schema with week tracking
   - Added Math Translation, Algorithm Trace, Code-Theory prompts
   - Updated implementation plan to 16 weeks with new Phase 3
   - Added COMP-237 success metrics

2. **`docs/COMP237_CUSTOMIZATION_SUMMARY.md`** (this file)
   - Summary of all COMP-237 customizations
   - Quick reference for new agents
   - Technology stack comparison
   - Implementation priorities

---

## Comparison: Before vs After

| Aspect | Before (Generic) | After (COMP-237) |
|--------|------------------|------------------|
| **Agents** | 6 agents | **10 agents** (3 new COMP-237-specific) |
| **Intent Types** | 5 types | **8 types** (added math, alg_trace, code_theory) |
| **Misconceptions** | ~20 generic | **50+ COMP-237-specific** by week |
| **LLM** | Multiple options | **Gemini 2.5 Flash** (single, optimized) |
| **Database** | Local Postgres | **Supabase** (cloud, managed) |
| **Week Tracking** | No | **Yes** (1-14 weeks) |
| **Math Focus** | Generic | **Math Translation Agent** (Priority 1) |
| **Code-Theory** | Mentioned | **Dedicated Agent** with 15+ mappings |
| **Algorithms** | Generic traces | **Detailed step-by-step** (DFS, BFS, A*) |
| **Timeline** | 14 weeks | **16 weeks** (new Phase 3) |

---

## Contact & Documentation

**Full PRD**: `docs/EDUCATE_MODE_PRD.md`  
**Summary**: `docs/EDUCATE_MODE_SUMMARY.md`  
**Architecture**: `development/backend/LANGGRAPH_ARCHITECTURE.md`  
**Course Outline**: Provided by user (14 weeks, 8 major topics)

**User Quote** (guiding principle):
> "there should be a math agent cause students struggle translating the math in the theoretical areas"

This customization prioritizes **math translation**, **algorithm visualization**, and **code-theory connection** to address the specific learning challenges of COMP-237 students.

---

**END OF SUMMARY**
