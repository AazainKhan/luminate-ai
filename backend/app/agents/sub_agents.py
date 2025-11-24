"""
Sub-Agents for Course Marshal
Specialized agents for different tasks
"""

from typing import Dict, List
import logging
from app.agents.state import AgentState
from app.agents.supervisor import Supervisor
from app.rag.chromadb_client import get_chromadb_client

logger = logging.getLogger(__name__)


class SyllabusAgent:
    """Agent for syllabus and course logistics queries"""
    
    def __init__(self):
        self.chromadb = get_chromadb_client()
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
            # Query for syllabus-related content
            results = self.chromadb.query(
                query_texts=[query],
                n_results=5,
                where={"content_type": "syllabus"}
            )
            
            if results.get("ids") and results["ids"][0]:
                return {
                    "found": True,
                    "sources": results.get("metadatas", [[]])[0] if results.get("metadatas") else [],
                    "content": results.get("documents", [[]])[0] if results.get("documents") else [],
                }
            
            return {"found": False}
        except Exception as e:
            logger.error(f"Error checking syllabus: {e}")
            return {"found": False, "error": str(e)}


class RAGAgent:
    """Agent for RAG retrieval and context prioritization"""
    
    def __init__(self):
        self.chromadb = get_chromadb_client()
    
    def retrieve_context(self, query: str, course_id: str = "COMP237") -> List[Dict]:
        """
        Retrieve relevant context from ChromaDB
        
        Args:
            query: User query
            course_id: Course identifier
            
        Returns:
            List of retrieved documents with metadata
        """
        try:
            results = self.chromadb.query(
                query_texts=[query],
                n_results=5,
                where={"course_id": course_id}
            )
            
            retrieved = []
            if results.get("ids") and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    retrieved.append({
                        "id": doc_id,
                        "text": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                    })
            
            logger.info(f"Retrieved {len(retrieved)} documents for query")
            return retrieved
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []


def rag_node(state: AgentState) -> AgentState:
    """
    RAG retrieval node
    Retrieves relevant context from ChromaDB
    """
    rag_agent = RAGAgent()
    query = state.get("query", "")
    
    retrieved = rag_agent.retrieve_context(query)
    
    state["retrieved_context"] = retrieved
    state["context_sources"] = [
        doc["metadata"].get("source_filename", "Unknown")
        for doc in retrieved
    ]
    
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
    
    # Build context string
    context_parts = []
    sources = []
    for doc in retrieved_context[:3]:  # Use top 3 results
        context_parts.append(doc["text"])
        source = doc["metadata"].get("source_filename", "Unknown")
        if source not in sources:
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
        state["response_sources"] = sources
        
        logger.info(f"Generated response using {model_name}")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        state["error"] = str(e)
        state["response"] = "I apologize, but I encountered an error generating a response. Please try again."
    
    return state

