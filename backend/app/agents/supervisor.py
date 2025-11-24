"""
Supervisor (Router) for Course Marshal
Routes queries to appropriate models and sub-agents
"""

from typing import Dict
import logging
from app.agents.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.config import settings
from app.observability import get_langfuse_handler

logger = logging.getLogger(__name__)


class Supervisor:
    """
    Router that selects appropriate model and strategy:
    - Fast Mode: Gemini 2.0 Flash (default)
    - Coder Mode: Groq (Llama 3.3 70B) or Gemini 2.0 Flash
    - Reasoning Mode: Gemini 2.0 Flash or Groq (Llama 3.3 70B)
    """

    def __init__(self):
        # Get Langfuse callback handler
        langfuse_handler = get_langfuse_handler()
        callbacks = [langfuse_handler] if langfuse_handler else []
        
        # Initialize Gemini (Primary/Fallback)
        self.gemini_flash = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.7,
            callbacks=callbacks,
        )
        
        # Initialize Groq (Performance/Coder)
        if settings.groq_api_key:
            self.groq_coder = ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=settings.groq_api_key,
                temperature=0.5, # Lower temperature for code
                callbacks=callbacks,
            )
            self.groq_fast = ChatGroq(
                model_name="llama-3.3-70b-versatile", # Upgrading fast to 70b as it is very fast on Groq
                groq_api_key=settings.groq_api_key,
                temperature=0.7,
                callbacks=callbacks,
            )
        else:
            logger.warning("GROQ_API_KEY not found. Falling back to Gemini for all tasks.")
            self.groq_coder = None
            self.groq_fast = None

    def route_intent(self, query: str) -> Dict[str, str]:
        """
        Determine intent and select appropriate model
        
        Args:
            query: User query
            
        Returns:
            Dictionary with intent and model_selected
        """
        query_lower = query.lower()
        
        # Check for coding intent
        code_keywords = [
            "python", "function", "script", "program", "implement",
            "write code", "debug", "syntax", "error", "algorithm"
        ]
        
        if any(keyword in query_lower for keyword in code_keywords) or ("code" in query_lower and "course code" not in query_lower):
            return {
                "intent": "coder",
                "model_selected": "groq-llama-70b" if self.groq_coder else "gemini-flash",
            }
        
        # Check for math/reasoning intent
        math_keywords = [
            "calculate", "derivative", "integral", "formula", "equation",
            "proof", "derive", "mathematical", "backpropagation", "gradient"
        ]
        if any(keyword in query_lower for keyword in math_keywords):
            # Gemini 2.0 Flash is strong at reasoning, or use Llama 70B
            return {
                "intent": "reasoning",
                "model_selected": "gemini-flash", 
            }
        
        # Check for syllabus/logistics intent
        syllabus_keywords = [
            "when", "due date", "deadline", "schedule", "syllabus",
            "overview", "chapter", "module", "week", "assignment"
        ]
        if any(keyword in query_lower for keyword in syllabus_keywords):
            return {
                "intent": "syllabus_query",
                "model_selected": "gemini-flash",
            }
        
        # Default to fast mode
        return {
            "intent": "fast",
            "model_selected": "gemini-flash",
        }

    def get_model(self, model_name: str):
        """Get model instance by name"""
        if model_name == "gemini-flash":
            return self.gemini_flash
        elif model_name == "groq-llama-70b":
            return self.groq_coder or self.gemini_flash
        elif model_name == "groq-llama-8b":
            return self.groq_fast or self.gemini_flash
        else:
            return self.gemini_flash  # Default fallback


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node for LangGraph
    Routes query to appropriate model
    """
    supervisor = Supervisor()
    routing = supervisor.route_intent(state.get("query", ""))
    
    state["intent"] = routing["intent"]
    state["model_selected"] = routing["model_selected"]
    
    logger.info(f"Routed to: {routing['intent']} using {routing['model_selected']}")
    
    return state
