"""Voice command API routes."""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ...core.perception.speech_recognition import SpeechRecognizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

_recognizer: Optional[SpeechRecognizer] = None


def _get_recognizer() -> SpeechRecognizer:
    global _recognizer
    if _recognizer is None:
        _recognizer = SpeechRecognizer()
    return _recognizer


class TranscriptionResponse(BaseModel):
    """Audio transcription result."""

    text: str
    available: bool


@router.post("/transcribe", response_model=TranscriptionResponse, summary="Transcribe audio")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe an uploaded audio file to text.

    The transcribed text can then be sent to the ``/chat`` endpoint.
    """
    recognizer = _get_recognizer()
    if not recognizer.is_available:
        return TranscriptionResponse(text="", available=False)

    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        result = recognizer.transcribe(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return TranscriptionResponse(text=result["text"], available=True)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Transcription error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
