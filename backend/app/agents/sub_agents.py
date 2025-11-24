"""
Sub-Agents for Course Marshal
Specialized agents for different tasks
"""

from typing import Dict, List
import logging
from app.agents.state import AgentState
from app.agents.supervisor import Supervisor
from app.rag.langchain_chroma import get_langchain_chroma_client

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
    
    def retrieve_context(self, query: str, course_id: str = "COMP237") -> List[Dict]:
        """
        Retrieve relevant context from ChromaDB using LangChain
        """
        try:
            records = self.vectorstore.retrieve_with_metadata(
                query=query,
                k=5,
                filter={"course_id": course_id}
            )
            logger.info(f"✅ Retrieved {len(records)} documents for query")
            return records
        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            return []
    
    def summarize_sources(self, records: List[Dict]) -> List[Dict]:
        """Summarize retrieval results into unique sources"""
        return self.vectorstore.summarize_sources(records)


def rag_node(state: AgentState) -> AgentState:
    """
    RAG retrieval node
    Retrieves relevant context from ChromaDB
    """
    rag_agent = RAGAgent()
    query = state.get("query", "")
    
    retrieved = rag_agent.retrieve_context(query)
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
    query = state.get("query", "")
    
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
    
    query = state.get("query", "")
    retrieved_context = state.get("retrieved_context", [])
    context_sources = state.get("context_sources", [])
    
    # Build context string
    context_parts = []
    sources = []
    for doc in retrieved_context[:3]:  # Use top 3 results
        context_parts.append(doc.get("content") or doc.get("text", ""))
        source = doc.get("source_filename") or doc.get("metadata", {}).get("source_filename", "Unknown")
        if source and source not in sources:
            sources.append(source)
    
    context_str = "\n\n---\n\n".join(context_parts)
    
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
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Add source citations
        if sources:
            response_text += f"\n\n[Sources: {', '.join(sources)}]"
        
        state["response"] = response_text
        
        # Build rich source payload for frontend
        response_sources = []
        for source in context_sources:
            filename = source.get("filename", "Unknown")
            description_parts = [
                f"Chunk {source.get('chunk_index', 0)}",
                f"Score {source.get('relevance_score', 0.0):.2f}",
            ]
            if source.get("content_type"):
                description_parts.append(source["content_type"])
            if source.get("preview"):
                description_parts.append(source["preview"][:140])
            
            response_sources.append({
                "title": filename,
                "url": source.get("public_url", ""),
                "description": " • ".join(description_parts)
            })
        
        state["response_sources"] = response_sources or [{"title": src, "url": "", "description": ""} for src in sources]
        
        logger.info(f"Generated response using {model_name}")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        state["error"] = str(e)
        state["response"] = "I apologize, but I encountered an error generating a response. Please try again."
    
    return state

