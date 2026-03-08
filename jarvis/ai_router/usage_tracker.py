"""Usage tracking for AI providers – enforces daily limits and rate limits."""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProviderUsage:
    """Runtime usage counters for a single provider."""

    requests_today: int = 0
    tokens_used_today: int = 0
    rate_limit_hits: int = 0
    error_count: int = 0
    last_reset_date: str = field(default_factory=lambda: str(date.today()))
    # Unix timestamp after which the provider is available again (0 = available)
    unavailable_until: float = 0.0


class UsageTracker:
    """Thread-safe daily usage tracker for AI providers.

    Tracks request counts, token usage, and rate-limit events.  Providers that
    exceed their *daily_limit* are automatically marked unavailable for the rest
    of the day.  Counters reset at midnight (checked on every access).
    """

    def __init__(self, limits: Optional[Dict[str, int]] = None) -> None:
        """Initialise the tracker.

        Args:
            limits: Mapping of ``provider_name → daily_request_limit``.
                    Providers not listed have no enforced limit.
        """
        self._lock = threading.Lock()
        self._limits: Dict[str, int] = limits or {}
        self._usage: Dict[str, ProviderUsage] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def increment(self, provider_name: str, tokens: int = 0) -> None:
        """Record one successful request (and optionally token count).

        Args:
            provider_name: Identifier of the provider.
            tokens: Number of tokens consumed (optional).
        """
        with self._lock:
            usage = self._get_or_create(provider_name)
            self._maybe_reset(usage)
            usage.requests_today += 1
            usage.tokens_used_today += tokens

            limit = self._limits.get(provider_name)
            if limit and usage.requests_today >= limit:
                # Mark unavailable until midnight
                usage.unavailable_until = self._next_midnight()
                logger.warning(
                    "Provider %s reached daily limit (%d). Unavailable until midnight.",
                    provider_name, limit,
                )

    def record_rate_limit(self, provider_name: str) -> None:
        """Increment the rate-limit-hit counter for a provider."""
        with self._lock:
            usage = self._get_or_create(provider_name)
            self._maybe_reset(usage)
            usage.rate_limit_hits += 1

    def record_error(self, provider_name: str) -> None:
        """Increment the error counter for a provider."""
        with self._lock:
            usage = self._get_or_create(provider_name)
            self._maybe_reset(usage)
            usage.error_count += 1

    def mark_unavailable(self, provider_name: str, duration_seconds: int = 300) -> None:
        """Mark a provider as temporarily unavailable.

        Args:
            provider_name: Provider to mark.
            duration_seconds: How long (seconds) to block.  Defaults to 5 min.
        """
        with self._lock:
            usage = self._get_or_create(provider_name)
            usage.unavailable_until = time.time() + duration_seconds
            logger.info(
                "Provider %s marked unavailable for %ds.", provider_name, duration_seconds
            )

    def is_available(self, provider_name: str) -> bool:
        """Return ``True`` if the provider is currently available."""
        with self._lock:
            usage = self._get_or_create(provider_name)
            self._maybe_reset(usage)
            if usage.unavailable_until > time.time():
                return False
            limit = self._limits.get(provider_name)
            if limit and usage.requests_today >= limit:
                return False
            return True

    def get_stats(self, provider_name: str) -> Dict:
        """Return a snapshot of usage stats for the provider."""
        with self._lock:
            usage = self._get_or_create(provider_name)
            self._maybe_reset(usage)
            return {
                "provider": provider_name,
                "requests_today": usage.requests_today,
                "tokens_used_today": usage.tokens_used_today,
                "rate_limit_hits": usage.rate_limit_hits,
                "error_count": usage.error_count,
                "available": usage.unavailable_until <= time.time(),
                "daily_limit": self._limits.get(provider_name),
            }

    def get_all_stats(self) -> Dict[str, Dict]:
        """Return stats for every tracked provider."""
        return {name: self.get_stats(name) for name in list(self._usage.keys())}

    def reset_provider(self, provider_name: str) -> None:
        """Force-reset counters for a provider (useful for testing)."""
        with self._lock:
            self._usage[provider_name] = ProviderUsage()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create(self, provider_name: str) -> ProviderUsage:
        if provider_name not in self._usage:
            self._usage[provider_name] = ProviderUsage()
        return self._usage[provider_name]

    @staticmethod
    def _maybe_reset(usage: ProviderUsage) -> None:
        """Reset counters if the date has changed since last reset."""
        today = str(date.today())
        if usage.last_reset_date != today:
            usage.requests_today = 0
            usage.tokens_used_today = 0
            usage.rate_limit_hits = 0
            usage.error_count = 0
            usage.last_reset_date = today
            usage.unavailable_until = 0.0

    @staticmethod
    def _next_midnight() -> float:
        """Unix timestamp of the upcoming midnight."""
        import datetime as dt
        now = dt.datetime.now()
        midnight = dt.datetime(now.year, now.month, now.day) + dt.timedelta(days=1)
        return midnight.timestamp()


# Module-level singleton
_tracker: UsageTracker | None = None


def get_usage_tracker(limits: Optional[Dict[str, int]] = None) -> UsageTracker:
    """Return the module-level :class:`UsageTracker` singleton."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker(limits=limits)
    return _tracker
