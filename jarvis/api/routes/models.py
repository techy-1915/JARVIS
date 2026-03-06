"""Models API – list available Ollama models and their capabilities."""

import logging

from fastapi import APIRouter

from ...ai.models import DEFAULT_MODEL, MODELS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/", summary="List available models")
async def list_models():
    """Return all configured AI models with their metadata."""
    models_list = []
    for key, cfg in MODELS.items():
        models_list.append(
            {
                "id": key,
                "name": cfg.name,
                "display_name": cfg.display_name,
                "context_window": cfg.context_window,
                "capabilities": cfg.capabilities,
                "temperature": cfg.temperature,
                "default": key == DEFAULT_MODEL,
            }
        )
    return {"models": models_list, "default": DEFAULT_MODEL}
