"""Standardised base interface for all JARVIS tools and plugins."""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict


class ToolBase(ABC):
    """Abstract base class for all JARVIS tools.

    Every tool must implement ``execute`` and expose a ``schema``
    property describing its input parameters.
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialise the tool.

        Args:
            name: Unique tool name.
            description: Human-readable description of the tool's purpose.
        """
        self.tool_id: str = str(uuid.uuid4())
        self.name: str = name
        self.description: str = description
        self.logger: logging.Logger = logging.getLogger(
            f"jarvis.tools.{name.lower().replace(' ', '_')}"
        )

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute the tool with the given parameters.

        Returns:
            Dict with ``status`` (``"success"``/``"error"``) and ``result``.
        """

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """JSON-Schema-like description of the tool's input parameters."""

    def _success(self, result: Any) -> Dict[str, Any]:
        return {"status": "success", "tool": self.name, "result": result}

    def _error(self, message: str) -> Dict[str, Any]:
        self.logger.error("%s", message)
        return {"status": "error", "tool": self.name, "error": message}
