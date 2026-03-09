"""Mistral local provider via Ollama – Priority 6."""

import logging
from typing import Any, Dict, Optional

from ..ai_router.system_prompts import get_system_prompt
from .base_provider import BaseProvider, ProviderError

logger = logging.getLogger(__name__)

_OLLAMA_DEFAULT_URL = "http://localhost:11434"


class MistralProvider(BaseProvider):
    """Local Mistral model via Ollama (priority 6 – general purpose)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("Mistral", config)
        self._ollama_url: str = self.config.get("ollama_url", _OLLAMA_DEFAULT_URL)
        self._model: str = self.config.get("ollama_model", "mistral")

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response using the local Mistral model via Ollama.

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
            raise ProviderError("aiohttp is required for MistralProvider") from exc

        temperature = kwargs.get("temperature", self.config.get("temperature", 0.5))
        task_type = kwargs.get("task_type", "reasoning")
        system_prompt = get_system_prompt(task_type)
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
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
                            f"Ollama Mistral error {response.status}: {await response.text()}"
                        )
                    data = await response.json()
                    return data.get("message", {}).get("content", "")
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Mistral (Ollama) connection error: {exc}") from exc

    def check_availability(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return self._model
