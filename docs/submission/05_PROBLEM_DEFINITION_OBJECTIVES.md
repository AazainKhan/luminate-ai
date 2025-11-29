# 2. Problem Definition and Objectives

## Luminate AI Course Marshal

---

## 2.1 Clarity of Problem Statement

### Primary Problem Definition

**Problem**: Students in COMP 237: Introduction to AI at Centennial College lack access to an intelligent, course-specific tutoring system that can provide personalized learning assistance while maintaining academic integrity standards.

### Detailed Problem Breakdown

#### 2.1.1 The Learning Support Gap

Current educational technology fails to bridge the gap between:

```
[Static Content Delivery] ←──────────────────→ [Personalized Tutoring]
      (Blackboard LMS)                              (AI Assistant)
           │                                              │
           ▼                                              ▼
    - PDFs, Videos                               - Context-Aware
    - Fixed Sequence                             - Adaptive Difficulty
    - No Interaction                             - 24/7 Availability
    - Generic Feedback                           - Socratic Method
```

#### 2.1.2 Academic Integrity Challenge

Generic AI tools present a dual-edged problem:

| Issue | Description | Impact |
|-------|-------------|--------|
| **Over-Assistance** | ChatGPT provides complete solutions | Undermines learning and assessment validity |
| **Under-Grounding** | Generic AI lacks course context | Responses may contradict syllabus or use different approaches |
| **No Policy Enforcement** | Tools cannot distinguish graded vs. practice work | Students can bypass learning process |

#### 2.1.3 Technical Complexity Barrier

COMP 237 combines multiple challenging domains:

1. **Mathematical Foundations**: Linear algebra, calculus, probability
2. **Programming Implementation**: Python, scikit-learn, TensorFlow/PyTorch
3. **Conceptual Understanding**: Algorithm design, optimization theory
4. **Practical Application**: Model training, hyperparameter tuning

Students often struggle at the intersection of these domains, requiring a tutor that can fluidly transition between mathematical derivation, conceptual explanation, and code implementation.

### Problem Scope Boundaries

| In Scope | Out of Scope |
|----------|--------------|
| COMP 237 course content only | General AI topics not in syllabus |
| Centennial College students | External users |
| Learning assistance and guidance | Complete homework solutions |
| Concept explanation and scaffolding | Assessment grading |
| Code examples and debugging help | Exam answers or test bank access |

---

## 2.2 Objectives and Goals

### SMART Objectives Framework

The project objectives follow the SMART criteria: Specific, Measurable, Achievable, Relevant, Time-bound.

#### Primary Objectives

| # | Objective | Success Criteria | Timeline |
|---|-----------|------------------|----------|
| **O1** | Deploy a functional AI tutoring Chrome Extension | Extension loads, authenticates, and streams responses | Week 8 |
| **O2** | Achieve 100% scope enforcement accuracy | Governor blocks all out-of-scope queries | Week 10 |
| **O3** | Achieve 0% direct solution provision rate | Governor blocks all assignment solution requests | Week 10 |
| **O4** | Achieve <3 second response latency for simple queries | 95th percentile response time under threshold | Week 12 |
| **O5** | Index complete COMP 237 course content | All course materials vectorized in ChromaDB | Week 6 |

#### Secondary Objectives

| # | Objective | Success Criteria | Priority |
|---|-----------|------------------|----------|
| **S1** | Implement Socratic scaffolding for conceptual questions | Tutor asks guiding questions before revealing answers | High |
| **S2** | Enable code execution in sandbox environment | Python code runs safely via E2B | Medium |
| **S3** | Track student mastery per concept | Mastery scores update based on interactions | Medium |
| **S4** | Provide admin dashboard for faculty | Admin can upload materials and view metrics | Low |

### Measurable Goals

#### Performance Goals

```
┌─────────────────────────────────────────────────────────────────┐
│                    Response Latency Targets                      │
├─────────────────────────────────────────────────────────────────┤
│  Fast Mode (Simple Queries)      │  < 2 seconds                 │
│  Standard Mode (RAG Queries)     │  < 5 seconds                 │
│  Code Generation                 │  < 10 seconds                │
│  Code Execution (E2B)            │  < 15 seconds                │
└─────────────────────────────────────────────────────────────────┘
```

#### Quality Goals

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Response Accuracy | 95% factually correct | Manual review of sample responses |
| Source Citation Rate | 100% when using RAG | Automated logging |
| Policy Compliance | 100% | Automated testing of integrity patterns |
| User Satisfaction | 4.0/5.0 average | Post-interaction survey |

#### Technical Goals

1. **Backend API**: 99.9% uptime during term
2. **ChromaDB**: Support for 10,000+ document chunks
3. **Authentication**: Secure Supabase JWT validation
4. **Extension**: Chrome Web Store compliance (future)

---

## 2.3 Relevance and Impact

### Educational Relevance

#### Alignment with COMP 237 Learning Outcomes

The Luminate AI Course Marshal directly supports the stated learning outcomes of COMP 237:

| Course Learning Outcome | How Luminate Supports It |
|------------------------|-------------------------|
| "Explain machine learning concepts" | Socratic scaffolding elicits student explanations |
| "Implement neural networks in Python" | Code agent provides guidance without full solutions |
| "Apply mathematical foundations" | Math agent provides step-by-step derivations |
| "Evaluate model performance" | Guides students through metric interpretation |
| "Design AI solutions" | Scaffolds problem decomposition |

#### Pedagogical Framework Integration

The system integrates established educational frameworks:

1. **Bloom's Taxonomy**: Responses target appropriate cognitive level
   - Remember → Definition retrieval
   - Understand → Concept explanation
   - Apply → Guided examples
   - Analyze → Comparison prompts
   - Evaluate → Critical thinking questions
   - Create → Project scaffolding

2. **Zone of Proximal Development (Vygotsky)**:
   - Assesses current understanding
   - Provides scaffolding at appropriate level
   - Gradually reduces support as mastery increases

3. **Socratic Method**:
   - Asks clarifying questions
   - Guides discovery rather than telling
   - Builds critical thinking skills

### Technical Relevance

#### Industry-Aligned Architecture

The project implements patterns used in production AI systems:

| Pattern | Industry Example | Luminate Implementation |
|---------|-----------------|------------------------|
| RAG | OpenAI GPTs, Perplexity | ChromaDB + Gemini Embeddings |
| Multi-Agent Systems | AutoGen, CrewAI | LangGraph Governor-Supervisor |
| Policy Guardrails | Anthropic Constitutional AI | Governor Three Laws |
| Streaming Responses | ChatGPT, Claude | Server-Sent Events (SSE) |

#### Technology Stack Relevance

All technologies selected are actively maintained and industry-standard:

- **Python 3.11+**: Dominant AI development language
- **FastAPI**: Leading Python API framework
- **LangGraph**: State-of-the-art agent orchestration
- **React/TypeScript**: Industry-standard frontend
- **ChromaDB**: Popular open-source vector database
- **Supabase**: Modern Backend-as-a-Service

### Potential Impact

#### Quantitative Impact Potential

| Impact Area | Potential Outcome | Measurement |
|-------------|------------------|-------------|
| Student Support Accessibility | 24/7 availability (vs. 4 hrs/week office hours) | Hours available |
| Support Capacity | Unlimited concurrent users (vs. 1:30 ratio) | Users served |
| Response Time | Seconds (vs. hours/days for email) | Average response time |
| Consistency | 100% policy-compliant (vs. human variability) | Audit results |

#### Qualitative Impact Potential

1. **Reduced Anxiety**: Students can get help without waiting or scheduling
2. **Increased Engagement**: Interactive tutoring promotes active learning
3. **Improved Equity**: All students have equal access regardless of schedule
4. **Faculty Time Savings**: Routine questions handled automatically

#### Broader Impact

The Governor-Agent pattern developed in this project can be:

1. **Open-Sourced**: Pattern documentation for other educational institutions
2. **Extended**: Applied to other courses at Centennial College
3. **Commercialized**: Potential for EdTech product development
4. **Research Basis**: Foundation for academic papers on AI in education

### Risk Mitigation Through Design

| Risk | Mitigation in Design |
|------|---------------------|
| Over-reliance on AI | Scaffolding encourages independent thinking |
| Academic dishonesty | Governor Law 2 prevents solution provision |
| Misinformation | RAG grounds responses in verified course content |
| Data privacy | Supabase RLS, no PII in vector store |
| Accessibility | Browser-based, no special software required |

---

*This section establishes the project's clear problem definition, measurable objectives, and potential impact. The following sections detail the methodology and technical execution used to achieve these goals.*
