"""Main AI router – priority-based provider selection with automatic fallback."""

import time
from typing import Any, Callable, Dict, List, Optional

from ..ai_router.logger import get_router_logger
from ..ai_router.provider_manager import ProviderManager
from ..ai_router.task_classifier import TaskClassifier, TaskType, get_task_classifier
from ..ai_router.usage_tracker import UsageTracker, get_usage_tracker
from ..providers.base_provider import (
    AllProvidersExhaustedError,
    BaseProvider,
    ProviderError,
    QuotaExceededError,
    RateLimitError,
)
from ..providers.deepseek_provider import DeepSeekProvider
from ..providers.gemini_provider import GeminiProvider
from ..providers.groq_provider import GroqProvider
from ..providers.mistral_provider import MistralProvider
from ..providers.openrouter_provider import OpenRouterProvider
from ..providers.phi_provider import PhiProvider

logger = get_router_logger()


def _build_default_providers(config: Dict[str, Any]) -> List[BaseProvider]:
    """Build the default priority-ordered provider list from *config*."""
    provider_cfg = config.get("providers", {})
    return [
        GeminiProvider(provider_cfg.get("gemini", {})),
        GroqProvider(provider_cfg.get("groq", {})),
        OpenRouterProvider(provider_cfg.get("openrouter", {})),
        PhiProvider(provider_cfg.get("phi3", {})),
        DeepSeekProvider(provider_cfg.get("deepseek", {})),
        MistralProvider(provider_cfg.get("mistral", {})),
    ]


class AIRouter:
    """Route AI requests to the best available provider with automatic fallback.

    Usage::

        router = AIRouter()
        response, provider_name = await router.route("Write a Python sort function")

    The router will:
    1. Classify the prompt to determine the task type.
    2. Ask the :class:`ProviderManager` for prioritised available providers.
    3. Try each provider in order, catching rate-limit / quota errors.
    4. Track usage via :class:`UsageTracker`.
    5. Raise :class:`AllProvidersExhaustedError` only when every provider fails.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        providers: Optional[List[BaseProvider]] = None,
        classifier: Optional[TaskClassifier] = None,
        usage_tracker: Optional[UsageTracker] = None,
        notify_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialise the router.

        Args:
            config: Optional provider configuration dict (from provider_config.yaml).
            providers: Override the default provider list.
            classifier: Override the task classifier.
            usage_tracker: Override the usage tracker.
            notify_callback: Optional callable ``(message: str) → None`` used to
                             surface provider-switch warnings to the user/UI.
        """
        self._config: Dict[str, Any] = config or {}
        self._classifier: TaskClassifier = classifier or get_task_classifier()
        self._tracker: UsageTracker = usage_tracker or get_usage_tracker(
            limits=self._build_limits()
        )
        _providers = providers or _build_default_providers(self._config)
        self._manager = ProviderManager(
            providers=_providers, usage_tracker=self._tracker
        )
        self._notify: Callable[[str], None] = notify_callback or (lambda msg: None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def route(
        self, prompt: str, task_type: Optional[TaskType] = None, **kwargs: Any
    ) -> tuple[str, str]:
        """Route *prompt* to the best available provider.

        Args:
            prompt: User input text.
            task_type: Override automatic task classification.
            **kwargs: Forwarded to the provider's ``generate`` method.

        Returns:
            ``(response_text, provider_name)`` tuple.

        Raises:
            AllProvidersExhaustedError: If every provider in the chain fails.
        """
        if task_type is None:
            task_type = self._classifier.classify(prompt)

        logger.info("Routing prompt | task_type=%s | len=%d", task_type.value, len(prompt))

        candidate_providers = self._manager.get_available_providers(task_type)
        if not candidate_providers:
            raise AllProvidersExhaustedError(
                "No providers are currently available. Please try again later."
            )

        last_error: Optional[Exception] = None

        for idx, provider in enumerate(candidate_providers):
            next_provider_name = (
                candidate_providers[idx + 1].name
                if idx + 1 < len(candidate_providers)
                else "none"
            )
            try:
                start = time.monotonic()
                response = await provider.generate(prompt, **kwargs)
                latency = time.monotonic() - start

                self._tracker.increment(provider.name)
                logger.info(
                    "Provider: %s | Task: %s | Latency: %.2fs",
                    provider.name, task_type.value, latency,
                )
                return response, provider.name

            except RateLimitError as exc:
                self._tracker.record_rate_limit(provider.name)
                self._manager.mark_unavailable(provider.name, duration_seconds=60)
                warning = (
                    f"⚠ {provider.name} rate limit reached. "
                    f"Switching to {next_provider_name}…"
                )
                logger.warning(
                    "Fallback triggered: %s → %s (RateLimit: %s)",
                    provider.name, next_provider_name, exc,
                )
                self._notify(warning)
                last_error = exc
                continue

            except QuotaExceededError as exc:
                self._tracker.record_error(provider.name)
                self._manager.mark_unavailable(
                    provider.name, duration_seconds=24 * 3600  # rest of the day
                )
                warning = (
                    f"⚠ {provider.name} quota exceeded. "
                    f"Switching to {next_provider_name}…"
                )
                logger.warning(
                    "Quota exceeded: %s → %s (%s)", provider.name, next_provider_name, exc
                )
                self._notify(warning)
                last_error = exc
                continue

            except ProviderError as exc:
                self._tracker.record_error(provider.name)
                logger.error(
                    "Provider %s failed: %s. Trying next provider.", provider.name, exc
                )
                last_error = exc
                continue

            except Exception as exc:  # noqa: BLE001
                self._tracker.record_error(provider.name)
                logger.error(
                    "Unexpected error from %s: %s. Trying next provider.",
                    provider.name, exc,
                )
                last_error = exc
                continue

        raise AllProvidersExhaustedError(
            f"All AI providers are currently unavailable. Last error: {last_error}"
        )

    def get_provider_status(self) -> Dict[str, Any]:
        """Return availability and usage stats for all providers."""
        return {
            name: self._tracker.get_stats(name)
            for name in self._manager.get_provider_names()
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_limits(self) -> Dict[str, int]:
        """Extract daily_limit values from provider config."""
        limits: Dict[str, int] = {}
        for name, cfg in self._config.get("providers", {}).items():
            if "daily_limit" in cfg:
                # Map config key to provider display name
                display = {
                    "gemini": "Gemini", "groq": "Groq",
                    "openrouter": "OpenRouter", "phi3": "Phi3",
                    "deepseek": "DeepSeek", "mistral": "Mistral",
                }.get(name, name)
                limits[display] = cfg["daily_limit"]
        return limits


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------


def load_provider_config(path: str = "config/provider_config.yaml") -> Dict[str, Any]:
    """Load provider configuration from *path*.

    Args:
        path: Path to the YAML config file.

    Returns:
        Parsed configuration dict, or empty dict on failure.
    """
    try:
        import yaml  # type: ignore[import]
        import os

        # Expand env vars in the YAML content before parsing
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        # Simple ${VAR} substitution
        import re
        def _replace_env(match: re.Match) -> str:
            return os.environ.get(match.group(1), "")
        raw = re.sub(r"\$\{([^}]+)\}", _replace_env, raw)
        return yaml.safe_load(raw) or {}
    except FileNotFoundError:
        logger.warning("Provider config not found at %s; using defaults.", path)
        return {}
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load provider config: %s", exc)
        return {}


# Module-level singleton
_router: AIRouter | None = None


def get_ai_router(config_path: str = "config/provider_config.yaml") -> AIRouter:
    """Return the module-level :class:`AIRouter` singleton."""
    global _router
    if _router is None:
        config = load_provider_config(config_path)
        _router = AIRouter(config=config)
    return _router
