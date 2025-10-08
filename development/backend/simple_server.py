"""
FastAPI server for Educate Mode with ChromaDB integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
from pathlib import Path
import chromadb

# Add langgraph_workflows to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "langgraph_workflows"))

from educate_graph import build_educate_graph, query_educate_mode
from navigate_graph import query_navigate_mode

# Initialize ChromaDB
chroma_path = backend_dir.parent.parent / "chromadb_data"
print(f"📦 Initializing ChromaDB from: {chroma_path}")
chroma_client = chromadb.PersistentClient(path=str(chroma_path))
chroma_collection = chroma_client.get_collection("course_materials")
print(f"✅ ChromaDB loaded with {chroma_collection.count()} documents")

app = FastAPI(title="Luminate AI - Educate Mode with ChromaDB")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ConversationMessage(BaseModel):
    role: str
    content: str

class LangGraphEducateRequest(BaseModel):
    query: str
    conversation_history: Optional[List[ConversationMessage]] = []

class QuizAnswerRequest(BaseModel):
    question: str
    question_type: str  # multiple_choice, short_answer, true_false
    correct_answer: str
    student_answer: str
    course_context: Optional[str] = ""

class BatchQuizRequest(BaseModel):
    questions: List[Dict]  # List of {question, type, correct_answer}
    student_answers: List[str]
    course_context: Optional[str] = ""

class LangGraphEducateResponse(BaseModel):
    main_content: str
    response_type: str  # This is what the formatted_response actually has
    hints: Optional[Dict] = None
    socratic_questions: Optional[List[Dict]] = None
    misconception_alert: Optional[str] = None
    sources: List[Dict] = []
    related_concepts: List[Dict] = []
    follow_up_suggestions: List[str] = []

# Educate workflow builds itself inside query_educate_mode
print("✅ Educate Mode ready!")

@app.get("/")
async def root():
    return {
        "message": "Luminate AI - Simplified Test Server",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "educate": "/langgraph/educate"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mode": "educate + navigate (full agents)",
        "available_modes": ["educate", "navigate"],
        "chromadb_documents": chroma_collection.count()
    }

@app.post("/langgraph/educate")
async def educate_endpoint(request: LangGraphEducateRequest):
    """
    Test Educate Mode AI tutoring
    """
    try:
        print(f"\n📚 Educate Query: {request.query}")
        
        # Convert conversation history
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
        
        # Query educate mode (workflow builds itself internally)
        result = query_educate_mode(
            query=request.query,
            conversation_history=history,
            chroma_db=chroma_collection  # Pass ChromaDB for retrieval
        )
        
        # Extract the formatted response
        formatted = result.get("formatted_response", {})
        metadata = result.get("metadata", {})
        
        # Add metadata back into the response for the frontend
        formatted["metadata"] = {
            "intent": metadata.get("intent", "unknown"),
            "complexity_level": "medium",  # Could be determined by agents
            "execution_time_ms": 0,  # Could be tracked
            "timestamp": ""  # Could add current time
        }
        
        print(f"✅ Intent: {metadata.get('intent', 'unknown')}")
        print(f"📝 Response length: {len(formatted.get('main_content', ''))} chars")
        
        return formatted  # Return raw dict instead of validating with Pydantic
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return fallback response
        return {
            "main_content": f"I encountered an error: {str(e)}. Please check the server logs.",
            "response_type": "error",
            "sources": [],
            "related_concepts": [],
            "follow_up_suggestions": [],
            "metadata": {
                "intent": "error",
                "complexity_level": "unknown",
                "execution_time_ms": 0,
                "timestamp": ""
            }
        }


@app.post("/langgraph/navigate")
async def navigate_mode(request: dict):
    """
    Navigate Mode - Find course materials and resources
    """
    try:
        query = request.get("query", "")
        print(f"\n🧭 Navigate Query: {query}")
        
        # Query navigate mode with ChromaDB
        result = query_navigate_mode(
            query=query,
            chroma_db=chroma_collection
        )
        
        # Extract formatted response
        formatted = result.get("formatted_response", {})
        metadata = result.get("metadata", {})
        
        # Return navigate response with external resources
        # Note: formatting agent returns "answer" not "main_content"
        return {
            "formatted_response": formatted.get("answer", "No results found"),
            "top_results": formatted.get("top_results", []),
            "related_topics": formatted.get("related_topics", []),
            "external_resources": formatted.get("external_resources", []),  # Include external resources!
            "query_metadata": {
                "intent": "search",
                "entities": metadata.get("parsed_query", {}).get("key_concepts", []),
                "complexity": "medium",
                "total_results": metadata.get("total_results", 0)
            }
        }
        
    except Exception as e:
        print(f"❌ Navigate error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "formatted_response": f"Navigate mode is temporarily disabled. Please use Educate mode for your queries.",
            "top_results": [],
            "related_topics": [],
            "query_metadata": {"intent": "error"}
        }


@app.post("/external-resources")
async def external_resources_endpoint(request: dict):
    """
    Lazy load external resources (YouTube videos, OER commons, etc.)
    Separate endpoint for on-demand resource loading
    """
    try:
        query = request.get("query", "")
        print(f"\n🎥 External Resources Query: {query}")
        
        # Import the search functions directly
        from agents.external_resources import search_youtube, search_educational_resources, search_oer_commons
        
        # Search all external resources
        resources = []
        resources.extend(search_youtube(query, max_results=3))
        resources.extend(search_educational_resources(query, max_results=3))
        resources.extend(search_oer_commons(query, max_results=1))
        
        print(f"✅ Found {len(resources)} external resources")
        
        return {
            "resources": resources,
            "count": len(resources)
        }
        
    except Exception as e:
        print(f"❌ External resources error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "resources": [],
            "count": 0
        }


@app.post("/quiz/feedback")
async def quiz_feedback_endpoint(request: QuizAnswerRequest):
    """
    Evaluate a single quiz answer and provide feedback.
    """
    try:
        print(f"\n📝 Quiz Feedback Request:")
        print(f"   Question: {request.question[:50]}...")
        print(f"   Student answer: {request.student_answer[:50]}...")
        
        # Import quiz feedback agent
        from agents.quiz_feedback import quiz_feedback_agent
        
        # Get feedback
        feedback = quiz_feedback_agent(
            question=request.question,
            question_type=request.question_type,
            correct_answer=request.correct_answer,
            student_answer=request.student_answer,
            course_context=request.course_context
        )
        
        print(f"✅ Feedback generated: {feedback['correctness_level']}")
        
        return feedback
        
    except Exception as e:
        print(f"❌ Quiz feedback error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "is_correct": False,
            "correctness_level": "ERROR",
            "score": 0.0,
            "feedback": f"Error evaluating answer: {str(e)}",
            "hints": [],
            "what_to_review": [],
            "encouragement": "Please try again.",
            "next_step": "Contact support if the issue persists."
        }


@app.post("/quiz/batch-feedback")
async def batch_quiz_feedback_endpoint(request: BatchQuizRequest):
    """
    Evaluate multiple quiz answers at once and provide overall results.
    """
    try:
        print(f"\n📊 Batch Quiz Feedback Request:")
        print(f"   Questions: {len(request.questions)}")
        print(f"   Answers: {len(request.student_answers)}")
        
        # Import quiz feedback agent
        from agents.quiz_feedback import batch_quiz_feedback
        
        # Get feedback for all questions
        results = batch_quiz_feedback(
            questions=request.questions,
            student_answers=request.student_answers,
            course_context=request.course_context
        )
        
        print(f"✅ Batch feedback complete: {results['correct_count']}/{results['total_questions']} correct")
        
        return results
        
    except Exception as e:
        print(f"❌ Batch quiz feedback error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "error": str(e),
            "total_questions": len(request.questions) if request.questions else 0,
            "correct_count": 0,
            "total_score": 0.0,
            "percentage": 0.0,
            "grade": "F",
            "overall_feedback": "Error processing quiz results.",
            "question_results": [],
            "areas_to_review": []
        }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting Simplified Luminate AI Server")
    print("📚 Educate Mode (Primary) + Navigate Mode (Fallback)")
    print("🔗 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
