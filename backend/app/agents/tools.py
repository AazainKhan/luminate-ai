"""
Tools for the Tutor Agent
Wraps sub-agents into LangChain tools

Enhanced Tool Design (2025 Refactor):
- Clear, action-oriented descriptions
- Explicit usage guidelines
- Strong input validation
"""

from typing import List, Dict, Optional
from langchain_core.tools import tool
from app.agents.sub_agents import RAGAgent, SyllabusAgent
from pydantic import BaseModel, Field

# Initialize agents once
rag_agent = RAGAgent()
syllabus_agent = SyllabusAgent()


class RetrieveContextInput(BaseModel):
    """Input schema for context retrieval tool"""
    query: str = Field(
        description="The AI/ML concept, topic, or question to search for in course materials. "
                    "Be specific - use exact concept names like 'backpropagation', 'gradient descent', "
                    "'decision trees', 'k-means clustering', etc."
    )
    course_id: str = Field(
        default="COMP237", 
        description="The course ID. Always use 'COMP237' for this tutoring system."
    )


@tool("retrieve_context", args_schema=RetrieveContextInput)
def retrieve_context(query: str, course_id: str = "COMP237") -> List[Dict]:
    """Search and retrieve relevant content from COMP 237 course materials.
    
    WHEN TO USE THIS TOOL:
    - Before answering ANY question about AI/ML concepts (neural networks, classification, etc.)
    - When you need to cite course-specific information
    - To verify your answer matches what was taught in class
    - When the student asks "what does the course say about X"
    
    WHEN NOT TO USE:
    - For simple greetings or off-topic conversation
    - When the student just wants a quick definition (use your knowledge instead)
    
    RETURNS: List of relevant document chunks with source information.
    Each chunk has: page_content, source_file, page number, relevance_score
    
    EXAMPLE QUERIES:
    - "backpropagation algorithm"
    - "difference between classification and regression"
    - "how neural networks learn"
    - "loss functions in machine learning"
    """
    # Normalize course_id (remove spaces)
    course_id = course_id.replace(" ", "").upper()
    return rag_agent.retrieve_context(query, course_id)


class CheckSyllabusInput(BaseModel):
    """Input schema for syllabus checking tool"""
    query: str = Field(
        description="The logistics question to check against the syllabus. "
                    "Examples: 'exam dates', 'assignment deadlines', 'grading policy', "
                    "'office hours', 'late submission policy'"
    )


@tool("check_syllabus", args_schema=CheckSyllabusInput)
def check_syllabus(query: str) -> Dict:
    """Check the COMP 237 course syllabus for administrative and logistics information.
    
    WHEN TO USE THIS TOOL:
    - Questions about due dates, deadlines, exam schedules
    - Questions about grading policies or weights
    - Questions about course rules (late policy, academic integrity)
    - Questions about instructor info or office hours
    - Questions about required textbooks or materials
    
    WHEN NOT TO USE:
    - Questions about AI/ML concepts (use retrieve_context instead)
    - Questions about how to do homework problems
    - General learning questions
    
    RETURNS: Dictionary with relevant syllabus sections and dates.
    
    EXAMPLE QUERIES:
    - "when is the midterm"
    - "what is the late policy"
    - "how is the grade calculated"
    - "instructor contact information"
    """
    return syllabus_agent.check_syllabus(query)


# List of available tools with clear documentation
tutor_tools = [retrieve_context, check_syllabus]
