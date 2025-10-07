"""
Intent Classification Agent for Educate Mode

Purpose: Analyze student questions and classify intent type
Uses: Google Gemini 2.0 Flash (fast, accurate classification)
"""

import json
from typing import Dict, Any
from llm_config import get_llm


def intent_classification_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify the student's query intent.
    
    Intent Types:
    - concept: Student wants to understand a concept
    - problem: Student needs help solving a problem
    - clarification: Student has misconception or confusion
    - assessment: Student wants to test knowledge
    
    Args:
        state: Current workflow state with 'query'
        
    Returns:
        Updated state with 'intent' and 'parsed_query'
    """
    query = state.get("query", "")
    conversation_history = state.get("conversation_history", [])
    
    # Build context from conversation history
    history_context = ""
    if conversation_history:
        recent_messages = conversation_history[-3:]  # Last 3 exchanges
        history_context = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in recent_messages
        ])
    
    # Prompt for intent classification
    prompt = f"""You are an educational intent classifier for COMP237 (Artificial Intelligence course).

Analyze the student's question and classify it into ONE of these categories:

1. **concept** - Student wants to understand a concept or theory
   Examples: "What is backpropagation?", "Explain gradient descent", "How does CNN work?"

2. **problem** - Student needs help solving a problem or implementing something
   Examples: "How do I implement this algorithm?", "I'm stuck on assignment 2", "Debug my code"

3. **clarification** - Student has a misconception or needs clarification
   Examples: "I thought CNN and RNN are the same?", "Why doesn't this work?", "Confused about..."

4. **assessment** - Student wants to test their knowledge
   Examples: "Quiz me on neural networks", "Test my understanding", "Practice questions"

{f"Previous Conversation Context:\\n{history_context}\\n" if history_context else ""}
Current Student Question: {query}

Analyze the question and respond with ONLY valid JSON (no markdown, no backticks):
{{
  "intent": "concept|problem|clarification|assessment",
  "key_concepts": ["concept1", "concept2"],
  "complexity_level": "beginner|intermediate|advanced",
  "reasoning": "Brief explanation of why you classified it this way",
  "is_followup": true/false
}}"""
    
    try:
        # Use Gemini 2.0 Flash for fast classification
        llm = get_llm(
            temperature=0.1,  # Low temperature for consistent classification
            model="gemini-2.0-flash-exp"
        )
        
        response = llm.invoke(prompt)
        
        # Parse response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean response (remove markdown if present)
        response_text = response_text.strip()
        if response_text.startswith("```"):
            # Remove markdown code blocks
            lines = response_text.split("\n")
            response_text = "\n".join([
                line for line in lines 
                if not line.strip().startswith("```")
            ])
        
        parsed_query = json.loads(response_text)
        
        # Validate intent
        valid_intents = ["concept", "problem", "clarification", "assessment"]
        if parsed_query.get("intent") not in valid_intents:
            parsed_query["intent"] = "concept"  # Default fallback
        
        print(f"📊 Intent Classification: {parsed_query['intent']} | Concepts: {parsed_query['key_concepts']}")
        
        return {
            **state,
            "intent": parsed_query["intent"],
            "parsed_query": parsed_query,
            "original_query": query
        }
        
    except Exception as e:
        print(f"⚠️  Intent classification error: {e}")
        # Fallback: simple keyword-based classification
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["quiz", "test", "practice", "assess"]):
            intent = "assessment"
        elif any(word in query_lower for word in ["how to", "implement", "code", "stuck", "help"]):
            intent = "problem"
        elif any(word in query_lower for word in ["confused", "don't understand", "clarify", "why"]):
            intent = "clarification"
        else:
            intent = "concept"
        
        return {
            **state,
            "intent": intent,
            "parsed_query": {
                "intent": intent,
                "key_concepts": [],
                "complexity_level": "intermediate",
                "reasoning": "Fallback classification due to API error",
                "is_followup": False
            },
            "original_query": query
        }
