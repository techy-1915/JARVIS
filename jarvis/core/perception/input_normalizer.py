"""Input normalizer – provides a unified preprocessing pipeline."""

import logging
from typing import Any, Dict, Optional

from .text_input import TextInputProcessor
from .wake_word import WakeWordDetector

logger = logging.getLogger(__name__)


class InputNormalizer:
    """Unified pipeline for all input types (text and speech).

    Applies text normalisation, wake-word stripping, and intent tagging.
    """

    def __init__(
        self,
        wake_phrase: str = "hey jarvis",
    ) -> None:
        self._text_processor = TextInputProcessor()
        self._wake_detector = WakeWordDetector(wake_phrase=wake_phrase)

    def normalize(
        self,
        raw_input: str,
        source: str = "chat",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalise an input from any source.

        Args:
            raw_input: The raw user input string.
            source: Input source (``"chat"``, ``"voice"``, ``"api"``).
            session_id: Optional session identifier.

        Returns:
            Normalised input dict with keys:
            - ``text``: cleaned input text
            - ``source``: input source
            - ``session_id``: session identifier
            - ``wake_word_detected``: bool
            - ``clean_text``: text with wake phrase removed
        """
        processed = self._text_processor.process(raw_input, session_id)
        text = processed["text"]

        wake_detected = self._wake_detector.check_text(text)
        clean = text.lower().replace(self._wake_detector._wake_phrase, "").strip() if wake_detected else text

        return {
            "text": text,
            "clean_text": clean,
            "source": source,
            "session_id": processed["session_id"],
            "wake_word_detected": wake_detected,
        }
