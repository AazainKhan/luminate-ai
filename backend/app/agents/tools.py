"""
Tools for the Tutor Agent
Wraps sub-agents into LangChain tools
"""

from typing import List, Dict, Optional
from langchain_core.tools import tool
from app.agents.sub_agents import RAGAgent, SyllabusAgent
from pydantic import BaseModel, Field

# Initialize agents once
rag_agent = RAGAgent()
syllabus_agent = SyllabusAgent()

class RetrieveContextInput(BaseModel):
    query: str = Field(description="The search query to retrieve context for")
    course_id: str = Field(default="COMP237", description="The course ID to search in")

@tool("retrieve_context", args_schema=RetrieveContextInput)
def retrieve_context(query: str, course_id: str = "COMP237") -> List[Dict]:
    """
    Retrieve relevant course materials and context from the vector database.
    Use this tool when you need to find information about course concepts, definitions, or content.
    """
    return rag_agent.retrieve_context(query, course_id)

class CheckSyllabusInput(BaseModel):
    query: str = Field(description="The query to check against the syllabus")

@tool("check_syllabus", args_schema=CheckSyllabusInput)
def check_syllabus(query: str) -> Dict:
    """
    Check the course syllabus for logistics, due dates, policies, and schedule.
    Use this tool when the user asks about deadlines, exam dates, or course rules.
    """
    return syllabus_agent.check_syllabus(query)

# List of available tools
tutor_tools = [retrieve_context, check_syllabus]
