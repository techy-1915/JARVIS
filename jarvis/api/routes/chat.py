"""Chat API routes with streaming support."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...ai.brain import AIBrain
from ...core.agents.commander_agent import CommanderAgent
from ...core.agents.message_bus import MessageBus
from ...core.perception.input_normalizer import InputNormalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Module-level singletons (initialised on first request)
_bus: Optional[MessageBus] = None
_commander: Optional[CommanderAgent] = None
_brain: Optional[AIBrain] = None
_normalizer = InputNormalizer()


def _get_commander() -> CommanderAgent:
    global _bus, _commander, _brain
    if _commander is None:
        _bus = MessageBus()
        _brain = AIBrain()
        _commander = CommanderAgent(message_bus=_bus, ai_brain=_brain)
    return _commander


class ChatRequest(BaseModel):
    """Incoming chat message."""

    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(default=None)
    stream: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Chat API response."""

    response: str
    session_id: str
    code_blocks: list = []
    type: str = "chat"


@router.post("/", summary="Send a chat message")
async def chat(body: ChatRequest):
    """Process a text chat message and return a response."""
    try:
        normalised = _normalizer.normalize(body.message, source="chat", session_id=body.session_id)
        commander = _get_commander()

        if body.stream:
            # Streaming response via Server-Sent Events
            async def generate():
                async for chunk in await _brain.generate(
                    prompt=normalised["clean_text"],
                    stream=True,
                ):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # Complete response
            result = await commander.run({"input": normalised["clean_text"]})

            if result["status"] == "error":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Unknown error"),
                )

            return ChatResponse(
                response=result["result"]["response"],
                session_id=normalised["session_id"],
                code_blocks=result["result"].get("code_blocks", []),
                type=result["result"].get("type", "chat"),
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health", summary="Check AI brain health")
async def health_check():
    """Check if Ollama is available."""
    # Reuse the existing _brain singleton if already initialised; otherwise create a temporary one.
    brain = _brain if _brain is not None else AIBrain()
    is_healthy = await brain.check_health()
    return {
        "ollama_available": is_healthy,
        "status": "ok" if is_healthy else "error",
    }

