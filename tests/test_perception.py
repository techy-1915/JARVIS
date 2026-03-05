"""Tests for the JARVIS perception modules."""

import pytest
from jarvis.core.perception.text_input import TextInputProcessor
from jarvis.core.perception.wake_word import WakeWordDetector
from jarvis.core.perception.input_normalizer import InputNormalizer


class TestTextInputProcessor:
    def setup_method(self):
        self.proc = TextInputProcessor()

    def test_basic_processing(self):
        result = self.proc.process("Hello JARVIS")
        assert result["text"] == "Hello JARVIS"
        assert result["session_id"] == "default"

    def test_whitespace_normalisation(self):
        result = self.proc.process("  hello   world  ")
        assert result["text"] == "hello world"

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            self.proc.process("")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="too long"):
            self.proc.process("x" * 10_001)

    def test_session_id_preserved(self):
        result = self.proc.process("test", session_id="abc123")
        assert result["session_id"] == "abc123"


class TestWakeWordDetector:
    def test_detects_wake_phrase(self):
        detector = WakeWordDetector(wake_phrase="hey jarvis")
        assert detector.check_text("hey jarvis, what time is it?") is True

    def test_case_insensitive(self):
        detector = WakeWordDetector(wake_phrase="hey jarvis")
        assert detector.check_text("HEY JARVIS do something") is True

    def test_no_match(self):
        detector = WakeWordDetector(wake_phrase="hey jarvis")
        assert detector.check_text("play some music") is False

    def test_callback_invoked(self):
        triggered = []
        detector = WakeWordDetector(wake_phrase="hey jarvis", callback=lambda: triggered.append(1))
        detector.check_text("hey jarvis!")
        assert len(triggered) == 1

    def test_start_stop(self):
        detector = WakeWordDetector()
        assert not detector.is_active
        detector.start_listening()
        assert detector.is_active
        detector.stop_listening()
        assert not detector.is_active


class TestInputNormalizer:
    def setup_method(self):
        self.norm = InputNormalizer(wake_phrase="hey jarvis")

    def test_basic_normalisation(self):
        result = self.norm.normalize("Hello!")
        assert result["text"] == "Hello!"
        assert result["source"] == "chat"

    def test_wake_word_detected(self):
        result = self.norm.normalize("hey jarvis turn on the lights")
        assert result["wake_word_detected"] is True
        assert "hey jarvis" not in result["clean_text"]

    def test_source_tag(self):
        result = self.norm.normalize("test", source="voice")
        assert result["source"] == "voice"
