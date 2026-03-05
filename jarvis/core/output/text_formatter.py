"""Text formatter – formats AI responses for display."""

import logging
import textwrap
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TextFormatter:
    """Formats raw text responses for different output channels."""

    def __init__(self, max_line_width: int = 80) -> None:
        self._max_width = max_line_width

    def format_response(
        self,
        text: str,
        channel: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format a response text for the specified output channel.

        Args:
            text: The raw response text.
            channel: One of ``"chat"``, ``"voice"``, ``"api"``, ``"terminal"``.
            metadata: Optional additional context.

        Returns:
            Formatted string ready for delivery.
        """
        if channel == "voice":
            return self._for_voice(text)
        elif channel == "terminal":
            return self._for_terminal(text)
        elif channel == "api":
            return text.strip()
        return text.strip()

    def _for_voice(self, text: str) -> str:
        """Strip markdown and formatting unsuitable for speech."""
        import re
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`[^`]+`", "", text)
        text = re.sub(r"[#*_~]", "", text)
        return text.strip()

    def _for_terminal(self, text: str) -> str:
        """Wrap text to a fixed terminal width."""
        return textwrap.fill(text, width=self._max_width)

    def format_list(self, items: List[str], numbered: bool = False) -> str:
        """Format a list of items for display."""
        if numbered:
            return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
        return "\n".join(f"• {item}" for item in items)
