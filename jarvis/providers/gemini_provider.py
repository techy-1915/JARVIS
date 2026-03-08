"""Gemini API provider – Priority 1."""

import logging
import os
from typing import Any, Dict, Optional

from .base_provider import BaseProvider, ProviderError, QuotaExceededError, RateLimitError

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """Google Gemini API provider (cloud, priority 1).

    Requires ``GEMINI_API_KEY`` environment variable or ``api_key`` in *config*.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("Gemini", config)
        self._api_key: str = (
            self.config.get("api_key") or os.environ.get("GEMINI_API_KEY", "")
        )
        self._model: str = self.config.get("model", "gemini-1.5-pro")
        self._base_url: str = (
            "https://generativelanguage.googleapis.com/v1beta/models"
        )

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response using the Gemini REST API.

        Args:
            prompt: User input text.
            **kwargs: Optional overrides (temperature, max_output_tokens).

        Returns:
            Text response from Gemini.

        Raises:
            RateLimitError: On HTTP 429.
            QuotaExceededError: On HTTP 403.
            ProviderError: On other non-200 responses.
        """
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY is not set")

        try:
            import aiohttp  # type: ignore[import]
        except ImportError as exc:  # noqa: BLE001
            raise ProviderError("aiohttp is required for GeminiProvider") from exc

        url = f"{self._base_url}/{self._model}:generateContent?key={self._api_key}"
        temperature = kwargs.get("temperature", self.config.get("temperature", 0.7))
        max_tokens = kwargs.get("max_output_tokens", self.config.get("max_output_tokens", 2048))

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status == 429:
                    raise RateLimitError(f"Gemini rate limit: {await response.text()}")
                if response.status == 403:
                    raise QuotaExceededError(f"Gemini quota exceeded: {await response.text()}")
                if response.status != 200:
                    raise ProviderError(
                        f"Gemini error {response.status}: {await response.text()}"
                    )

                data = await response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError) as exc:
                    raise ProviderError(f"Unexpected Gemini response format: {data}") from exc

    def check_availability(self) -> bool:
        """Return ``True`` if an API key is configured."""
        return bool(self._api_key)

    def get_model_name(self) -> str:
        return self._model
