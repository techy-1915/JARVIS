"""OpenRouter API provider – Priority 3."""

import logging
import os
from typing import Any, Dict, Optional

from .base_provider import BaseProvider, ProviderError, QuotaExceededError, RateLimitError

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseProvider):
    """OpenRouter cloud fallback provider (priority 3).

    Requires ``OPENROUTER_API_KEY`` environment variable or ``api_key`` in *config*.
    OpenRouter exposes an OpenAI-compatible API that forwards requests to many
    underlying models.
    """

    _BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("OpenRouter", config)
        self._api_key: str = (
            self.config.get("api_key") or os.environ.get("OPENROUTER_API_KEY", "")
        )
        self._model: str = self.config.get("model", "anthropic/claude-3-haiku")

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response using the OpenRouter API.

        Args:
            prompt: User input text.
            **kwargs: Optional overrides (temperature, max_tokens).

        Returns:
            Text response.

        Raises:
            RateLimitError: On HTTP 429.
            QuotaExceededError: On HTTP 402.
            ProviderError: On other errors.
        """
        if not self._api_key:
            raise ProviderError("OPENROUTER_API_KEY is not set")

        try:
            import aiohttp  # type: ignore[import]
        except ImportError as exc:
            raise ProviderError("aiohttp is required for OpenRouterProvider") from exc

        temperature = kwargs.get("temperature", self.config.get("temperature", 0.7))
        max_tokens = kwargs.get("max_tokens", self.config.get("max_tokens", 2048))

        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/techy-1915/JARVIS",
            "X-Title": "JARVIS AI Assistant",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._BASE_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=90),
            ) as response:
                if response.status == 429:
                    raise RateLimitError(f"OpenRouter rate limit: {await response.text()}")
                if response.status == 402:
                    raise QuotaExceededError(
                        f"OpenRouter quota exceeded: {await response.text()}"
                    )
                if response.status != 200:
                    raise ProviderError(
                        f"OpenRouter error {response.status}: {await response.text()}"
                    )
                data = await response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError) as exc:
                    raise ProviderError(
                        f"Unexpected OpenRouter response format: {data}"
                    ) from exc

    def check_availability(self) -> bool:
        return bool(self._api_key)

    def get_model_name(self) -> str:
        return self._model
