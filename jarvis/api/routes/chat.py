"""Chat API routes – text-based interaction."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...core.agents.commander_agent import CommanderAgent
from ...core.agents.message_bus import MessageBus
from ...core.brain.model_manager import ModelManager
from ...core.memory.memory_store import MemoryStore
from ...core.output.response_manager import ResponseManager
from ...core.perception.input_normalizer import InputNormalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Module-level singletons (initialised on first request)
_model_manager: Optional[ModelManager] = None
_memory: Optional[MemoryStore] = None
_bus: Optional[MessageBus] = None
_commander: Optional[CommanderAgent] = None
_response_manager = ResponseManager()
_normalizer = InputNormalizer()


def _get_commander() -> CommanderAgent:
    global _model_manager, _memory, _bus, _commander
    if _commander is None:
        _model_manager = ModelManager()
        _memory = MemoryStore()
        _bus = MessageBus()
        _commander = CommanderAgent(brain=_model_manager.brain, message_bus=_bus)
    return _commander


class ChatRequest(BaseModel):
    """Incoming chat message."""

    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(default=None)
    speak: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Chat API response."""

    response: str
    session_id: str
    spoken: bool = False


@router.post("/", response_model=ChatResponse, summary="Send a chat message")
async def chat(body: ChatRequest):
    """Process a text chat message and return a response."""
    try:
        normalised = _normalizer.normalize(body.message, source="chat", session_id=body.session_id)
        commander = _get_commander()
        result = await commander.run({"input": normalised["clean_text"]})

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error"),
            )

        response_text = result["result"]["response"]
        output = _response_manager.respond(response_text, channel="api", speak=body.speak)

        return ChatResponse(
            response=output["text"],
            session_id=normalised["session_id"],
            spoken=output["spoken"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
