"""
Supervisor (Router) for Course Marshal
Routes queries to appropriate models and sub-agents
"""

from typing import Dict
import logging
from app.agents.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from app.config import settings

logger = logging.getLogger(__name__)


class Supervisor:
    """
    Router that selects appropriate model and strategy:
    - Fast Mode: Gemini 1.5 Flash (default)
    - Coder Mode: Claude 3.5 Sonnet (code generation)
    - Reasoning Mode: Gemini 1.5 Pro (math derivations)
    """

    def __init__(self):
        self.gemini_flash = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.7,
        )
        
        if settings.anthropic_api_key:
            self.claude_sonnet = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                anthropic_api_key=settings.anthropic_api_key,
                temperature=0.7,
            )
        else:
            self.claude_sonnet = None
        
        self.gemini_pro = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", # Using 2.0 flash as Pro fallback for now
            google_api_key=settings.google_api_key,
            temperature=0.7,
        )

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
        # "code" by itself is too generic (e.g. "course code"), so checking context or exact phrases is better
        # Removing single word "code" to prevent false positives like "course code"
        
        if any(keyword in query_lower for keyword in code_keywords) or ("code" in query_lower and "course code" not in query_lower):
            return {
                "intent": "coder",
                "model_selected": "claude-sonnet" if self.claude_sonnet else "gemini-flash",
            }
        
        # Check for math/reasoning intent
        math_keywords = [
            "calculate", "derivative", "integral", "formula", "equation",
            "proof", "derive", "mathematical", "backpropagation", "gradient"
        ]
        if any(keyword in query_lower for keyword in math_keywords):
            return {
                "intent": "reasoning",
                "model_selected": "gemini-flash", # Fallback to flash for reliability
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
        elif model_name == "claude-sonnet":
            return self.claude_sonnet or self.gemini_pro  # Fallback
        elif model_name == "gemini-pro":
            return self.gemini_pro
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

