"""Tests for the JARVIS output modules."""

import pytest
from jarvis.core.output.text_formatter import TextFormatter
from jarvis.core.output.response_manager import ResponseManager


class TestTextFormatter:
    def setup_method(self):
        self.fmt = TextFormatter()

    def test_chat_format_strips_whitespace(self):
        result = self.fmt.format_response("  hello  ", channel="chat")
        assert result == "hello"

    def test_voice_strips_markdown(self):
        result = self.fmt.format_response("**bold** and `code`", channel="voice")
        assert "**" not in result
        assert "`" not in result

    def test_voice_strips_code_blocks(self):
        result = self.fmt.format_response("```python\nprint('hi')\n```", channel="voice")
        assert "```" not in result

    def test_format_numbered_list(self):
        result = self.fmt.format_list(["a", "b", "c"], numbered=True)
        assert "1. a" in result
        assert "3. c" in result

    def test_format_bullet_list(self):
        result = self.fmt.format_list(["x", "y"])
        assert "• x" in result


class TestResponseManager:
    def test_respond_returns_dict(self):
        rm = ResponseManager(speak_by_default=False)
        result = rm.respond("Hello!", channel="api")
        assert "text" in result
        assert result["channel"] == "api"
        assert result["spoken"] is False
