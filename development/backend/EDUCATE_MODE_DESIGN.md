# Educate Mode Design - Lightweight Cloud-Based Architecture

## Date: October 7, 2025

---

## Executive Summary

This document outlines the **lightweight Educate Mode implementation** for Luminate AI, optimized for performance on a laptop with:
- **Processor**: 12th Gen Intel Core i7-1255U (1.70 GHz)
- **RAM**: 16 GB
- **Approach**: Cloud-based LLMs (no local models) to keep system performant

---

## Design Philosophy

### Why Cloud-Based LLMs?

1. **No Local Resource Drain**: Using API calls instead of running Ollama/local models locally
2. **Better Performance**: Cloud LLMs (Gemini, GPT-4) are more powerful than local models
3. **Cost-Effective**: Google Gemini offers generous free tier (60 requests/minute)
4. **Faster Responses**: No model loading time
5. **Seamless Updates**: Cloud providers continuously improve models

### Architecture Choice

```
┌─────────────────────────────────────────────────────────────────┐
│              EDUCATE MODE - CLOUD-BASED ARCHITECTURE             │
└─────────────────────────────────────────────────────────────────┘

Chrome Extension                FastAPI Backend              Cloud LLM APIs
─────────────────               ────────────────             ──────────────
┌──────────────┐                ┌──────────────┐            ┌─────────────┐
│ Mode Switcher│───────────────▶│ /langgraph/  │───────────▶│Google Gemini│
│   Navigate   │                │   educate    │◀───────────│(Free Tier)  │
│   Educate    │                │              │            └─────────────┘
└──────────────┘                │ LangGraph    │
                                │ Workflow     │            ┌─────────────┐
┌──────────────┐                │              │───────────▶│  ChromaDB   │
│ Chat UI      │◀───────────────│ - Intent     │◀───────────│  (Local)    │
│ (Educate)    │                │ - Scaffolding│            └─────────────┘
└──────────────┘                │ - Socratic   │
                                │ - Retrieval  │
                                └──────────────┘
```

---

## Educate Mode Features

### Core Pedagogical Techniques

Based on educational AI research (VanLehn 2011, AutoTutor):

1. **Concept Explanation**: Clear, structured explanations with examples
2. **Scaffolding**: Gradual hints (light → medium → full)
3. **Socratic Dialogue**: Guide learning through questions
4. **Misconception Detection**: Identify and correct common errors
5. **Retrieval Practice**: Generate quiz questions
6. **Worked Examples**: Step-by-step problem solutions

### Intent Types

The system will handle 4 main student intent types:

```python
INTENT_TYPES = {
    "concept": "Student wants to understand a concept",
    "problem": "Student needs help solving a problem",
    "clarification": "Student has misconception or confusion",
    "assessment": "Student wants to test their knowledge"
}
```

---

## LangGraph Workflow Design

### Educate State

```python
class EducateState(TypedDict):
    # Input
    query: str
    conversation_history: List[Dict]
    
    # Agent outputs
    intent: str  # concept, problem, clarification, assessment
    parsed_query: Dict[str, Any]
    retrieved_context: List[Dict]  # From ChromaDB
    explanation: str
    hint_level: str  # light, medium, full
    socratic_questions: List[str]
    detected_misconception: Optional[str]
    assessment_questions: List[Dict]
    
    # Final output
    formatted_response: Dict[str, Any]
```

### Agent Workflow

```
[Student Question]
      ↓
┌──────────────────┐
│ Intent Agent       │ ← Classify query type
│ (Gemini Flash)     │   Extract key concepts
└──────────────────┘
      ↓
┌──────────────────┐
│ Retrieval Agent    │ ← Get relevant course content
│ (ChromaDB)         │   Same as Navigate mode
└──────────────────┘
      ↓
    ┌─────┴─────┐
    │           │
    ↓           ↓
┌─────────┐ ┌──────────────┐
│ Concept │ │ Problem      │
│ Explain │ │ Solving      │
└─────────┘ └──────────────┘
    │           │
    └─────┬─────┘
          ↓
┌──────────────────┐
│ Scaffolding Agent │ ← Determine appropriate hint level
│ (Gemini Flash)    │   Provide gradual support
└──────────────────┘
      ↓
┌──────────────────┐
│ Socratic Agent    │ ← Generate guiding questions
│ (Gemini Pro)      │   Encourage critical thinking
└──────────────────┘
      ↓
┌──────────────────┐
│ Formatting Agent  │ ← Structure response for UI
│                   │   Include follow-up suggestions
└──────────────────┘
      ↓
[Response to Student]
```

---

## Agent Specifications

### 1. Intent Classification Agent

**Purpose**: Determine what the student is asking for

**LLM**: Gemini 2.0 Flash (fast, accurate)

**Prompt Template**:
```
You are an educational intent classifier for COMP237 (Artificial Intelligence course).

Analyze the student's question and classify it into ONE of these categories:
1. concept - Student wants to understand a concept (e.g., "What is backpropagation?")
2. problem - Student needs help solving a problem (e.g., "How do I implement gradient descent?")
3. clarification - Student has a misconception or confusion (e.g., "I thought CNN and RNN are the same?")
4. assessment - Student wants to test knowledge (e.g., "Can you quiz me on neural networks?")

Student Question: {query}

Respond with JSON:
{
  "intent": "concept|problem|clarification|assessment",
  "key_concepts": ["concept1", "concept2"],
  "complexity_level": "beginner|intermediate|advanced",
  "reasoning": "Why you classified it this way"
}
```

### 2. Concept Explanation Agent

**Purpose**: Provide clear, structured explanations

**LLM**: Gemini 1.5 Pro (deeper reasoning)

**Prompt Template**:
```
You are an AI tutor for COMP237. Explain concepts clearly with:
1. Simple definition (1-2 sentences)
2. Why it matters (real-world context)
3. Key components or steps
4. Example from course materials
5. Common misconceptions to avoid

Use the following course content as reference:
{retrieved_context}

Student Question: {query}

Provide explanation in markdown format.
```

### 3. Problem Solving Agent

**Purpose**: Guide students through problems with scaffolding

**LLM**: Gemini 1.5 Pro

**Prompt Template**:
```
You are a problem-solving tutor. Help the student solve this problem using scaffolding:

Problem: {query}

Course Context: {retrieved_context}

Provide hints at THREE levels:
1. Light Hint: General guidance without giving away solution
2. Medium Hint: Point to specific concepts or steps
3. Full Solution: Complete worked example with explanation

Format as JSON:
{
  "light_hint": "...",
  "medium_hint": "...",
  "full_solution": {
    "steps": ["step1", "step2", ...],
    "explanation": "...",
    "code_example": "..." (if applicable)
  },
  "current_hint_level": "light"  // Start with light
}
```

### 4. Socratic Dialogue Agent

**Purpose**: Encourage critical thinking through questions

**LLM**: Gemini 1.5 Pro

**Prompt Template**:
```
You are a Socratic tutor. Instead of direct answers, ask guiding questions.

Student Question: {query}

Context: {retrieved_context}

Generate 3 guiding questions that:
1. Help student discover the answer themselves
2. Build on their current understanding
3. Connect to related concepts

Techniques:
- Pumping: "Can you elaborate on that?"
- Hinting: "Consider what happens when..."
- Analogies: "How is this similar to...?"

Format as JSON array of questions.
```

### 5. Formatting Agent

**Purpose**: Structure response for Chrome extension UI

**LLM**: Gemini 2.0 Flash (fast formatting)

**Output Structure**:
```json
{
  "response_type": "concept|problem|socratic|assessment",
  "main_content": "Primary explanation or response",
  "hints": {
    "current_level": "light|medium|full",
    "light": "...",
    "medium": "...",
    "full": "..."
  },
  "socratic_questions": ["q1", "q2", "q3"],
  "related_concepts": [
    {"title": "...", "why_explore": "..."}
  ],
  "sources": [
    {"title": "...", "url": "...", "module": "..."}
  ],
  "follow_up_suggestions": ["suggestion1", "suggestion2"],
  "misconception_alert": "..." (if detected)
}
```

---

## API Configuration

### LLM Provider Selection

Use existing `llm_config.py` with these settings:

```env
# .env configuration
LLM_PROVIDER=gemini
MODEL_NAME=gemini-2.0-flash-exp  # For fast agents
GEMINI_PRO_MODEL=gemini-1.5-pro   # For complex reasoning
GOOGLE_API_KEY=your_api_key_here

# Fallback to OpenAI if needed
OPENAI_API_KEY=your_key_here
```

### Rate Limits & Cost

**Google Gemini Free Tier**:
- 2.0 Flash: 15 RPM (requests per minute)
- 1.5 Pro: 2 RPM
- **Cost**: FREE up to limits

**OpenAI (Paid Fallback)**:
- GPT-4o-mini: $0.150 / 1M input tokens
- GPT-4o: $2.50 / 1M input tokens

---

## Implementation Plan

### Phase 1: Core Workflow (Week 1)
- [ ] Create `educate_graph.py` with LangGraph workflow
- [ ] Implement Intent Classification Agent
- [ ] Implement Concept Explanation Agent
- [ ] Add FastAPI endpoint `/langgraph/educate`

### Phase 2: Advanced Agents (Week 2)
- [ ] Implement Problem Solving Agent with scaffolding
- [ ] Implement Socratic Dialogue Agent
- [ ] Add Formatting Agent

### Phase 3: UI Integration (Week 3)
- [ ] Add mode switcher to Chrome extension
- [ ] Create Educate Mode chat interface
- [ ] Implement hint level progression UI

### Phase 4: Testing & Refinement
- [ ] Test with sample COMP237 questions
- [ ] Measure response latency
- [ ] Optimize prompts for better pedagogy

---

## Performance Considerations

### Why This Won't Slow Down Your Laptop

1. **No Local Model Loading**: All LLM inference happens on Google's servers
2. **Lightweight Backend**: FastAPI only does routing and API calls
3. **Async Operations**: Non-blocking API calls
4. **Cached Retrieval**: ChromaDB queries are fast (already local)
5. **Minimal Memory**: Only stores conversation context (few KB per session)

### Expected Resource Usage

- **RAM**: ~200 MB for FastAPI service (negligible)
- **CPU**: <5% during API calls
- **Network**: ~5-10 KB per request/response
- **Disk**: Only ChromaDB storage (already exists)

---

## Success Metrics

1. **Response Time**: <3 seconds for concept explanations
2. **Accuracy**: >90% correct intent classification
3. **Student Engagement**: Multiple follow-up questions per session
4. **Learning Effectiveness**: Improved quiz performance (future metric)

---

## Next Steps

1. Create `educate_graph.py` with agent implementations
2. Add educate endpoint to FastAPI
3. Update Chrome extension with mode switcher
4. Test with real COMP237 questions

---

## References

- VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems.
- Graesser et al. (2004). AutoTutor: A tutor with dialogue in natural language.
- Wood et al. (1976). The role of tutoring in problem solving.
- Google Gemini API: https://ai.google.dev/
