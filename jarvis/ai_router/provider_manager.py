"""Provider manager – priority ordering, availability tracking, and task routing."""

import logging
from typing import Dict, List, Optional

from ..ai_router.task_classifier import TaskType
from ..ai_router.usage_tracker import UsageTracker, get_usage_tracker
from ..providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default task → provider priority mapping
# ---------------------------------------------------------------------------

# Provider name → list of supported task types
_PROVIDER_TASK_MAP: Dict[str, List[TaskType]] = {
    "Gemini": [TaskType.REASONING, TaskType.NORMAL_CHAT, TaskType.EMBEDDINGS],
    "Groq": [TaskType.CODE_GENERATION, TaskType.NORMAL_CHAT],
    "OpenRouter": [
        TaskType.REASONING, TaskType.NORMAL_CHAT, TaskType.CODE_GENERATION,
    ],
    "Phi3": [TaskType.REASONING, TaskType.NORMAL_CHAT],
    "DeepSeek": [TaskType.CODE_GENERATION],
    "Mistral": [TaskType.NORMAL_CHAT, TaskType.REASONING],
}


class ProviderManager:
    """Manage a prioritised list of AI providers.

    Providers are tried in priority order (lowest index first).  A provider is
    skipped if:
    * it reports itself as unavailable via :meth:`BaseProvider.check_availability`, or
    * the :class:`UsageTracker` marks it unavailable (daily limit reached).

    Task-type filtering is applied so that unsuitable providers are moved to the
    end of the candidate list rather than skipped entirely, ensuring there is
    always a fallback.
    """

    def __init__(
        self,
        providers: List[BaseProvider],
        usage_tracker: Optional[UsageTracker] = None,
        task_map: Optional[Dict[str, List[TaskType]]] = None,
    ) -> None:
        """Initialise the manager.

        Args:
            providers: Ordered list of providers (index 0 = highest priority).
            usage_tracker: Shared :class:`UsageTracker` instance.
            task_map: Override for the default task→provider suitability map.
        """
        self._providers: List[BaseProvider] = providers
        self._tracker: UsageTracker = usage_tracker or get_usage_tracker()
        self._task_map: Dict[str, List[TaskType]] = task_map or _PROVIDER_TASK_MAP

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_available_providers(
        self, task_type: Optional[TaskType] = None
    ) -> List[BaseProvider]:
        """Return providers that are currently available, ordered by priority.

        Providers suitable for *task_type* come first; unsuitable ones are
        appended at the end so they can still serve as a last resort.

        Args:
            task_type: The type of task to be performed.

        Returns:
            Ordered list of available :class:`BaseProvider` instances.
        """
        available = [p for p in self._providers if self._is_available(p)]

        if task_type is None:
            return available

        suitable = [
            p for p in available
            if task_type in self._task_map.get(p.name, list(TaskType))
        ]
        unsuitable = [p for p in available if p not in suitable]
        return suitable + unsuitable

    def get_optimal_provider(
        self, task_type: Optional[TaskType] = None
    ) -> Optional[BaseProvider]:
        """Return the best available provider for *task_type* (or ``None``)."""
        providers = self.get_available_providers(task_type)
        return providers[0] if providers else None

    def mark_unavailable(self, provider_name: str, duration_seconds: int = 300) -> None:
        """Temporarily block a provider via the usage tracker.

        Args:
            provider_name: Name of the provider to block.
            duration_seconds: Duration in seconds (default 5 min).
        """
        self._tracker.mark_unavailable(provider_name, duration_seconds)
        logger.info("Provider %s blocked for %ds.", provider_name, duration_seconds)

    def reset_availability(self) -> None:
        """Reset all provider availability (intended for daily/test resets)."""
        for provider in self._providers:
            self._tracker.reset_provider(provider.name)
        logger.info("All provider availability has been reset.")

    def get_provider_names(self) -> List[str]:
        """Return names of all registered providers in priority order."""
        return [p.name for p in self._providers]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_available(self, provider: BaseProvider) -> bool:
        """Return True if *provider* passes both availability checks."""
        if not provider.available:
            return False
        if not self._tracker.is_available(provider.name):
            return False
        return True
