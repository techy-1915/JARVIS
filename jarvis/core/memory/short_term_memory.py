"""Short-term (in-process) memory – current conversation context."""

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """Manages the active conversation context for the current session.

    Stores a rolling window of messages so older entries are
    automatically evicted when the window is full.
    """

    def __init__(self, max_messages: int = 50) -> None:
        """Initialise with an optional message cap.

        Args:
            max_messages: Maximum number of messages to retain.
        """
        self._max_messages = max_messages
        self._messages: Deque[Dict[str, Any]] = deque(maxlen=max_messages)

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Append a message to short-term memory.

        Args:
            role: The speaker role (``"user"``, ``"assistant"``, ``"system"``).
            content: The message text.
            metadata: Optional extra data (e.g., timestamps, tool calls).
        """
        entry: Dict[str, Any] = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self._messages.append(entry)
        logger.debug("STM: added %s message (%d chars)", role, len(content))

    def get_context(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return recent messages as a list suitable for LLM context.

        Args:
            limit: Optional maximum number of messages to return.

        Returns:
            List of message dicts with ``role`` and ``content`` keys.
        """
        msgs = list(self._messages)
        if limit is not None:
            msgs = msgs[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    def clear(self) -> None:
        """Erase all short-term memory."""
        self._messages.clear()
        logger.info("Short-term memory cleared")

    def __len__(self) -> int:
        return len(self._messages)
