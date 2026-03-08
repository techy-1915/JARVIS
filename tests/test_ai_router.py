"""Tests for the AI router system – task classifier, usage tracker, provider manager, and router."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jarvis.ai_router.task_classifier import TaskClassifier, TaskType, get_task_classifier
from jarvis.ai_router.usage_tracker import UsageTracker
from jarvis.ai_router.provider_manager import ProviderManager
from jarvis.ai_router.router import AIRouter
from jarvis.providers.base_provider import (
    AllProvidersExhaustedError,
    BaseProvider,
    ProviderError,
    QuotaExceededError,
    RateLimitError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeProvider(BaseProvider):
    """Deterministic fake provider for testing."""

    def __init__(self, name: str, response: str = "ok", raise_error: Exception | None = None):
        super().__init__(name)
        self._response = response
        self._raise = raise_error
        self.call_count = 0

    async def generate(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        if self._raise:
            raise self._raise
        return self._response

    def check_availability(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return f"fake-{self.name}"


# ---------------------------------------------------------------------------
# TaskClassifier tests
# ---------------------------------------------------------------------------


class TestTaskClassifier:
    def setup_method(self):
        self.clf = TaskClassifier()

    def test_code_generation_force_keyword(self):
        assert self.clf.classify("write code to sort a list") == TaskType.CODE_GENERATION
        assert self.clf.classify("write a program in python") == TaskType.CODE_GENERATION
        assert self.clf.classify("debug this code") == TaskType.CODE_GENERATION

    def test_code_generation_keyword_score(self):
        assert self.clf.classify("write a python function to sort a list") == TaskType.CODE_GENERATION

    def test_code_generation_code_block(self):
        assert self.clf.classify("What does this do?\n```python\nprint('hi')\n```") == TaskType.CODE_GENERATION

    def test_reasoning_keywords(self):
        result = self.clf.classify("analyze the pros and cons of this approach")
        assert result == TaskType.REASONING

    def test_normal_chat_hello(self):
        assert self.clf.classify("hello, how are you?") == TaskType.NORMAL_CHAT

    def test_normal_chat_default(self):
        result = self.clf.classify("What is the capital of France?")
        # Should be either NORMAL_CHAT or REASONING depending on keywords
        assert result in (TaskType.NORMAL_CHAT, TaskType.REASONING)

    def test_embeddings(self):
        assert self.clf.classify("create an embedding for this text") == TaskType.EMBEDDINGS

    def test_returns_task_type(self):
        result = self.clf.classify("some random text")
        assert isinstance(result, TaskType)

    def test_singleton(self):
        c1 = get_task_classifier()
        c2 = get_task_classifier()
        assert c1 is c2


# ---------------------------------------------------------------------------
# UsageTracker tests
# ---------------------------------------------------------------------------


class TestUsageTracker:
    def test_increment_and_stats(self):
        tracker = UsageTracker()
        tracker.increment("gemini", tokens=100)
        stats = tracker.get_stats("gemini")
        assert stats["requests_today"] == 1
        assert stats["tokens_used_today"] == 100

    def test_is_available_within_limit(self):
        tracker = UsageTracker(limits={"gemini": 10})
        for _ in range(5):
            tracker.increment("gemini")
        assert tracker.is_available("gemini") is True

    def test_is_unavailable_when_limit_reached(self):
        tracker = UsageTracker(limits={"gemini": 3})
        for _ in range(3):
            tracker.increment("gemini")
        assert tracker.is_available("gemini") is False

    def test_mark_unavailable_and_recover(self):
        tracker = UsageTracker()
        tracker.mark_unavailable("groq", duration_seconds=1)
        assert tracker.is_available("groq") is False
        time.sleep(1.1)
        assert tracker.is_available("groq") is True

    def test_record_rate_limit(self):
        tracker = UsageTracker()
        tracker.record_rate_limit("groq")
        stats = tracker.get_stats("groq")
        assert stats["rate_limit_hits"] == 1

    def test_record_error(self):
        tracker = UsageTracker()
        tracker.record_error("openrouter")
        stats = tracker.get_stats("openrouter")
        assert stats["error_count"] == 1

    def test_reset_provider(self):
        tracker = UsageTracker()
        tracker.increment("phi3", tokens=50)
        tracker.reset_provider("phi3")
        stats = tracker.get_stats("phi3")
        assert stats["requests_today"] == 0

    def test_get_all_stats(self):
        tracker = UsageTracker()
        tracker.increment("gemini")
        tracker.increment("groq")
        all_stats = tracker.get_all_stats()
        assert "gemini" in all_stats
        assert "groq" in all_stats


# ---------------------------------------------------------------------------
# ProviderManager tests
# ---------------------------------------------------------------------------


class TestProviderManager:
    def test_get_available_providers_all_available(self):
        providers = [FakeProvider("A"), FakeProvider("B"), FakeProvider("C")]
        mgr = ProviderManager(providers)
        available = mgr.get_available_providers()
        assert len(available) == 3

    def test_get_available_providers_respects_usage_tracker(self):
        tracker = UsageTracker()
        providers = [FakeProvider("A"), FakeProvider("B")]
        mgr = ProviderManager(providers, usage_tracker=tracker)
        tracker.mark_unavailable("A", duration_seconds=60)
        available = mgr.get_available_providers()
        assert len(available) == 1
        assert available[0].name == "B"

    def test_mark_unavailable(self):
        tracker = UsageTracker()
        providers = [FakeProvider("A"), FakeProvider("B")]
        mgr = ProviderManager(providers, usage_tracker=tracker)
        mgr.mark_unavailable("A", duration_seconds=60)
        available = mgr.get_available_providers()
        assert all(p.name != "A" for p in available)

    def test_get_provider_names(self):
        providers = [FakeProvider("X"), FakeProvider("Y")]
        mgr = ProviderManager(providers)
        assert mgr.get_provider_names() == ["X", "Y"]

    def test_task_filtering_puts_suitable_first(self):
        # Only "Gemini" name is in the default task map for REASONING
        p1 = FakeProvider("Gemini")
        p2 = FakeProvider("DeepSeek")
        from jarvis.ai_router.provider_manager import _PROVIDER_TASK_MAP
        task_map = {
            "Gemini": [TaskType.REASONING],
            "DeepSeek": [TaskType.CODE_GENERATION],
        }
        mgr = ProviderManager([p1, p2], task_map=task_map)
        available = mgr.get_available_providers(TaskType.REASONING)
        assert available[0].name == "Gemini"
        assert available[1].name == "DeepSeek"


# ---------------------------------------------------------------------------
# AIRouter tests
# ---------------------------------------------------------------------------


class TestAIRouter:
    def _make_router(self, providers, notify=None):
        tracker = UsageTracker()
        mgr = ProviderManager(providers, usage_tracker=tracker)
        router = AIRouter.__new__(AIRouter)
        router._config = {}
        router._classifier = get_task_classifier()
        router._tracker = tracker
        router._manager = mgr
        router._notify = notify or (lambda msg: None)
        return router

    @pytest.mark.asyncio
    async def test_successful_route(self):
        provider = FakeProvider("TestProvider", response="Hello!")
        router = self._make_router([provider])
        response, name = await router.route("hello there")
        assert response == "Hello!"
        assert name == "TestProvider"

    @pytest.mark.asyncio
    async def test_fallback_on_rate_limit(self):
        p1 = FakeProvider("Primary", raise_error=RateLimitError("rate limited"))
        p2 = FakeProvider("Fallback", response="fallback response")
        notifications = []
        router = self._make_router([p1, p2], notify=notifications.append)
        response, name = await router.route("hello")
        assert response == "fallback response"
        assert name == "Fallback"
        assert any("rate limit" in n.lower() for n in notifications)

    @pytest.mark.asyncio
    async def test_fallback_on_quota_exceeded(self):
        p1 = FakeProvider("Primary", raise_error=QuotaExceededError("quota"))
        p2 = FakeProvider("Fallback", response="fallback")
        router = self._make_router([p1, p2])
        response, name = await router.route("hello")
        assert response == "fallback"
        assert name == "Fallback"

    @pytest.mark.asyncio
    async def test_fallback_on_provider_error(self):
        p1 = FakeProvider("P1", raise_error=ProviderError("api error"))
        p2 = FakeProvider("P2", response="ok")
        router = self._make_router([p1, p2])
        response, name = await router.route("hi")
        assert response == "ok"

    @pytest.mark.asyncio
    async def test_all_providers_exhausted(self):
        p1 = FakeProvider("P1", raise_error=ProviderError("fail"))
        p2 = FakeProvider("P2", raise_error=ProviderError("fail"))
        router = self._make_router([p1, p2])
        with pytest.raises(AllProvidersExhaustedError):
            await router.route("hi")

    @pytest.mark.asyncio
    async def test_no_providers_available(self):
        router = self._make_router([])
        with pytest.raises(AllProvidersExhaustedError):
            await router.route("hi")

    @pytest.mark.asyncio
    async def test_task_type_override(self):
        provider = FakeProvider("P", response="code response")
        router = self._make_router([provider])
        response, _ = await router.route("hello", task_type=TaskType.CODE_GENERATION)
        assert response == "code response"

    def test_get_provider_status(self):
        provider = FakeProvider("P1")
        router = self._make_router([provider])
        status = router.get_provider_status()
        assert "P1" in status
