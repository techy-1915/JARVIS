"""Abstract brain interface for JARVIS AI."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BrainInterface(ABC):
    """Abstract base class for the AI brain module.

    This interface allows the underlying model to be swapped out
    (e.g., from Ollama/LLaMA to a custom transformer) without
    changing any other part of the system.
    """

    @abstractmethod
    async def think(self, prompt: str, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate a response given a prompt and optional conversation context.

        Args:
            prompt: The user prompt or instruction.
            context: Optional list of previous messages in conversation history.
                     Each message is a dict with 'role' and 'content' keys.

        Returns:
            The generated text response.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """Check whether the underlying model is available and reachable.

        Returns:
            True if the model is ready, False otherwise.
        """

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the currently loaded model.

        Returns:
            Dictionary with model name, version, and capabilities.
        """
