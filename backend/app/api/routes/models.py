"""
Models API routes for listing available LLM models

Simplified: Now only uses Gemini 2.5 Flash
"""
import logging
from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.api.middleware import require_student
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])

# Single model configuration - we only use Gemini 2.5 Flash
AVAILABLE_MODELS = [
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "google",
        "description": "Google's latest and fastest multimodal model",
        "speed": "very_fast",
        "quality": "excellent",
        "cost": "low",
        "available": True,
        "default": True,
        "local": False,
    }
]


@router.get("/")
async def list_models(
    user_info: dict = Depends(require_student),
) -> List[Dict[str, Any]]:
    """
    List all available LLM models for the frontend model selector.
    
    Returns models with availability status based on configured API keys.
    Each model includes:
    - id: Model identifier (e.g., "gemini-2.5-flash")
    - name: Display name (e.g., "Gemini 2.5 Flash")
    - provider: Provider name (google)
    - description: Brief description
    - speed: Performance tier (very_fast)
    - quality: Quality tier (excellent)
    - cost: Cost tier (low)
    - available: Whether the model is currently available
    - default: Whether this is the default model
    - local: Whether this is a local model
    """
    logger.info(f"Models list requested by user {user_info.get('email')}")
    
    # Check if Google API key is configured
    models = []
    for model in AVAILABLE_MODELS:
        model_copy = model.copy()
        model_copy["available"] = bool(settings.google_api_key)
        models.append(model_copy)
    
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
