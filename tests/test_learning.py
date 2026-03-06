"""Tests for jarvis.core.learning – LearningEngine and DatasetBuilder."""

import json
import time
from pathlib import Path

import pytest

from jarvis.core.learning.dataset_builder import DatasetBuilder
from jarvis.core.learning.learning_engine import (
    CATEGORY_CODING,
    CATEGORY_CONVERSATION,
    CATEGORY_REASONING,
    LearningEngine,
)


@pytest.fixture
def tmp_engine(tmp_path):
    """Create a LearningEngine backed by a temporary directory."""
    engine = LearningEngine(dataset_dir=str(tmp_path), flush_interval=0.05)
    yield engine
    engine.stop()


@pytest.fixture
def started_engine(tmp_path):
    """Create and start a LearningEngine backed by a temporary directory."""
    engine = LearningEngine(dataset_dir=str(tmp_path), flush_interval=0.05)
    engine.start()
    yield engine
    engine.stop()


class TestLearningEngine:
    def test_category_dirs_created(self, tmp_path):
        LearningEngine(dataset_dir=str(tmp_path))
        for cat in (CATEGORY_CONVERSATION, CATEGORY_CODING, CATEGORY_REASONING):
            assert (tmp_path / cat).is_dir()

    def test_log_interaction_buffers_entry(self, tmp_engine):
        tmp_engine.log_interaction("hello", "hi there")
        assert len(tmp_engine._buffer) == 1

    def test_flush_writes_to_disk(self, tmp_engine, tmp_path):
        tmp_engine.log_interaction("hello", "hi there", intent="conversation")
        tmp_engine._flush_buffer()
        files = list((tmp_path / CATEGORY_CONVERSATION).glob("*.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["input"] == "hello"
        assert entry["output"] == "hi there"

    def test_intent_routing(self, tmp_engine, tmp_path):
        tmp_engine.log_interaction("write code", "def foo(): ...", intent="coding")
        tmp_engine.log_interaction("analyze this", "My analysis...", intent="reasoning")
        tmp_engine._flush_buffer()
        assert list((tmp_path / CATEGORY_CODING).glob("*.jsonl"))
        assert list((tmp_path / CATEGORY_REASONING).glob("*.jsonl"))

    def test_background_flush(self, started_engine, tmp_path):
        started_engine.log_interaction("ping", "pong", intent="conversation")
        # Wait long enough for the background thread to flush
        time.sleep(0.3)
        files = list((tmp_path / CATEGORY_CONVERSATION).glob("*.jsonl"))
        assert len(files) == 1

    def test_get_dataset_stats(self, tmp_engine, tmp_path):
        tmp_engine.log_interaction("q1", "a1", intent="conversation")
        tmp_engine.log_interaction("q2", "a2", intent="coding")
        tmp_engine._flush_buffer()
        stats = tmp_engine.get_dataset_stats()
        assert stats[CATEGORY_CONVERSATION] == 1
        assert stats[CATEGORY_CODING] == 1
        assert stats[CATEGORY_REASONING] == 0

    def test_build_dataset_returns_entries(self, tmp_engine):
        tmp_engine.log_interaction("q", "a", intent="conversation")
        tmp_engine._flush_buffer()
        entries = tmp_engine.build_dataset(CATEGORY_CONVERSATION)
        assert len(entries) == 1
        assert entries[0]["input"] == "q"

    def test_start_stop_idempotent(self, tmp_engine):
        tmp_engine.start()
        tmp_engine.start()  # second call should be a no-op
        tmp_engine.stop()
        tmp_engine.stop()  # second stop should be safe


class TestDatasetBuilder:
    @pytest.fixture
    def builder_with_data(self, tmp_path):
        engine = LearningEngine(dataset_dir=str(tmp_path))
        for i in range(3):
            engine.log_interaction(f"user msg {i}", f"assistant reply {i}", intent="conversation")
        for i in range(2):
            engine.log_interaction(f"write code {i}", f"def foo_{i}(): pass", intent="coding")
        for i in range(1):
            engine.log_interaction(f"analyze {i}", f"My analysis {i}", intent="reasoning")
        engine._flush_buffer()
        builder = DatasetBuilder(engine)
        yield builder
        engine.stop()

    def test_build_conversation_dataset_alpaca(self, builder_with_data):
        entries = builder_with_data.build_conversation_dataset(fmt="alpaca")
        assert len(entries) == 3
        for entry in entries:
            assert "instruction" in entry
            assert "input" in entry
            assert "output" in entry

    def test_build_coding_dataset_alpaca(self, builder_with_data):
        entries = builder_with_data.build_coding_dataset(fmt="alpaca")
        assert len(entries) == 2

    def test_build_reasoning_dataset_alpaca(self, builder_with_data):
        entries = builder_with_data.build_reasoning_dataset(fmt="alpaca")
        assert len(entries) == 1

    def test_chatml_format(self, builder_with_data):
        entries = builder_with_data.build_conversation_dataset(fmt="chatml")
        assert len(entries) == 3
        for entry in entries:
            assert "messages" in entry
            assert len(entry["messages"]) == 3
            roles = [m["role"] for m in entry["messages"]]
            assert roles == ["system", "user", "assistant"]

    def test_invalid_format_raises(self, builder_with_data):
        with pytest.raises(ValueError, match="Unknown format"):
            builder_with_data.build_conversation_dataset(fmt="invalid")

    def test_export_all_creates_files(self, builder_with_data, tmp_path):
        output_dir = str(tmp_path / "export")
        exported = builder_with_data.export_all(output_dir=output_dir, fmt="alpaca")
        for cat in (CATEGORY_CONVERSATION, CATEGORY_CODING, CATEGORY_REASONING):
            assert cat in exported
            assert Path(exported[cat]).exists()

    def test_clean_dataset_removes_blank(self, builder_with_data):
        dirty = [
            {"instruction": "hello", "input": "", "output": "hi"},
            {"instruction": "", "input": "", "output": "hi"},  # blank instruction
            {"instruction": "q", "input": "", "output": ""},  # blank output
        ]
        cleaned = builder_with_data.clean_dataset(dirty)
        assert len(cleaned) == 1

    def test_clean_dataset_removes_errors(self, builder_with_data):
        dirty = [
            {"instruction": "q", "input": "", "output": "[Error: something failed]"},
            {"instruction": "q", "input": "", "output": "good answer"},
        ]
        cleaned = builder_with_data.clean_dataset(dirty)
        assert len(cleaned) == 1
        assert cleaned[0]["output"] == "good answer"

    def test_clean_dataset_deduplicates(self, builder_with_data):
        duplicate = {"instruction": "same", "input": "", "output": "same answer"}
        dirty = [duplicate, duplicate, duplicate]
        cleaned = builder_with_data.clean_dataset(dirty)
        assert len(cleaned) == 1
