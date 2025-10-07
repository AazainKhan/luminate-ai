"""
Simplified FastAPI server for testing Educate Mode
No ChromaDB dependency - just tests LLM responses
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
from pathlib import Path

# Add langgraph_workflows to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "langgraph_workflows"))

from educate_graph import build_educate_graph, query_educate_mode

app = FastAPI(title="Luminate AI - Simplified Test Server")

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
    return {"status": "healthy", "mode": "educate-only"}

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
            conversation_history=history
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
    Navigate Mode - Temporarily returns educate mode response
    (ChromaDB navigate mode disabled for now)
    """
    try:
        query = request.get("query", "")
        
        # Since navigate mode requires ChromaDB which we disabled,
        # we'll redirect to educate mode for now
        print(f"🔀 Navigate mode requested, using Educate mode instead")
        print(f"📝 Query: {query}")
        
        # Use educate mode to answer the query
        result = query_educate_mode(
            query=query,
            conversation_history=[]
        )
        
        # Format as navigate response structure
        formatted = result.get("formatted_response", {})
        
        # Convert educate response to navigate format
        navigate_response = {
            "formatted_response": formatted.get("main_content", "No response generated"),
            "top_results": [],  # No ChromaDB results
            "related_topics": [
                {"title": topic.get("title", ""), "relevance": "high"}
                for topic in formatted.get("related_concepts", [])[:3]
            ],
            "query_metadata": {
                "intent": "search",
                "entities": [],
                "complexity": "medium"
            }
        }
        
        return navigate_response
        
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


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting Simplified Luminate AI Server")
    print("📚 Educate Mode (Primary) + Navigate Mode (Fallback)")
    print("🔗 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
