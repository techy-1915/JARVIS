"""Local LLM integration via Ollama for JARVIS."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from .brain_interface import BrainInterface

logger = logging.getLogger(__name__)


class LocalLLM(BrainInterface):
    """Integrates with a locally running Ollama LLM instance.

    Communicates with the Ollama HTTP API to generate responses.
    Falls back gracefully when Ollama is not available.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: float = 120.0,
    ) -> None:
        """Initialise the LocalLLM client.

        Args:
            base_url: Base URL of the running Ollama instance.
            model: Name of the Ollama model to use.
            timeout: HTTP request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def think(
        self,
        prompt: str,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Send a prompt to the local Ollama model and return its response.

        Args:
            prompt: The user prompt.
            context: Optional conversation history.

        Returns:
            Generated text from the model.
        """
        messages = list(context or [])
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.RequestError as exc:
            logger.error("Failed to reach Ollama: %s", exc)
            return "I'm sorry, the local AI model is currently unavailable."
        except (KeyError, ValueError) as exc:
            logger.error("Unexpected response from Ollama: %s", exc)
            return "I encountered an error processing the model response."

    async def is_available(self) -> bool:
        """Ping the Ollama health endpoint.

        Returns:
            True if Ollama responds successfully.
        """
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the active Ollama model.

        Returns:
            Dictionary with model name and base URL.
        """
        return {
            "name": self.model,
            "provider": "ollama",
            "base_url": self.base_url,
        }

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
