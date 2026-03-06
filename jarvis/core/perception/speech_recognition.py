"""Speech recognition – converts voice audio to text."""

import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """Converts speech audio to text using OpenAI Whisper (if available).

    Falls back gracefully to a stub when Whisper is not installed.
    """

    def __init__(self, model_size: str = "base") -> None:
        """Initialise the speech recogniser.

        Args:
            model_size: Whisper model size (``"tiny"``, ``"base"``, ``"small"``, etc.).
        """
        self._model_size = model_size
        self._model = None
        self._try_load()

    def _try_load(self) -> None:
        """Attempt to load the Whisper model."""
        try:
            import whisper  # type: ignore[import]
            self._model = whisper.load_model(self._model_size)
            logger.info("Whisper model '%s' loaded", self._model_size)
        except ImportError:
            logger.warning("openai-whisper not installed; speech recognition disabled")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load Whisper model: %s", exc)

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio file (WAV, MP3, etc.).

        Returns:
            Dict with ``text`` key containing the transcription.
        """
        if self._model is None:
            return {"text": "", "error": "Whisper model not available"}

        if not Path(audio_path).exists():
            return {"text": "", "error": f"Audio file not found: {audio_path}"}

        try:
            result = self._model.transcribe(audio_path)
            return {"text": result.get("text", "").strip()}
        except Exception as exc:  # noqa: BLE001
            logger.error("Transcription failed: %s", exc)
            return {"text": "", "error": str(exc)}

    @property
    def is_available(self) -> bool:
        """True if a Whisper model is loaded."""
        return self._model is not None
