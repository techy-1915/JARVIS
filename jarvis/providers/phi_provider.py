"""Phi-3 local provider via Ollama – Priority 4."""

import logging
from typing import Any, Dict, Optional

from .base_provider import BaseProvider, ProviderError

logger = logging.getLogger(__name__)

_OLLAMA_DEFAULT_URL = "http://localhost:11434"


class PhiProvider(BaseProvider):
    """Local Phi-3 model via Ollama (priority 4 – general reasoning/chat)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("Phi3", config)
        self._ollama_url: str = self.config.get("ollama_url", _OLLAMA_DEFAULT_URL)
        self._model: str = self.config.get("ollama_model", "phi3")

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response using the local Phi-3 model via Ollama.

        Args:
            prompt: User input text.
            **kwargs: Optional overrides (temperature).

        Returns:
            Text response.

        Raises:
            ProviderError: If Ollama is unreachable or returns an error.
        """
        try:
            import aiohttp  # type: ignore[import]
        except ImportError as exc:
            raise ProviderError("aiohttp is required for PhiProvider") from exc

        temperature = kwargs.get("temperature", self.config.get("temperature", 0.7))
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._ollama_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as response:
                    if response.status != 200:
                        raise ProviderError(
                            f"Ollama Phi3 error {response.status}: {await response.text()}"
                        )
                    data = await response.json()
                    return data.get("message", {}).get("content", "")
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Phi3 (Ollama) connection error: {exc}") from exc

    def check_availability(self) -> bool:
        """Return ``True`` (availability checked at runtime via :meth:`generate`)."""
        return True

    def get_model_name(self) -> str:
        return self._model
