"""
Sub-Agents for Course Marshal
Specialized agents for different tasks
"""

from typing import Dict, List, Optional
import logging
import time
from app.agents.state import AgentState
from app.agents.supervisor import Supervisor
from app.rag.langchain_chroma import get_langchain_chroma_client
from app.agents.source_metadata import (
    extract_sources,
    format_sources_for_response,
    normalize_rag_results,
    Source
)
from app.observability.langfuse_client import create_child_span_from_state

logger = logging.getLogger(__name__)


class SyllabusAgent:
    """Agent for syllabus and course logistics queries"""
    
    def __init__(self):
        self.vectorstore = get_langchain_chroma_client()
        self.supervisor = Supervisor()
    
    def check_syllabus(self, query: str) -> Dict[str, any]:
        """
        Check syllabus for course information
        
        Args:
            query: User query
            
        Returns:
            Dictionary with syllabus information
        """
        try:
            results = self.vectorstore.retrieve_with_metadata(
                query=query,
                k=5,
                filter={"content_type": "syllabus"}
            )
            if results:
                summaries = self.vectorstore.summarize_sources(results)
                return {
                    "found": True,
                    "sources": summaries,
                    "content": [record["content"] for record in results],
                }
            
            return {"found": False}
        except Exception as e:
            logger.error(f"Error checking syllabus: {e}")
            return {"found": False, "error": str(e)}


class RAGAgent:
    """Agent for RAG retrieval and context prioritization"""
    
    def __init__(self):
        self.vectorstore = get_langchain_chroma_client()
    
    def retrieve_context(self, query: str, course_id: str = "COMP237", state: Optional[AgentState] = None) -> List[Dict]:
        """
        Retrieve relevant context from ChromaDB using LangChain.
        
        Now instrumented with Langfuse span for observability.
        """
        start_time = time.time()
        span = None
        
        try:
            # Create Langfuse span if state is available
            if state:
                span = create_child_span_from_state(
                    state=state, 
                    name="rag_retrieval",
                    input_data={"query": query, "course_id": course_id, "k": 5},
                    metadata={"span_type": "TOOL"}
                )
            
            records = self.vectorstore.retrieve_with_metadata(
                query=query,
                k=5,
                filter={"course_id": course_id}
            )
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"✅ Retrieved {len(records)} documents for query ({duration_ms:.0f}ms)")
            
            # Update span with results
            if span:
                source_filenames = [r.get("source_filename", "unknown") for r in records]
                span.update(
                    output={
                        "documents_retrieved": len(records),
                        "source_files": source_filenames,
                        "duration_ms": round(duration_ms, 2)
                    },
                    level="DEFAULT"
                )
                span.end()
            
            return records
            
        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            if span:
                span.update(output={"error": str(e)}, level="ERROR")
                span.end()
            return []
    
    def summarize_sources(self, records: List[Dict]) -> List[Dict]:
        """Summarize retrieval results into unique sources"""
        return self.vectorstore.summarize_sources(records)


def rag_node(state: AgentState) -> AgentState:
    """
    RAG retrieval node
    Retrieves relevant context from ChromaDB
    Now instrumented with Langfuse spans.
    """
    rag_agent = RAGAgent()
    # Use effective_query (contextualized) if available, otherwise original query
    query = state.get("effective_query") or state.get("query", "")
    
    # Pass state for Langfuse span creation
    retrieved = rag_agent.retrieve_context(query, state=state)
    source_summaries = rag_agent.summarize_sources(retrieved)
    
    state["retrieved_context"] = retrieved
    state["context_sources"] = source_summaries
    
    return state


def syllabus_node(state: AgentState) -> AgentState:
    """
    Syllabus check node
    Checks syllabus for course information
    """
    syllabus_agent = SyllabusAgent()
    # Use effective_query (contextualized) if available, otherwise original query
    query = state.get("effective_query") or state.get("query", "")
    
    syllabus_info = syllabus_agent.check_syllabus(query)
    state["syllabus_check"] = syllabus_info
    
    return state


def generate_response_node(state: AgentState) -> AgentState:
    """
    Generate response using selected model and retrieved context
    """
    supervisor = Supervisor()
    model_name = state.get("model_selected", "gemini-flash")
    model = supervisor.get_model(model_name)
    
    # Use effective_query (contextualized) if available, otherwise original query
    query = state.get("effective_query") or state.get("query", "")
    retrieved_context = state.get("retrieved_context", [])
    context_sources = state.get("context_sources", [])
    
    # Use standardized source extraction
    sources = extract_sources(retrieved_context)
    
    # Build context string from normalized results
    normalized = normalize_rag_results(retrieved_context[:3])  # Use top 3 results
    context_parts = [doc.get("content", "") for doc in normalized if doc.get("content")]
    context_str = "\n\n---\n\n".join(context_parts)
    
    # Get unique source filenames
    source_filenames = list(set(s.filename for s in sources if s.filename != "Unknown"))
    
    # Build prompt
    prompt = f"""You are Course Marshal, an AI tutor for COMP 237: Introduction to AI at Centennial College.

You must prioritize the retrieved course content over your pre-trained knowledge. Always cite sources.

Retrieved Course Content:
{context_str}

User Question: {query}

Instructions:
1. Answer based primarily on the retrieved course content above
2. If the answer isn't in the retrieved content, say so
3. Cite sources using format: [Source: filename]
4. Be pedagogical - explain concepts clearly
5. For coding questions, provide guidance but not complete solutions for graded work
6. Use examples from the course materials when possible

Response:"""
    
    try:
        response = model.invoke(prompt)
        # Handle Gemini 2.5+ list content format
        raw_content = response.content if hasattr(response, 'content') else str(response)
        if isinstance(raw_content, list):
            text_parts = []
            for block in raw_content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif isinstance(block, str):
                    text_parts.append(block)
            response_text = ''.join(text_parts)
        else:
            response_text = raw_content if isinstance(raw_content, str) else str(raw_content)
        
        # Add source citations using standardized format
        source_citation = format_sources_for_response(sources, max_sources=3)
        if source_citation:
            response_text += source_citation
        
        state["response"] = response_text
        
        # Build rich source payload for frontend using Source objects
        response_sources = [s.to_dict() for s in sources[:5] if s.filename != "Unknown"]
        
        # Fallback to simple format if no valid sources
        if not response_sources and source_filenames:
            response_sources = [{"title": src, "url": "", "description": ""} for src in source_filenames]
        
        state["response_sources"] = response_sources
        
        logger.info(f"Generated response using {model_name}, {len(response_sources)} sources attached")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        state["error"] = str(e)
        state["response"] = "I apologize, but I encountered an error generating a response. Please try again."
    
    return state

