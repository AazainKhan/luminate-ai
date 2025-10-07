"""
Socratic Dialogue Agent for Educate Mode

Purpose: Guide learning through questions instead of direct answers
Uses: Google Gemini 1.5 Pro (complex dialogue generation)
"""

from typing import Dict, Any, List
from llm_config import get_llm


def socratic_dialogue_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Socratic questions to guide student learning.
    
    Techniques (Graesser et al., 2014):
    - Pumping: "Can you elaborate on that?"
    - Hinting: "Consider what happens when..."
    - Analogies: "How is this similar to...?"
    - Reflection: "Why do you think that?"
    
    Args:
        state: Workflow state
        
    Returns:
        Updated state with 'socratic_questions'
    """
    query = state.get("query", "")
    parsed_query = state.get("parsed_query", {})
    retrieved_context = state.get("retrieved_context", [])
    intent = state.get("intent", "concept")
    
    # Build context
    context_text = "\n".join([
        f"{chunk.get('title', '')}: {chunk.get('text', '')[:300]}"
        for chunk in retrieved_context[:3]
    ]) if retrieved_context else ""
    
    # Get key concepts
    key_concepts = parsed_query.get("key_concepts", [])
    concepts_str = ", ".join(key_concepts) if key_concepts else "the topic"
    
    prompt = f"""You are a Socratic tutor following the teaching method of asking questions rather than giving direct answers.

Student Question: "{query}"
Key Concepts: {concepts_str}
Learning Context: {intent}

Course Content:
{context_text}

Generate 3-4 guiding questions that help the student discover the answer themselves.

Use these Socratic techniques:

1. **Pumping**: Encourage elaboration ("Can you explain more about...", "What do you mean by...")
2. **Hinting**: Point toward key concepts ("What happens when...", "Consider how X affects Y...")
3. **Analogies**: Connect to familiar concepts ("How is this similar to...", "Think about...")
4. **Reflection**: Encourage metacognition ("Why do you think...", "What would happen if...")
5. **Decomposition**: Break down complex topics ("Let's start with...", "First, what is...")

Guidelines:
- Questions should build on each other (scaffolding)
- Don't give away the answer
- Make student think critically
- Connect to what they already know
- Be encouraging and supportive

Respond with ONLY valid JSON (no markdown, no backticks):
{{
  "questions": [
    {{
      "question": "First guiding question",
      "technique": "pumping|hinting|analogy|reflection|decomposition",
      "purpose": "What this question helps student discover"
    }},
    {{
      "question": "Second guiding question",
      "technique": "...",
      "purpose": "..."
    }},
    {{
      "question": "Third guiding question",
      "technique": "...",
      "purpose": "..."
    }}
  ],
  "learning_goal": "What student should discover through these questions",
  "encouragement": "Brief encouraging message"
}}"""
    
    try:
        llm = get_llm(
            temperature=0.6,  # Higher creativity for diverse questions
            model="gemini-1.5-pro"
        )
        
        import json
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean response
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join([
                line for line in lines 
                if not line.strip().startswith("```")
            ])
        
        socratic_data = json.loads(response_text)
        
        print(f"🤔 Generated {len(socratic_data.get('questions', []))} Socratic questions")
        
        return {
            **state,
            "socratic_questions": socratic_data.get("questions", []),
            "learning_goal": socratic_data.get("learning_goal", ""),
            "encouragement": socratic_data.get("encouragement", "")
        }
        
    except Exception as e:
        print(f"⚠️  Socratic dialogue error: {e}")
        
        # Fallback questions
        fallback_questions = [
            {
                "question": f"What do you already know about {concepts_str}?",
                "technique": "reflection",
                "purpose": "Activate prior knowledge"
            },
            {
                "question": f"How would you explain {concepts_str} in your own words?",
                "technique": "pumping",
                "purpose": "Encourage articulation"
            },
            {
                "question": "What examples from the course materials relate to this?",
                "technique": "hinting",
                "purpose": "Connect to resources"
            }
        ]
        
        return {
            **state,
            "socratic_questions": fallback_questions,
            "learning_goal": "Build understanding through self-discovery",
            "encouragement": "Take your time thinking through these questions!",
            "error": str(e)
        }


def clarification_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect misconceptions and provide tailored clarification.
    
    Based on AutoTutor's expectation-misconception approach.
    
    Args:
        state: Workflow state
        
    Returns:
        Updated state with clarification
    """
    query = state.get("query", "")
    parsed_query = state.get("parsed_query", {})
    retrieved_context = state.get("retrieved_context", [])
    
    # Build context
    context_text = "\n".join([
        f"{chunk.get('title', '')}: {chunk.get('text', '')[:400]}"
        for chunk in retrieved_context[:3]
    ]) if retrieved_context else ""
    
    prompt = f"""You are an expert tutor detecting and correcting misconceptions.

Student Query: "{query}"

Course Content:
{context_text}

Analyze the student's question/statement for common misconceptions:

1. Identify any misconceptions present
2. Explain why it's a misconception
3. Provide correct understanding
4. Give examples to clarify
5. Suggest how to avoid this confusion

Common AI Course Misconceptions:
- Confusing ML algorithms (e.g., supervised vs unsupervised)
- Misunderstanding neural network concepts
- Mixing up terminology
- Incorrect assumptions about how algorithms work

Respond with ONLY valid JSON (no markdown, no backticks):
{{
  "misconception_detected": true/false,
  "misconception_description": "What the student likely misunderstands",
  "correct_understanding": "The accurate concept explained clearly",
  "explanation": "Why this misconception occurs and how to think about it correctly",
  "examples": ["Example 1 showing correct concept", "Example 2..."],
  "prevention_tips": ["Tip 1", "Tip 2"],
  "related_correct_concepts": ["Concept 1", "Concept 2"]
}}"""
    
    try:
        llm = get_llm(
            temperature=0.3,
            model="gemini-1.5-pro"
        )
        
        import json
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean response
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join([
                line for line in lines 
                if not line.strip().startswith("```")
            ])
        
        clarification_data = json.loads(response_text)
        
        # Build explanation from clarification data
        if clarification_data.get("misconception_detected"):
            explanation = f"""## ⚠️ Let's Clarify This

**Misconception**: {clarification_data.get('misconception_description', '')}

**Correct Understanding**: 
{clarification_data.get('correct_understanding', '')}

**Why This Matters**:
{clarification_data.get('explanation', '')}

**Examples**:
{chr(10).join(f"- {ex}" for ex in clarification_data.get('examples', []))}

**How to Remember**:
{chr(10).join(f"✓ {tip}" for tip in clarification_data.get('prevention_tips', []))}
"""
        else:
            explanation = f"""Your understanding seems on track! Let me provide some additional clarity:

{clarification_data.get('correct_understanding', '')}

{clarification_data.get('explanation', '')}
"""
        
        print(f"🔍 Misconception detected: {clarification_data.get('misconception_detected')}")
        
        return {
            **state,
            "clarification_data": clarification_data,
            "explanation": explanation,
            "response_type": "clarification"
        }
        
    except Exception as e:
        print(f"⚠️  Clarification agent error: {e}")
        
        fallback = f"""Let me help clarify your question about: "{query}"

Based on the course materials, here's what you should know:

{context_text[:500]}

If you're still confused, try asking:
- "What's the difference between [concept A] and [concept B]?"
- "Can you give an example of [concept]?"
- "Why does [specific aspect] work this way?"

I'm here to help clear up any confusion!"""
        
        return {
            **state,
            "clarification_data": {
                "misconception_detected": False,
                "correct_understanding": fallback
            },
            "explanation": fallback,
            "response_type": "clarification",
            "error": str(e)
        }


def assessment_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate practice questions for retrieval practice.
    
    Based on Roediger & Karpicke (2006) - retrieval practice enhances retention.
    
    Args:
        state: Workflow state
        
    Returns:
        Updated state with assessment questions
    """
    query = state.get("query", "")
    parsed_query = state.get("parsed_query", {})
    retrieved_context = state.get("retrieved_context", [])
    key_concepts = parsed_query.get("key_concepts", [])
    
    # Build context
    context_text = "\n".join([
        f"{chunk.get('title', '')}: {chunk.get('text', '')[:400]}"
        for chunk in retrieved_context[:3]
    ]) if retrieved_context else ""
    
    concepts_str = ", ".join(key_concepts) if key_concepts else "COMP237 topics"
    
    prompt = f"""You are creating practice questions for retrieval practice (Roediger & Karpicke, 2006).

Student Request: "{query}"
Focus Areas: {concepts_str}

Course Content:
{context_text}

Generate 5 practice questions at different difficulty levels:
- 2 easy (factual recall)
- 2 medium (conceptual understanding)
- 1 hard (application/analysis)

For each question, include:
- The question
- Difficulty level
- Correct answer
- Brief explanation

Respond with ONLY valid JSON (no markdown, no backticks):
{{
  "questions": [
    {{
      "question": "Question text here?",
      "difficulty": "easy|medium|hard",
      "type": "multiple_choice|short_answer|true_false",
      "options": ["A", "B", "C", "D"] (if multiple choice),
      "correct_answer": "The answer",
      "explanation": "Why this is correct"
    }}
  ],
  "learning_objectives": ["Objective 1", "Objective 2"],
  "study_tips": ["Tip 1", "Tip 2"]
}}"""
    
    try:
        llm = get_llm(
            temperature=0.4,
            model="gemini-1.5-pro"
        )
        
        import json
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean response
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join([
                line for line in lines 
                if not line.strip().startswith("```")
            ])
        
        assessment_data = json.loads(response_text)
        
        # Build explanation
        questions_list = "\n\n".join([
            f"**Question {i+1}** ({q.get('difficulty', 'medium').upper()})\n{q.get('question', '')}\n\n"
            f"{'Options: ' + str(q.get('options', [])) if q.get('type') == 'multiple_choice' else ''}"
            for i, q in enumerate(assessment_data.get('questions', []))
        ])
        
        explanation = f"""## 📝 Practice Questions on {concepts_str}

{questions_list}

*Scroll down to see answers and explanations...*

---

## ✅ Answers & Explanations

{chr(10).join([
    f"**Q{i+1}**: {q.get('correct_answer', '')}\n{q.get('explanation', '')}\n"
    for i, q in enumerate(assessment_data.get('questions', []))
])}

**Study Tips**:
{chr(10).join(f"- {tip}" for tip in assessment_data.get('study_tips', []))}
"""
        
        print(f"📝 Generated {len(assessment_data.get('questions', []))} assessment questions")
        
        return {
            **state,
            "assessment_questions": assessment_data.get("questions", []),
            "explanation": explanation,
            "response_type": "assessment"
        }
        
    except Exception as e:
        print(f"⚠️  Assessment agent error: {e}")
        
        fallback = f"""I'd love to quiz you on {concepts_str}!

Here are some questions to consider:

1. What is the main purpose of {concepts_str}?
2. How does it compare to related concepts?
3. Can you give a real-world example?
4. What are common mistakes when applying this?
5. How would you explain this to someone new?

Try answering these, then review the course materials to check your understanding!"""
        
        return {
            **state,
            "assessment_questions": [],
            "explanation": fallback,
            "response_type": "assessment",
            "error": str(e)
        }
