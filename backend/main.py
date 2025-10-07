from fastapi import FastAPI
from pydantic import BaseModel

# Create the FastAPI app instance
app = FastAPI(title="Luminate AI Backend")

# Define a data model for incoming chat requests
class ChatRequest(BaseModel):
    query: str
    user_id: str = "default_user" # We'll use this later for personalization

@app.get("/")
def read_root():
    """A simple endpoint to check if the server is running."""
    return {"status": "Luminate AI server is alive!"}

@app.post("/chat")
def handle_chat(request: ChatRequest):
    """A placeholder endpoint for the main chat logic."""
    # For now, this just confirms it received the query.
    # Later, this is where we will call our delegator agent.
    return {
        "response": f"You asked: '{request.query}'. The delegator isn't connected yet."
    }