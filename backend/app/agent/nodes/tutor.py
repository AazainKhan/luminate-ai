"""
Tutor Node - LearnLM-aligned Socratic tutoring

Handles:
- explain: Full scaffolding with escalation levels (DEFAULT)
- code: Programming help with scaffolding

NOTE: No "quick" task type - ALL questions benefit from scaffolding.
This aligns with LearnLM: "Inspire active learning"

Uses Docker ChromaDB for RAG retrieval.
Includes proper Langfuse v3 tracing with nested spans.
"""

import logging
import time
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.state import AgentState
from app.agent.schemas import TaskType
from app.agent.tools.rag import get_rag_retriever
from app.agent.prompts import (
    TUTOR_SYSTEM_PROMPT,
    CODE_PROMPT,
    OUT_OF_SCOPE_PROMPT,
)
from app.config import settings
from app.observability import get_langfuse_client, calculate_cost

logger = logging.getLogger(__name__)

# Source selection prompt for intelligent filtering
SOURCE_SELECTION_PROMPT = """You are evaluating sources for relevance to a student question about AI/ML.

STUDENT QUESTION: {question}

RETRIEVED SOURCES:
{sources}

TASK: Evaluate each source and rank them by relevance to answering the student's question.

For each source, respond with a JSON array where each object has:
- "index": The source number (1-based)
- "relevant": true/false - Is this source directly relevant to the question?
- "reasoning": Brief (1 sentence) explanation of why/why not
- "priority": "high", "medium", or "low"

Only include sources that are ACTUALLY relevant. Prioritize:
1. Sources that directly explain the concept asked about
2. Sources with specific examples or definitions
3. Visual aids (images/diagrams) that illustrate the concept
4. Video lectures covering the topic

Respond with ONLY the JSON array, no other text."""


def _intelligent_source_selection(
    query: str, 
    docs: list, 
    sources: list,
    langfuse: Any = None
) -> tuple[list, list, dict]:
    """
    Use LLM to intelligently select the most relevant sources for the query.
    
    Returns:
        tuple: (filtered_docs, filtered_sources, selection_reasoning)
    """
    if not docs or len(docs) <= 3:
        # Not enough sources to filter - return as-is
        return docs, sources, {"method": "no-filter", "reason": "too_few_sources"}
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Build source descriptions for the prompt
        source_descriptions = []
        for i, (doc, source) in enumerate(zip(docs[:8], sources[:8]), 1):  # Max 8 sources to evaluate
            source_type = doc.get("source_type", "course")
            title = source.title if hasattr(source, 'title') else doc.get("title", "Unknown")
            module = doc.get("module", "")
            week = doc.get("week", "")
            content_preview = doc.get("content", "")[:200]
            
            desc = f"""
SOURCE {i}:
- Title: {title}
- Type: {source_type}
- Module: {module}, Week: {week}
- Content Preview: {content_preview}...
"""
            source_descriptions.append(desc)
        
        prompt = SOURCE_SELECTION_PROMPT.format(
            question=query,
            sources="\n".join(source_descriptions)
        )
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            google_api_key=settings.google_api_key,
        )
        
        # Run with tracing if available (synchronous invoke)
        if langfuse:
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="source_selection",
                input={"query": query, "source_count": len(docs)},
            ) as span:
                response = llm.invoke([
                    HumanMessage(content=prompt)
                ])
                span.update(output={"response": response.content[:500]})
        else:
            response = llm.invoke([
                HumanMessage(content=prompt)
            ])
        
        # Parse the JSON response
        import json
        import re
        
        response_text = response.content.strip()
        # Extract JSON from response (handle potential markdown code blocks)
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            selections = json.loads(json_match.group())
        else:
            logger.warning(f"[SourceSelection] Could not parse JSON response: {response_text[:200]}")
            return docs, sources, {"method": "parse-failed", "reason": "invalid_json"}
        
        # Filter to relevant sources
        filtered_docs = []
        filtered_sources = []
        selection_reasoning = {
            "method": "llm-selection",
            "evaluated": len(docs),
            "selected": 0,
            "reasons": []
        }
        
        for selection in selections:
            idx = selection.get("index", 0) - 1  # Convert to 0-based
            if 0 <= idx < len(docs) and selection.get("relevant", False):
                priority = selection.get("priority", "medium")
                if priority in ["high", "medium"]:  # Only include high/medium priority
                    filtered_docs.append(docs[idx])
                    filtered_sources.append(sources[idx])
                    selection_reasoning["reasons"].append({
                        "source": idx + 1,
                        "title": docs[idx].get("title", "Unknown")[:40],
                        "priority": priority,
                        "reasoning": selection.get("reasoning", "")[:100]
                    })
        
        selection_reasoning["selected"] = len(filtered_docs)
        
        # Ensure we have at least some sources
        if len(filtered_docs) < 2:
            # Fall back to top sources by score
            logger.info(f"[SourceSelection] Too few selected ({len(filtered_docs)}), using top by score")
            return docs[:3], sources[:3], {"method": "fallback", "reason": "too_few_selected"}
        
        logger.info(f"[SourceSelection] Selected {len(filtered_docs)}/{len(docs)} sources via LLM")
        return filtered_docs, filtered_sources, selection_reasoning
        
    except Exception as e:
        logger.warning(f"[SourceSelection] LLM selection failed: {e}")
        # Fall back to original sources
        return docs, sources, {"method": "error", "reason": str(e)}


def _format_history(conversation_history: list) -> str:
    """Format conversation history for prompt"""
    if not conversation_history:
        return "No previous conversation."
    
    lines = []
    for msg in conversation_history[-6:]:  # Last 6 messages
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"Student: {content}")
        else:
            lines.append(f"AI Tutor: {content}")
    
    return "\n".join(lines)


def _get_mastery_context(user_id: str, detected_concept: str = None) -> str:
    """Get student mastery context for the prompt.
    
    Returns a human-readable mastery summary from Supabase.
    """
    if not user_id:
        return "Unknown (not logged in) - Use diagnostic questions"
    
    try:
        from app.services.mastery import get_mastery_context_sync
        return get_mastery_context_sync(user_id, detected_concept)
    except Exception as e:
        logger.warning(f"Failed to get mastery context: {e}")
        if detected_concept:
            return f"Topic: {detected_concept.replace('_', ' ').title()} - Use scaffolding approach"
        return "No prior mastery data - start with diagnostic questions"


def tutor_node(state: AgentState) -> Dict[str, Any]:
    """
    Tutor node: generates educational response with scaffolding
    
    Handles explain and code tasks (no "quick" - all questions get scaffolding).
    Uses RAG for course context retrieval.
    Includes proper Langfuse v3 tracing with nested spans.
    """
    query = state.get("query", "")
    user_id = state.get("user_id", "")
    plan = state.get("plan", {})
    subtasks = plan.get("subtasks", [])
    current_subtask = subtasks[0] if subtasks else {}
    
    task = current_subtask.get("task", "explain")
    payload = current_subtask.get("payload", {})
    
    escalation_level = state.get("escalation_level", 1)
    conversation_history = state.get("conversation_history", [])
    
    logger.info(f"[Tutor] Task: {task}, Escalation: {escalation_level}")
    
    # Get Langfuse client for tracing
    langfuse = get_langfuse_client()
    start_time = time.time()
    
    # Wrap entire node in a chain span for Agent Graph visualization
    if langfuse:
        try:
            with langfuse.start_as_current_observation(
                as_type="chain",
                name="tutor_node",
                input={"query": query, "task": task, "escalation_level": escalation_level},
                metadata={"node": "tutor", "version": "v3"}
            ) as node_span:
                return _execute_tutor_logic(state, langfuse)
        except Exception as e:
            logger.error(f"[Tutor] Error with tracing: {e}")
            # Fallback to non-traced execution if tracing fails
            return _execute_tutor_logic(state, None)
    else:
        return _execute_tutor_logic(state, None)


def _execute_tutor_logic(state: AgentState, langfuse: Any) -> Dict[str, Any]:
    """Core tutor logic separated for cleaner tracing wrapper"""
    query = state.get("query", "")
    user_id = state.get("user_id", "")
    plan = state.get("plan", {})
    subtasks = plan.get("subtasks", [])
    current_subtask = subtasks[0] if subtasks else {}
    
    task = current_subtask.get("task", "explain")
    payload = current_subtask.get("payload", {})
    
    escalation_level = state.get("escalation_level", 1)
    conversation_history = state.get("conversation_history", [])

    # Get mastery context for personalization
    mastery_context = _get_mastery_context(user_id)
    
    # Get RAG context with tracing
    try:
        retriever = get_rag_retriever()
        
        # Use context manager pattern for Langfuse v3 span tracing
        if langfuse:
            # Use context propagation from root span, not trace_context
            with langfuse.start_as_current_observation(
                as_type="retriever",
                name="rag_retrieval",
                input={"query": query, "k": 8},  # Retrieve more for intelligent filtering
                metadata={"retriever": "chromadb", "collections": "auto-detect"}
            ) as rag_span:
                # Let RAG auto-detect if OER is needed based on query content
                docs, rag_metadata = retriever.retrieve(query, k=8)  # Get more sources for filtering
                sources = retriever.docs_to_sources(docs)
                
                # Intelligent source selection (filters down to most relevant)
                docs, sources, selection_info = _intelligent_source_selection(
                    query, docs, sources, langfuse
                )
                
                # Now format context with filtered sources
                context_str = retriever.format_context(docs)
                
                # Update span with output
                rag_span.update(
                    output={
                        "docs_retrieved": len(docs),
                        "has_comp237": rag_metadata.has_comp237 if rag_metadata else False,
                        "sources": [s.title for s in sources[:3]] if sources else [],
                        "used_oer": any(s.source_type == "oer" for s in sources) if sources else False,
                        "used_embedded": any(s.source_type == "embedded" for s in sources) if sources else False,
                        "source_selection": selection_info
                    }
                )
        else:
            # No Langfuse - run without tracing (auto-detect OER usage)
            docs, rag_metadata = retriever.retrieve(query, k=8)
            sources = retriever.docs_to_sources(docs)
            
            # Intelligent source selection
            docs, sources, selection_info = _intelligent_source_selection(
                query, docs, sources, None
            )
            
            context_str = retriever.format_context(docs)
            
    except Exception as e:
        logger.error(f"[Tutor] RAG failed: {e}")
        docs = []
        rag_metadata = None
        context_str = "No course context available."
        sources = []
        selection_info = {"method": "error", "reason": str(e)}
    
    # Format history
    history_str = _format_history(conversation_history)
    
    # Check if RAG returned COMP237 context
    has_comp237 = rag_metadata.has_comp237 if rag_metadata else False
    
    # Select prompt based on task type (NO QUICK - everything gets scaffolding)
    if task == TaskType.CODE.value or task == "code":
        language = payload.get("language", "python")
        prompt = CODE_PROMPT.format(
            context=context_str,
            request=query,
            language=language,
            mastery_context=mastery_context,
            escalation_level=escalation_level,
        )
    elif not has_comp237:
        # Out of scope - no COMP237 context found
        prompt = OUT_OF_SCOPE_PROMPT.format(question=query)
    else:
        # Default: explain with scaffolding (this is the main path)
        prompt = TUTOR_SYSTEM_PROMPT.format(
            escalation_level=escalation_level,
            mastery_context=mastery_context,
            context=context_str,
            history=history_str,
            question=query,
        )
    
    # Generate response with tracing
    try:
        model_name = "gemini-2.5-flash"
        temperature = 0.7 if task == "explain" else 0.3
        
        # Enable thinking support for reasoning display
        # LangChain returns thinking as: [{'type': 'thinking', 'thinking': '...'}, {'type': 'text', 'text': '...'}]
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=settings.google_api_key,
            include_thoughts=True,  # Enable Gemini thinking/reasoning
        )
        
        messages = [HumanMessage(content=prompt)]
        
        # Log prompt details for debugging
        logger.debug(f"[Tutor] Prompt length: {len(prompt)} chars")
        logger.debug(f"[Tutor] Task: {task}, Escalation: {escalation_level}, Has COMP237: {has_comp237}")
        
        # Use context manager pattern for Langfuse v3 generation tracing
        if langfuse:
            # Use context propagation from root span, not trace_context
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="tutor_generation",
                model=model_name,
                model_parameters={"temperature": temperature, "include_thoughts": True},
                input={
                    "prompt_template": "TUTOR_SYSTEM_PROMPT" if task != "code" else "CODE_PROMPT",
                    "escalation_level": escalation_level,
                    "task": task,
                    "has_context": bool(context_str and len(context_str) > 50),
                    "history_turns": len(conversation_history),
                    "query": query,
                    "prompt_preview": prompt[:1000] + "..." if len(prompt) > 1000 else prompt
                },
                metadata={
                    "task": task,
                    "escalation_level": escalation_level,
                    "has_comp237_context": has_comp237,
                    "context_length": len(context_str) if context_str else 0,
                    "history_length": len(conversation_history),
                }
            ) as generation:
                response = llm.invoke(messages)
                
                # Debug: Log response structure
                logger.debug(f"[Tutor] Response type: {type(response.content)}")
                logger.debug(f"[Tutor] Response metadata: {response.response_metadata}")
                if isinstance(response.content, list):
                    logger.debug(f"[Tutor] Response content parts: {[p.get('type') if isinstance(p, dict) else 'string' for p in response.content]}")
                
                # Parse response content - with include_thoughts=True, content may be a list
                # Format: [{'type': 'thinking', 'thinking': '...'}, {'type': 'text', 'text': '...'}]
                response_text = ""
                reasoning_text = ""
                
                if isinstance(response.content, list):
                    for part in response.content:
                        if isinstance(part, dict):
                            if part.get("type") == "thinking":
                                reasoning_text = part.get("thinking", "")
                            elif part.get("type") == "text":
                                response_text = part.get("text", "").strip()
                        elif isinstance(part, str):
                            response_text = part.strip()
                else:
                    response_text = response.content.strip() if response.content else ""
                
                # Calculate usage and cost - extract from Gemini response metadata
                # Gemini uses different key names in response_metadata
                usage_metadata = response.response_metadata.get("usage_metadata", {})
                input_tokens = usage_metadata.get("prompt_token_count") or usage_metadata.get("input_tokens", 0)
                output_tokens = usage_metadata.get("candidates_token_count") or usage_metadata.get("output_tokens", 0)
                
                # Log for debugging
                logger.debug(f"[Tutor] Token usage: input={input_tokens}, output={output_tokens}")
                logger.debug(f"[Tutor] Full usage_metadata: {usage_metadata}")
                
                cost_info = calculate_cost(model_name, input_tokens, output_tokens)
                
                # Log response details for debugging
                logger.info(f"[Tutor] Response: {len(response_text)} chars, {input_tokens}+{output_tokens} tokens")
                if len(response_text) < 100:
                    logger.warning(f"[Tutor] SHORT RESPONSE: '{response_text}'")
                
                # Log reasoning if present
                if reasoning_text:
                    logger.info(f"[Tutor] Reasoning: {len(reasoning_text)} chars")
                
                # Update generation with full output and usage
                generation.update(
                    output={
                        "response": response_text,
                        "reasoning": reasoning_text[:500] if reasoning_text else None,
                        "response_length": len(response_text),
                        "reasoning_length": len(reasoning_text) if reasoning_text else 0,
                        "finish_reason": response.response_metadata.get("finish_reason", "unknown"),
                    },
                    usage_details={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens,
                    },
                )
        else:
            # No Langfuse - run without tracing
            response = llm.invoke(messages)
            
            # Parse response content for non-Langfuse path
            response_text = ""
            reasoning_text = ""
            
            if isinstance(response.content, list):
                for part in response.content:
                    if isinstance(part, dict):
                        if part.get("type") == "thinking":
                            reasoning_text = part.get("thinking", "")
                        elif part.get("type") == "text":
                            response_text = part.get("text", "").strip()
                    elif isinstance(part, str):
                        response_text = part.strip()
            else:
                response_text = response.content.strip() if response.content else ""
                
            input_tokens = response.response_metadata.get("usage_metadata", {}).get("prompt_token_count", 0)
            output_tokens = response.response_metadata.get("usage_metadata", {}).get("candidates_token_count", 0)
        
        logger.info(f"[Tutor] Generated {len(response_text)} chars, {input_tokens}+{output_tokens} tokens")
        
        # Convert rag_metadata to dict if it's a Pydantic model
        rag_meta_dict = rag_metadata.model_dump() if rag_metadata else {"docs_retrieved": 0, "retrieval_success": False}
        
        # Get source selection info (should always exist after RAG step)
        source_selection = selection_info if selection_info else {"method": "default"}
        
        return {
            **state,
            "response": response_text,
            "reasoning": reasoning_text,  # Add reasoning to state for streaming
            "sources": [s.model_dump() for s in sources],
            "retrieved_docs": docs,
            "rag_metadata": rag_meta_dict,
            "context_str": context_str,
            "source_selection": source_selection,  # Include selection reasoning
        }
        
    except Exception as e:
        logger.error(f"[Tutor] Generation failed: {e}")
        return {
            **state,
            "response": "I encountered an error while processing your question. Please try again.",
            "error": str(e),
            "sources": [],
            "rag_metadata": {"docs_retrieved": 0, "retrieval_success": False},
        }
