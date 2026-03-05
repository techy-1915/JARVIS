"""Tests for the JARVIS agent system."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from jarvis.core.agents.agent_base import AgentBase
from jarvis.core.agents.message_bus import Message, MessageBus, MessageType


class ConcreteAgent(AgentBase):
    """Minimal concrete agent for testing."""
    async def run(self, task):
        return self._success({"echo": task.get("input", "")})


class TestAgentBase:
    def test_agent_has_id(self):
        agent = ConcreteAgent("TestAgent")
        assert len(agent.agent_id) == 36  # UUID4 format

    def test_success_structure(self):
        agent = ConcreteAgent("TestAgent")
        result = agent._success("my result")
        assert result["status"] == "success"
        assert result["result"] == "my result"
        assert result["agent"] == "TestAgent"

    def test_error_structure(self):
        agent = ConcreteAgent("TestAgent")
        result = agent._error("something went wrong")
        assert result["status"] == "error"
        assert "something went wrong" in result["error"]

    def test_run_returns_success(self):
        agent = ConcreteAgent("TestAgent")
        result = asyncio.get_event_loop().run_until_complete(agent.run({"input": "hello"}))
        assert result["status"] == "success"


class TestMessageBus:
    def test_subscribe_and_publish(self):
        bus = MessageBus()
        received = []

        async def handler(msg):
            received.append(msg)

        bus.subscribe(MessageType.COMMAND, handler)
        msg = Message(MessageType.COMMAND, "test_sender", {"data": "hello"})

        asyncio.get_event_loop().run_until_complete(bus.publish(msg))
        assert len(received) == 1
        assert received[0].payload["data"] == "hello"

    def test_history_recorded(self):
        bus = MessageBus()
        msg = Message(MessageType.EVENT, "agent1", {"key": "value"})
        asyncio.get_event_loop().run_until_complete(bus.publish(msg))
        history = bus.get_history()
        assert len(history) >= 1

    def test_unsubscribe(self):
        bus = MessageBus()
        calls = []

        async def handler(msg):
            calls.append(msg)

        bus.subscribe(MessageType.QUERY, handler)
        bus.unsubscribe(MessageType.QUERY, handler)
        msg = Message(MessageType.QUERY, "sender", {})
        asyncio.get_event_loop().run_until_complete(bus.publish(msg))
        assert len(calls) == 0
