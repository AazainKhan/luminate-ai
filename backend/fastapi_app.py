"""
fastapi_app.py
Enhanced FastAPI with LLM integration for intelligent tutoring responses
(using local LLaMA model via Ollama + ChromaDB semantic search)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import chromadb.errors
from typing import List, Dict
import subprocess
import json

app = FastAPI()

# -------------------------------
# CORS Middleware
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Initialize ChromaDB
# -------------------------------
client = chromadb.PersistentClient(path="chroma_index")
try:
    collection = client.get_collection("comp237_chunks")
except chromadb.errors.NotFoundError:
    collection = client.create_collection("comp237_chunks")

# -------------------------------
# Pydantic model for queries
# -------------------------------
class Query(BaseModel):
    question: str
    mode: str = "educate"  # "navigate" or "educate"

# -------------------------------
# LLaMA-based AI tutor function
# -------------------------------
def generate_tutor_response(question: str, retrieved_docs: List[Dict], mode: str) -> Dict:
    """
    Generate intelligent tutor response using LLaMA model (via Ollama) and ChromaDB content.
    """

    # Step 1: Build context from retrieved docs
    context = "\n\n".join([doc["text"][:500] for doc in retrieved_docs[:5]])  # top 5 chunks

    # Step 2: Create prompt for LLaMA
    if mode == "navigate":
        prompt = (
            f"You are a navigation assistant for COMP-237.\n"
            f"Student Question: {question}\n"
            f"Course Content:\n{context}\n\n"
            "Provide a short and clear navigation answer (1-2 sentences) pointing to relevant modules or sections."
        )
    else:  # educate mode
        prompt = (
            f"You are an AI tutor for COMP-237.\n"
            f"Student Question: {question}\n"
            f"Course Content:\n{context}\n\n"
            "Provide a concise tutoring answer (3-4 sentences max) that:\n"
            "1. Explains the concept clearly\n"
            "2. Includes a follow-up question\n"
            "3. Suggests next steps for learning"
        )

    # Step 3: Call Ollama CLI to generate response
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt.encode("utf-8"),
            capture_output=True,
            check=True,
            timeout=30  # prevent long hangs
        )
        # Ollama outputs plain text
        ai_response = result.stdout.decode("utf-8").strip()
        if not ai_response:
            ai_response = result.stderr.decode("utf-8").strip() or "No response generated."
    except subprocess.TimeoutExpired:
        ai_response = "The LLaMA model took too long to respond. Please try again."
    except Exception as e:
        ai_response = f"I encountered an error generating a response: {str(e)}"

    # Step 4: Return structured response with sources
    return {
        "response": ai_response,
        "mode": mode,
        "sources": [
            {"title": doc["meta"].get("source_file", "Course Material"), "relevance": f"Relevance: {i+1}/{len(retrieved_docs)}"}
            for i, doc in enumerate(retrieved_docs[:5])
        ]
    }

# -------------------------------
# API Endpoints
# -------------------------------
@app.get("/")
def root():
    return {"message": "Luminate AI Backend is running with local LLaMA model!"}

@app.get("/debug/collection_info")
def collection_info():
    count = collection.count()
    if count > 0:
        sample = collection.peek(limit=3)
        return {
            "count": count,
            "sample_documents": sample.get("documents", [])[:2],
            "sample_ids": sample.get("ids", [])
        }
    else:
        return {"count": count, "message": "Collection is empty"}

@app.post("/ask")
def ask(q: Query):
    """Ask endpoint with local LLaMA AI tutor response"""

    # Step 1: Retrieve relevant documents from ChromaDB
    results = collection.query(
        query_texts=[q.question],
        n_results=5  # top 5 chunks
    )

    docs = []
    for i, doc_id in enumerate(results["ids"][0]):
        docs.append({
            "id": doc_id,
            "text": results["documents"][0][i],
            "meta": results["metadatas"][0][i],
            "relevance_score": results["distances"][0][i] if "distances" in results else 0.5
        })

    # Step 2: Generate AI tutor response
    response_data = generate_tutor_response(q.question, docs, q.mode)

    # Step 3: Return structured response
    return {
        "tutor_response": response_data["response"],
        "mode": response_data["mode"],
        "sources": response_data["sources"],
        "retrieved_count": len(docs)
    }

@app.post("/study_plan")
def create_study_plan(request: Dict):
    """Generate personalized study plan based on student needs"""
    topic = request.get("topic", "")
    duration = request.get("duration", 60)  # minutes

    results = collection.query(query_texts=[f"study plan {topic} exercises practice"], n_results=5)

    plan = {
        "topic": topic,
        "total_duration": duration,
        "sections": [
            {"activity": "Review key concepts", "duration": duration * 0.3, "type": "reading"},
            {"activity": "Practice exercises", "duration": duration * 0.4, "type": "practice"},
            {"activity": "Self-assessment", "duration": duration * 0.3, "type": "assessment"}
        ],
        "resources": [doc["meta"].get("source_file", "Course Material") for doc in results["documents"][0][:3]]
    }

    return {"study_plan": plan, "status": "generated"}

# -------------------------------
# Run server
# -------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
