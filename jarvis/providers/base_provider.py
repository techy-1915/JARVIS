"""Abstract base class for all AI providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Provider-specific exceptions
# ---------------------------------------------------------------------------


class ProviderError(Exception):
    """Generic provider error."""


class RateLimitError(ProviderError):
    """Raised when the provider returns a rate-limit response."""


class QuotaExceededError(ProviderError):
    """Raised when the daily/monthly quota for the provider is exhausted."""


class AllProvidersExhaustedError(Exception):
    """Raised when every provider in the fallback chain has failed."""


# ---------------------------------------------------------------------------
# Abstract base provider
# ---------------------------------------------------------------------------


class BaseProvider(ABC):
    """Abstract base class for all AI providers.

    Subclasses must implement :meth:`generate`, :meth:`check_availability`,
    and :meth:`get_model_name`.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialise the provider.

        Args:
            name: Human-readable provider name (e.g. ``"Gemini"``).
            config: Provider-specific configuration dictionary.
        """
        self.name = name
        self.config: Dict[str, Any] = config or {}
        self.available: bool = True

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response for *prompt*.

        Args:
            prompt: The user's input text.
            **kwargs: Provider-specific options (e.g. temperature, max_tokens).

        Returns:
            Generated text response.

        Raises:
            RateLimitError: If the provider is rate-limited.
            QuotaExceededError: If the quota is exhausted.
            ProviderError: For other provider-specific errors.
        """

    @abstractmethod
    def check_availability(self) -> bool:
        """Return ``True`` if the provider is currently reachable/available."""

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the underlying model identifier string."""

    def handle_error(self, error: Exception) -> None:
        """Handle a provider-specific error (override for custom logic).

        The default implementation marks the provider as unavailable.

        Args:
            error: The exception that was raised.
        """
        self.available = False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} available={self.available}>"
