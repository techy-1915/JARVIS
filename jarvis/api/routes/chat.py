"""Chat API routes with streaming support."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...ai_router.router import get_ai_router
from ...core.perception.input_normalizer import InputNormalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Module-level singletons (initialised on first request)
_router = None  # AIRouter singleton
_normalizer = InputNormalizer()


def _get_router():
    """Get or initialise the AIRouter singleton."""
    global _router
    if _router is None:
        _router = get_ai_router()
    return _router


class ChatRequest(BaseModel):
    """Incoming chat message."""

    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(default=None)
    stream: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Chat API response."""

    response: str
    session_id: str
    provider: str = "unknown"
    code_blocks: list = []
    type: str = "chat"


@router.post("/", summary="Send a chat message")
async def chat(body: ChatRequest):
    """Process a text chat message and return a response."""
    try:
        normalised = _normalizer.normalize(body.message, source="chat", session_id=body.session_id)
        router_instance = _get_router()

        if body.stream:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Streaming is not currently supported with the AI router",
            )

        response_text, provider_name = await router_instance.route(normalised["clean_text"])
        logger.info("Response received from provider: %s", provider_name)

        return ChatResponse(
            response=response_text,
            session_id=normalised["session_id"],
            provider=provider_name,
            code_blocks=[],
            type="chat",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health", summary="Check AI router health")
async def health_check():
    """Check if AI providers are available."""
    try:
        router_instance = _get_router()
        available_providers = router_instance.get_provider_status()
        return {
            "providers": available_providers,
            "status": "ok" if available_providers else "error",
        }
    except Exception as exc:
        logger.error("Health check error: %s", exc)
        return {
            "providers": {},
            "status": "error",
            "message": str(exc),
        }

