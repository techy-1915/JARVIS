"""Response manager – coordinates all output channels."""

import logging
from typing import Any, Dict, Optional

from .text_formatter import TextFormatter
from .speech_synthesis import SpeechSynthesizer

logger = logging.getLogger(__name__)


class ResponseManager:
    """Manages delivery of responses across all output channels.

    Coordinates text formatting, TTS synthesis, and logging.
    """

    def __init__(
        self,
        formatter: Optional[TextFormatter] = None,
        synthesizer: Optional[SpeechSynthesizer] = None,
        speak_by_default: bool = False,
    ) -> None:
        self._formatter = formatter or TextFormatter()
        self._synthesizer = synthesizer or SpeechSynthesizer()
        self._speak = speak_by_default

    def respond(
        self,
        text: str,
        channel: str = "chat",
        speak: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Deliver a response through the appropriate channels.

        Args:
            text: The raw response text.
            channel: Output channel (``"chat"``, ``"voice"``, ``"api"``).
            speak: Override whether to speak the response aloud.
            metadata: Optional additional data to include.

        Returns:
            Dict with ``text``, ``channel``, and ``spoken`` keys.
        """
        formatted = self._formatter.format_response(text, channel, metadata)
        should_speak = speak if speak is not None else (self._speak or channel == "voice")
        spoken = False

        if should_speak:
            voice_text = self._formatter.format_response(text, "voice")
            spoken = self._synthesizer.speak(voice_text)

        logger.debug("Response delivered via %s (spoken=%s)", channel, spoken)
        return {
            "text": formatted,
            "channel": channel,
            "spoken": spoken,
            "metadata": metadata or {},
        }
