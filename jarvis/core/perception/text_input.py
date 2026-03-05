"""Text input processor – handles and normalises chat messages."""

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 10_000


class TextInputProcessor:
    """Processes raw text input from chat interfaces."""

    def process(self, raw_input: str, session_id: Optional[str] = None) -> Dict[str, str]:
        """Validate and normalise a text input.

        Args:
            raw_input: The raw text from the user.
            session_id: Optional identifier for the current session.

        Returns:
            Dict with ``text`` (normalised) and ``session_id`` keys.

        Raises:
            ValueError: If the input is empty or too long.
        """
        if not raw_input or not raw_input.strip():
            raise ValueError("Input cannot be empty")

        if len(raw_input) > MAX_INPUT_LENGTH:
            raise ValueError(f"Input too long ({len(raw_input)} chars; max {MAX_INPUT_LENGTH})")

        normalised = self._normalise(raw_input)
        return {"text": normalised, "session_id": session_id or "default"}

    @staticmethod
    def _normalise(text: str) -> str:
        """Strip excess whitespace and invisible characters."""
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        # Remove null bytes and other control characters (except newlines/tabs)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return text
