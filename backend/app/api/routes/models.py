"""
Models API routes for listing available LLM models
"""
import logging
from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.api.middleware import require_student
from app.agents.supervisor import get_available_models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/")
async def list_models(
    user_info: dict = Depends(require_student),
) -> List[Dict[str, Any]]:
    """
    List all available LLM models for the frontend model selector.
    
    Returns models with availability status based on configured API keys.
    Each model includes:
    - id: Model identifier (e.g., "gemini-2.0-flash")
    - name: Display name (e.g., "Gemini 2.0 Flash")
    - provider: Provider name (google, github, groq, ollama)
    - description: Brief description
    - speed: Performance tier (very_fast, fast, medium, slow)
    - quality: Quality tier (medium, high, very_high, excellent)
    - cost: Cost tier (free, low, medium, high)
    - available: Whether the model is currently available
    - default: Whether this is the default model
    - local: Whether this is a local model (Ollama)
    """
    logger.info(f"Models list requested by user {user_info.get('email')}")
    
    models = get_available_models()
    
    # Sort: available first, then by default, then by quality
    quality_order = {"excellent": 0, "very_high": 1, "high": 2, "medium": 3}
    models.sort(key=lambda m: (
        not m["available"],  # Available first
        not m.get("default", False),  # Default first
        quality_order.get(m["quality"], 4),  # Then by quality
    ))
    
    logger.debug(f"Returning {len(models)} models, {sum(1 for m in models if m['available'])} available")
    
    return models


@router.get("/default")
async def get_default_model(
    user_info: dict = Depends(require_student),
) -> Dict[str, Any]:
    """
    Get the default model for new chats.
    """
    models = get_available_models()
    
    # Find default model that's available
    for model in models:
        if model.get("default") and model.get("available"):
            return model
    
    # Fallback to first available model
    for model in models:
        if model.get("available"):
            return model
    
    # Last resort
    return {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "google",
        "available": True,
        "default": True,
    }
