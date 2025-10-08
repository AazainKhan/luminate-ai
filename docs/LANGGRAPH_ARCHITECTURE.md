# LangGraph Architecture Plan for Luminate AI
## Based on Educational AI Research (educational_ai.md)

## Date: October 4, 2025

---

## Executive Summary

This document outlines the **LangGraph multi-agent architecture** for Luminate AI, grounded in educational AI research from VanLehn (2011), AutoTutor (Graesser et al., 2004), and modern LLM-based tutoring systems. The architecture implements both **Navigate Mode** and **Educate Mode** using agentic workflows.

---

## Research Foundation

### VanLehn's ITS Model (2011) - Four Components

1. **Domain Model**: Knowledge graph of COMP237 content ✅ (We have 1,296 relationships)
2. **Student Model**: Track learner progress, misconceptions, mastery levels
3. **Pedagogical Model**: Scaffolding, hints, adaptive feedback strategies
4. **Interface Model**: User-friendly Chrome extension with two modes

### Agent-Based Architecture Principles

**AutoTutor (Graesser et al., 2004):**
- Natural language dialogue agents
- Expectation-misconception tailored feedback
- Multi-turn context maintenance

**SimStudent (Matsuda et al., 2015):**
- Learn by demonstration
- Worked examples provision
- Scaffolded problem solving

**Modern LLM Agents (2023-2025):**
- LangGraph for chain-of-thought reasoning
- Tool-augmented agents (e.g., retrieval, calculation)
- Local models (Ollama) for privacy

### Key Pedagogical Techniques to Implement

1. **Scaffolding** (Wood et al., 1976): Gradual hints (light → medium → full)
2. **Retrieval Practice** (Roediger & Karpicke, 2006): Spaced quizzes
3. **Personalization** (Aleven et al., 2006): Adapt to student model
4. **Multi-Turn Dialogue** (Graesser et al., 2014): Context across sessions

---

## LangGraph Architecture

### Mode 1: Navigate Mode (Current Focus)

**Purpose**: Help students find and navigate course content

**Agent Workflow:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      NAVIGATE MODE GRAPH                         │
└─────────────────────────────────────────────────────────────────┘

[Student Query] 
      ↓
┌──────────────────┐
│ Query Understanding │  ← Expand acronyms, identify intent
│ Agent               │     Extract key concepts
└──────────────────┘
      ↓
┌──────────────────┐
│ Retrieval Agent    │  ← Call ChromaDB via FastAPI
│                    │     Re-rank by BB IDs
└──────────────────┘     Filter duplicates
      ↓
┌──────────────────┐
│ Context Agent      │  ← Add related topics from graph
│                    │     Include prerequisite/next steps
└──────────────────┘
      ↓
┌──────────────────┐
│ Formatting Agent   │  ← Group by module/topic
│                    │     Generate "Related Topics"
└──────────────────┘     Format for Chrome extension
      ↓
[Response to Student]
```

**Navigate Mode Agents:**

1. **Query Understanding Agent**
   - **Input**: Raw student query
   - **Tools**: None (pure LLM)
   - **Output**: Parsed query with expanded terms
   - **Prompt**: "You are a query parser for COMP237. Expand acronyms (e.g., ML → machine learning), identify topic categories (e.g., algorithms, neural networks), and extract 3-5 key search terms."

2. **Retrieval Agent**
   - **Input**: Parsed query
   - **Tools**: FastAPI `/query/navigate` endpoint
   - **Output**: Top 10-15 relevant chunks
   - **Logic**: 
     - Call ChromaDB search
     - Re-rank: prioritize docs with BB IDs (90% weight), recency (10% weight)
     - Remove duplicates (same bb_doc_id)

3. **Context Agent**
   - **Input**: Retrieved chunks
   - **Tools**: Graph relationships (CONTAINS, NEXT_IN_MODULE, PREV_IN_MODULE)
   - **Output**: Enriched results with related topics
   - **Logic**:
     - For top 3 results, find related docs via graph
     - Add "Prerequisites" and "Next Steps" sections
     - Include module context

4. **Formatting Agent**
   - **Input**: Enriched results
   - **Tools**: None (pure LLM)
   - **Output**: Structured JSON for Chrome extension
   - **Prompt**: "Format search results into: 1) Top Results (max 5), 2) Related Topics (max 3), 3) Suggested Next Steps. Include Blackboard URLs."

**LangGraph Implementation (Navigate):**

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class NavigateState(TypedDict):
    query: str
    parsed_query: dict
    retrieved_chunks: List[dict]
    enriched_results: List[dict]
    formatted_response: dict

def build_navigate_graph():
    graph = StateGraph(NavigateState)
    
    # Add nodes
    graph.add_node("understand_query", query_understanding_agent)
    graph.add_node("retrieve", retrieval_agent)
    graph.add_node("add_context", context_agent)
    graph.add_node("format_response", formatting_agent)
    
    # Add edges
    graph.set_entry_point("understand_query")
    graph.add_edge("understand_query", "retrieve")
    graph.add_edge("retrieve", "add_context")
    graph.add_edge("add_context", "format_response")
    graph.add_edge("format_response", END)
    
    return graph.compile()
```

---

### Mode 2: Educate Mode (Future Phase)

**Purpose**: Provide adaptive tutoring with scaffolding and feedback

**Agent Workflow:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      EDUCATE MODE GRAPH                          │
└─────────────────────────────────────────────────────────────────┘

[Student Question/Problem]
      ↓
┌──────────────────┐
│ Intent Agent       │  ← Classify: concept question, problem help, 
│                    │     misconception, assessment request
└──────────────────┘
      ↓
   ┌─────┴─────┐
   │           │
   ↓           ↓
┌─────┐    ┌─────────┐
│Explain│    │Problem  │
│Concept│    │Solving  │
└─────┘    └─────────┘
   │           │
   ↓           ↓
┌──────────────────┐
│ Scaffolding Agent  │  ← Determine hint level
│                    │     (light, medium, full)
└──────────────────┘
      ↓
┌──────────────────┐
│ Misconception      │  ← Detect common errors
│ Detection Agent    │     Provide tailored feedback
└──────────────────┘
      ↓
┌──────────────────┐
│ Socratic Agent     │  ← Ask guiding questions
│                    │     Encourage student reasoning
└──────────────────┘
      ↓
┌──────────────────┐
│ Assessment Agent   │  ← Generate follow-up quiz
│                    │     Track mastery level
└──────────────────┘
      ↓
[Response + Student Model Update]
```

**Educate Mode Agents:**

1. **Intent Classification Agent**
   - Classify query type: concept explanation, problem solving, clarification, assessment
   - Route to appropriate sub-graph

2. **Scaffolding Agent** (Wood et al., 1976)
   - **Levels**:
     - Light: "Think about how X relates to Y"
     - Medium: "Recall the steps in algorithm Z"
     - Full: Worked example with explanation
   - **Logic**: Start light, escalate if student stuck (based on session history)

3. **Misconception Detection Agent** (AutoTutor)
   - **Input**: Student answer/question
   - **Tools**: Retrieval from common misconceptions DB
   - **Output**: Identified misconception + tailored feedback
   - **Example**: Student confuses BFS and DFS → Provide comparative visualization

4. **Socratic Dialogue Agent** (Graesser et al., 2014)
   - **Prompt**: "You are a Socratic tutor. Instead of direct answers, ask guiding questions that lead the student to discover the concept themselves."
   - **Techniques**:
     - Pumping: "Can you say more about that?"
     - Hinting: "Consider what happens at each node..."
     - Reframing: "How would you approach this differently?"

5. **Assessment Agent** (Retrieval Practice)
   - Generate quiz questions based on current topic
   - Track student responses in Postgres
   - Calculate mastery level (0-100%)
   - Implement spaced repetition schedule

**LangGraph Implementation (Educate):**

```python
from langgraph.graph import StateGraph, END

class EducateState(TypedDict):
    query: str
    intent: str  # concept, problem, misconception, assessment
    student_context: dict  # mastery levels, history
    hint_level: str  # light, medium, full
    detected_misconception: str
    response: dict

def build_educate_graph():
    graph = StateGraph(EducateState)
    
    # Add nodes
    graph.add_node("classify_intent", intent_agent)
    graph.add_node("explain_concept", concept_explanation_agent)
    graph.add_node("solve_problem", problem_solving_agent)
    graph.add_node("provide_scaffolding", scaffolding_agent)
    graph.add_node("detect_misconception", misconception_agent)
    graph.add_node("socratic_dialogue", socratic_agent)
    graph.add_node("generate_assessment", assessment_agent)
    
    # Conditional routing based on intent
    graph.set_entry_point("classify_intent")
    
    def route_by_intent(state):
        if state["intent"] == "concept":
            return "explain_concept"
        elif state["intent"] == "problem":
            return "solve_problem"
        elif state["intent"] == "assessment":
            return "generate_assessment"
        else:
            return "socratic_dialogue"
    
    graph.add_conditional_edges("classify_intent", route_by_intent)
    
    # All paths lead to scaffolding/misconception detection
    for node in ["explain_concept", "solve_problem", "socratic_dialogue"]:
        graph.add_edge(node, "provide_scaffolding")
    
    graph.add_edge("provide_scaffolding", "detect_misconception")
    graph.add_edge("detect_misconception", END)
    graph.add_edge("generate_assessment", END)
    
    return graph.compile()
```

---

## Student Model Schema (Postgres)

**Purpose**: Track learner progress for personalization

**Tables:**

1. **students**
   - student_id (PK)
   - created_at
   - last_active

2. **session_history**
   - session_id (PK)
   - student_id (FK)
   - timestamp
   - mode (navigate/educate)
   - query
   - response
   - feedback_rating (1-5)

3. **topic_mastery**
   - student_id (FK)
   - topic_name (e.g., "neural networks")
   - mastery_level (0-100%)
   - last_practiced
   - practice_count

4. **misconceptions**
   - student_id (FK)
   - misconception_type (e.g., "confuses BFS/DFS")
   - detected_count
   - resolved (boolean)

5. **quiz_responses**
   - response_id (PK)
   - student_id (FK)
   - question_id
   - answer
   - correct (boolean)
   - timestamp

---

## Prompt Engineering for Pedagogy

### Navigate Mode Prompts

**Query Understanding:**
```
You are a query parser for COMP237 (Artificial Intelligence).

Task: Analyze the student's search query and extract structured information.

Rules:
1. Expand acronyms (ML → machine learning, NN → neural networks)
2. Identify main topic category (algorithms, machine learning, NLP, etc.)
3. Extract 3-5 key search terms
4. Infer student's likely goal (find concept, locate assignment, review topic)

Input: {query}

Output JSON:
{
  "expanded_query": "...",
  "category": "...",
  "search_terms": [...],
  "student_goal": "..."
}
```

**Formatting:**
```
You are a course content organizer for COMP237.

Task: Format search results for student navigation.

Rules:
1. Group results by relevance (Top Results, Related Topics, Next Steps)
2. Include Blackboard URLs for all items
3. Add brief explanations (<50 words) for why each result is relevant
4. Suggest logical learning path

Input: {enriched_results}

Output: Formatted JSON for Chrome extension display
```

### Educate Mode Prompts

**Socratic Tutor:**
```
You are a Socratic tutor for COMP237 (Artificial Intelligence).

Goal: Guide the student to discover the answer through questioning, not direct explanation.

Techniques:
1. Ask guiding questions that build on prior knowledge
2. Encourage active reasoning ("What would happen if...?")
3. Probe for understanding ("Why do you think that works?")
4. Provide hints only after 2-3 failed attempts
5. Celebrate breakthroughs ("Exactly! You've identified the key insight.")

Student context:
- Topic: {topic}
- Mastery level: {mastery_level}%
- Previous misconceptions: {misconceptions}

Student question: {query}

Your response:
```

**Scaffolding Prompts (3 Levels):**

*Light Hint:*
```
The student is working on: {problem}

Provide a LIGHT hint that:
1. Doesn't reveal the solution
2. Asks them to recall a related concept
3. Encourages independent thinking

Example: "Remember what we learned about [related concept]. How might that apply here?"
```

*Medium Hint:*
```
The student is stuck on: {problem}
Previous light hint didn't help.

Provide a MEDIUM hint that:
1. Points to the specific step they're missing
2. Provides a partial example
3. Still requires them to complete the solution

Example: "Look at the first step: [partial solution]. Now try completing the rest."
```

*Full Explanation:*
```
The student needs a complete worked example for: {problem}

Provide:
1. Step-by-step solution
2. Explanation of WHY each step works
3. Common mistakes to avoid
4. Similar problem for practice

Include: Code examples, diagrams (describe), and key insights.
```

---

## Implementation Roadmap

### Phase 4A: Navigate Mode with LangGraph (Week 1-2)

**Tasks:**
1. Install LangGraph: `pip install langgraph langchain`
2. Implement 4 Navigate agents (query, retrieval, context, formatting)
3. Create StateGraph with proper routing
4. Add LLM backend (Ollama Llama 3 8B)
5. Test with sample queries
6. Integrate with FastAPI endpoint

**Deliverables:**
- `development/backend/langgraph/navigate_graph.py`
- Unit tests for each agent
- Integration test: student query → formatted response

### Phase 4B: Student Model (Week 3)

**Tasks:**
1. Set up Postgres database
2. Create student model schema
3. Implement session logging
4. Add topic mastery tracking
5. Build query history API

**Deliverables:**
- Postgres schema SQL
- `development/backend/student_model.py`
- API endpoint: `/student/progress`

### Phase 5: Educate Mode with LangGraph (Week 4-6)

**Tasks:**
1. Implement Educate mode agents (5 agents)
2. Build scaffolding logic (light/medium/full)
3. Create misconception detection
4. Implement Socratic dialogue
5. Add assessment generation
6. Integrate with student model for personalization

**Deliverables:**
- `development/backend/langgraph/educate_graph.py`
- Misconception database
- Assessment question bank
- Pedagogical tests (hint quality, scaffolding effectiveness)

### Phase 6: Chrome Extension Integration (Week 7-8)

**Tasks:**
1. Build TypeScript + React UI
2. Inject chatbot into Blackboard
3. Connect to LangGraph backend via FastAPI
4. Implement session management
5. Add feedback collection
6. Test with real students

**Deliverables:**
- Chrome extension package
- User guide
- Privacy policy
- Pilot study results

---

## Evaluation Metrics (Aligned with Research)

### Learning Gains (VanLehn, 2011)
- Pre/post-test on COMP237 topics
- Target: 0.5-0.76 sigma effect size

### Engagement (du Boulay et al., 2018)
- Average session length: >10 minutes
- Return rate: >60% students use more than once
- Query diversity: >5 different topics per student

### Usability (System Usability Scale)
- Target SUS score: >70/100
- Navigation clarity: 4/5 stars
- Tutor helpfulness: 4/5 stars

### Pedagogical Effectiveness
- Scaffolding success rate: >70% students solve after hints
- Misconception correction: >80% resolved after feedback
- Retrieval practice: >50% students complete quiz

---

## Research Citations

1. **VanLehn, K. (2011)**. "The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems." *Educational Psychologist*, 46(4), 197-221.

2. **Graesser, A. C., et al. (2004)**. "AutoTutor: An intelligent tutoring system with mixed-initiative dialogue." *IEEE Transactions on Education*, 47(4), 612-618.

3. **Wood, D., Bruner, J. S., & Ross, G. (1976)**. "The role of tutoring in problem solving." *Journal of Child Psychology and Psychiatry*, 17(2), 89-100.

4. **Roediger, H. L., & Karpicke, J. D. (2006)**. "The power of testing memory: Basic research and implications for educational practice." *Perspectives on Psychological Science*, 1(3), 181-210.

5. **UNESCO (2024)**. "Guidance for generative AI in education and research." Paris: UNESCO.

---

## Next Steps

1. **Immediate**: Install LangGraph and Ollama
2. **Week 1**: Build Navigate Mode graph with 4 agents
3. **Week 2**: Test Navigate Mode, integrate with Chrome extension prototype
4. **Week 3**: Set up Postgres student model
5. **Week 4**: Begin Educate Mode implementation

---

**Status**: Ready to implement Phase 4A (Navigate Mode LangGraph)  
**Dependencies**: Ollama installed, LangGraph package added  
**Timeline**: 6-8 weeks to full Navigate + Educate modes
