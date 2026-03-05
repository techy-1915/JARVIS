"""Base class for all JARVIS agents."""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class AgentBase(ABC):
    """Abstract base class that every JARVIS agent must inherit from.

    Provides a unique ID, structured logging, and a standard
    ``run`` interface.
    """

    def __init__(self, name: str, description: str = "") -> None:
        """Initialise the agent.

        Args:
            name: Human-readable agent name.
            description: Short description of the agent's purpose.
        """
        self.agent_id: str = str(uuid.uuid4())
        self.name: str = name
        self.description: str = description
        self.created_at: datetime = datetime.now(timezone.utc)
        self.logger: logging.Logger = logging.getLogger(
            f"jarvis.agents.{name.lower().replace(' ', '_')}"
        )

    @abstractmethod
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary task.

        Args:
            task: A dictionary describing the task to perform.
                  Must include at least a ``type`` key.

        Returns:
            A dictionary containing at minimum a ``status`` key
            (``"success"`` or ``"error"``) and a ``result`` key.
        """

    def _success(self, result: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build a standardised success response."""
        return {
            "status": "success",
            "agent": self.name,
            "agent_id": self.agent_id,
            "result": result,
            "metadata": metadata or {},
        }

    def _error(self, message: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
        """Build a standardised error response."""
        self.logger.error("%s: %s", message, exc)
        return {
            "status": "error",
            "agent": self.name,
            "agent_id": self.agent_id,
            "error": message,
        }
