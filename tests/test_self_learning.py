"""Tests for the self-learning AI brain architecture.

Covers:
- VectorMemory (fallback mode, no ChromaDB required)
- ConversationLogger
- FeedbackManager
- AutoDatasetBuilder
- KnowledgeConsolidator
- SelfLearningLoop
- Extended ModelManager
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# VectorMemory
# ---------------------------------------------------------------------------


class TestVectorMemory:
    """Test the VectorMemory using its in-memory fallback (no ChromaDB needed)."""

    @pytest.fixture
    def vm(self):
        from jarvis.core.memory.vector_memory import VectorMemory

        # Force fallback mode by using a non-existent path that won't init ChromaDB
        mem = VectorMemory(
            persist_directory="/tmp/test_vector_db_nonexistent",
            collection_name="test_col",
        )
        # Bypass ChromaDB by pre-setting fallback only
        mem._initialized = True
        mem._client = None
        mem._collection = None
        return mem

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, vm):
        mem_id = await vm.store_memory("Paris is the capital of France", {"type": "fact"})
        assert mem_id is not None

        results = await vm.retrieve_similar("capital of France", top_k=5)
        assert len(results) > 0
        assert results[0]["text"] == "Paris is the capital of France"

    @pytest.mark.asyncio
    async def test_store_returns_unique_ids(self, vm):
        id1 = await vm.store_memory("first memory", {})
        id2 = await vm.store_memory("second memory", {})
        assert id1 != id2

    @pytest.mark.asyncio
    async def test_delete_memory(self, vm):
        mem_id = await vm.store_memory("delete me", {})
        deleted = await vm.delete_memory(mem_id)
        assert deleted is True

        # Second delete should return False
        deleted_again = await vm.delete_memory(mem_id)
        assert deleted_again is False

    @pytest.mark.asyncio
    async def test_update_memory(self, vm):
        mem_id = await vm.store_memory("original text", {"v": 1})
        updated = await vm.update_memory(mem_id, "updated text", {"v": 2})
        assert updated is True

        results = await vm.retrieve_similar("updated", top_k=1)
        assert any(r["text"] == "updated text" for r in results)

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, vm):
        result = await vm.update_memory("nonexistent-id", "text", {})
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_all(self, vm):
        await vm.store_memory("memory 1", {})
        await vm.store_memory("memory 2", {})
        count_before = await vm.count()
        assert count_before >= 2

        cleared = await vm.clear_all()
        assert cleared is True
        count_after = await vm.count()
        assert count_after == 0

    @pytest.mark.asyncio
    async def test_retrieve_empty(self, vm):
        results = await vm.retrieve_similar("anything", top_k=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_metadata_preserved(self, vm):
        meta = {"type": "test", "source": "unit_test"}
        mem_id = await vm.store_memory("test content", meta)
        results = await vm.retrieve_similar("test", top_k=1)
        assert len(results) > 0
        stored_meta = results[0]["metadata"]
        assert stored_meta.get("type") == "test"
        assert stored_meta.get("source") == "unit_test"


# ---------------------------------------------------------------------------
# ConversationLogger
# ---------------------------------------------------------------------------


class TestConversationLogger:
    @pytest.fixture
    def logger_obj(self, tmp_path):
        from jarvis.core.learning.conversation_logger import ConversationLogger

        return ConversationLogger(storage_path=str(tmp_path / "conversations"))

    @pytest.mark.asyncio
    async def test_log_and_retrieve(self, logger_obj):
        conv_id = await logger_obj.log_interaction(
            user_prompt="Hello JARVIS",
            assistant_response="Hello! How can I help?",
            context="",
            metadata={"model_used": "llama3.1:8b"},
        )
        assert conv_id is not None

        entries = await logger_obj.get_recent(days=1)
        assert len(entries) == 1
        assert entries[0]["instruction"] == "Hello JARVIS"
        assert entries[0]["output"] == "Hello! How can I help?"

    @pytest.mark.asyncio
    async def test_conversation_id_reuse(self, logger_obj):
        conv_id = "fixed-id-123"
        await logger_obj.log_interaction("q1", "a1", conversation_id=conv_id)
        await logger_obj.log_interaction("q2", "a2", conversation_id=conv_id)

        results = await logger_obj.get_by_conversation_id(conv_id, days=1)
        assert len(results) == 2
        assert all(r["metadata"]["conversation_id"] == conv_id for r in results)

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_conv(self, logger_obj):
        results = await logger_obj.get_by_conversation_id("unknown-xyz", days=1)
        assert results == []

    @pytest.mark.asyncio
    async def test_creates_daily_file(self, logger_obj, tmp_path):
        await logger_obj.log_interaction("test", "reply")
        conv_dir = tmp_path / "conversations"
        jsonl_files = list(conv_dir.glob("conversations_*.jsonl"))
        assert len(jsonl_files) == 1

    @pytest.mark.asyncio
    async def test_multiple_entries_append(self, logger_obj):
        for i in range(5):
            await logger_obj.log_interaction(f"q{i}", f"a{i}")
        entries = await logger_obj.get_recent(days=1)
        assert len(entries) == 5


# ---------------------------------------------------------------------------
# FeedbackManager
# ---------------------------------------------------------------------------


class TestFeedbackManager:
    @pytest.fixture
    def fm(self, tmp_path):
        from jarvis.core.learning.feedback_manager import FeedbackManager

        return FeedbackManager(db_path=str(tmp_path / "feedback.db"))

    @pytest.mark.asyncio
    async def test_record_and_retrieve(self, fm):
        conv_id = "conv_001"
        await fm.record_feedback(conv_id, "explicit", 0.9)
        score = await fm.get_conversation_score(conv_id)
        assert score == pytest.approx(0.9)

    @pytest.mark.asyncio
    async def test_implicit_score_good_response(self, fm):
        good_response = (
            "This is a well-structured answer. First, we consider the problem. "
            "Because of this reason, we conclude that the answer is correct. "
            "Therefore, the solution is valid. In conclusion, everything checks out."
        )
        score = await fm.calculate_implicit_score(good_response, {})
        assert score > 0.5

    @pytest.mark.asyncio
    async def test_implicit_score_short_response(self, fm):
        score = await fm.calculate_implicit_score("Yes.", {})
        assert score < 0.6

    @pytest.mark.asyncio
    async def test_implicit_score_error_response(self, fm):
        error_response = "[Error: Something went wrong] " * 5
        score = await fm.calculate_implicit_score(error_response, {})
        assert score < 0.4

    @pytest.mark.asyncio
    async def test_task_success_bonus(self, fm):
        base = await fm.calculate_implicit_score("A decent response " * 5, {})
        success = await fm.calculate_implicit_score(
            "A decent response " * 5, {"task_success": True}
        )
        assert success > base

    @pytest.mark.asyncio
    async def test_score_clamped(self, fm):
        score = await fm.calculate_implicit_score(
            "x" * 10000, {"task_success": True}
        )
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_weighted_average(self, fm):
        conv_id = "conv_weighted"
        await fm.record_feedback(conv_id, "implicit", 0.5)
        await fm.record_feedback(conv_id, "explicit", 1.0)
        score = await fm.get_conversation_score(conv_id)
        # explicit weight 2×, implicit weight 1×: (0.5*1 + 1.0*2) / 3 = 2.5/3 ≈ 0.833
        assert score == pytest.approx(2.5 / 3, abs=0.01)

    @pytest.mark.asyncio
    async def test_get_high_quality_conversations(self, fm):
        await fm.record_feedback("good_conv", "explicit", 0.9)
        await fm.record_feedback("bad_conv", "explicit", 0.3)

        results = await fm.get_high_quality_conversations(min_score=0.7, limit=10)
        ids = [r["conversation_id"] for r in results]
        assert "good_conv" in ids
        assert "bad_conv" not in ids

    @pytest.mark.asyncio
    async def test_delete_feedback(self, fm):
        await fm.record_feedback("to_delete", "explicit", 0.8)
        success = await fm.delete_feedback("to_delete")
        assert success is True
        score = await fm.get_conversation_score("to_delete")
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_no_feedback_returns_zero(self, fm):
        score = await fm.get_conversation_score("nonexistent_conv")
        assert score == 0.0


# ---------------------------------------------------------------------------
# AutoDatasetBuilder
# ---------------------------------------------------------------------------


class TestAutoDatasetBuilder:
    @pytest.fixture
    def builder(self, tmp_path):
        from jarvis.core.learning.auto_dataset_builder import AutoDatasetBuilder

        return AutoDatasetBuilder(output_path=str(tmp_path / "datasets"))

    @pytest.mark.asyncio
    async def test_filter_quality_removes_blank(self, builder):
        data = [
            {"instruction": "hello", "output": "hi", "input": ""},
            {"instruction": "", "output": "hi", "input": ""},  # blank instruction
            {"instruction": "q", "output": "", "input": ""},  # blank output
        ]
        filtered = await builder.filter_quality(data)
        assert len(filtered) == 1

    @pytest.mark.asyncio
    async def test_convert_to_instruction_format(self, builder):
        data = [
            {
                "instruction": "What is 2+2?",
                "input": "",
                "output": "4",
                "metadata": {"model_used": "test"},
            }
        ]
        examples = await builder.convert_to_instruction_format(data)
        assert len(examples) == 1
        assert examples[0]["instruction"] == "What is 2+2?"
        assert examples[0]["output"] == "4"
        assert "metadata" in examples[0]

    @pytest.mark.asyncio
    async def test_deduplicate_exact_duplicates(self, builder):
        dup = {"instruction": "same", "input": "", "output": "same answer"}
        examples = [dup, dup, dup]
        deduped = await builder.deduplicate_examples(examples, similarity_threshold=0.9)
        assert len(deduped) == 1

    @pytest.mark.asyncio
    async def test_deduplicate_preserves_unique(self, builder):
        examples = [
            {"instruction": "capital of France", "input": "", "output": "Paris"},
            {"instruction": "capital of Germany", "input": "", "output": "Berlin"},
            {"instruction": "write Python code", "input": "", "output": "def hello(): pass"},
        ]
        deduped = await builder.deduplicate_examples(examples)
        assert len(deduped) == 3

    @pytest.mark.asyncio
    async def test_save_training_dataset(self, builder, tmp_path):
        examples = [
            {"instruction": "Q1", "input": "", "output": "A1", "metadata": {}},
            {"instruction": "Q2", "input": "", "output": "A2", "metadata": {}},
        ]
        path = await builder.save_training_dataset(examples, "test_output.jsonl")
        saved = Path(path)
        assert saved.exists()
        lines = saved.read_text().strip().splitlines()
        assert len(lines) == 2
        entry = json.loads(lines[0])
        assert entry["instruction"] == "Q1"


# ---------------------------------------------------------------------------
# KnowledgeConsolidator
# ---------------------------------------------------------------------------


class TestKnowledgeConsolidator:
    @pytest.fixture
    def consolidator(self, tmp_path):
        from jarvis.core.learning.knowledge_consolidator import KnowledgeConsolidator

        return KnowledgeConsolidator(archive_path=str(tmp_path / "archive"))

    @pytest.mark.asyncio
    async def test_cluster_empty(self, consolidator):
        clusters = await consolidator.cluster_memories([], eps=0.3)
        assert clusters == []

    @pytest.mark.asyncio
    async def test_cluster_single_memory(self, consolidator):
        memories = [{"id": "1", "text": "Paris is the capital of France"}]
        clusters = await consolidator.cluster_memories(memories, eps=0.3)
        assert len(clusters) == 1
        assert len(clusters[0]) == 1

    @pytest.mark.asyncio
    async def test_deduplicate_cluster_selects_longest(self, consolidator):
        cluster = [
            {"id": "1", "text": "short"},
            {"id": "2", "text": "much longer text that should win"},
            {"id": "3", "text": "medium length text here"},
        ]
        best = await consolidator.deduplicate_cluster(cluster)
        assert best["id"] == "2"

    @pytest.mark.asyncio
    async def test_summarize_cluster_fallback(self, consolidator):
        cluster = [
            {"id": "1", "text": "a short fact"},
            {"id": "2", "text": "a much longer and more detailed fact about something"},
        ]
        summary = await consolidator.summarize_cluster(cluster, brain=None)
        # Fallback picks the longest
        assert "longer" in summary

    @pytest.mark.asyncio
    async def test_archive_memories(self, consolidator, tmp_path):
        memories = [
            {"id": "mem1", "text": "first memory"},
            {"id": "mem2", "text": "second memory"},
        ]
        success = await consolidator.archive_memories(
            ["mem1", "mem2"],
            archive_path=str(tmp_path / "archive"),
            all_memories=memories,
        )
        assert success is True
        archive_files = list((tmp_path / "archive").glob("archive_*.json"))
        assert len(archive_files) == 1
        content = json.loads(archive_files[0].read_text())
        assert len(content) == 2


# ---------------------------------------------------------------------------
# SelfLearningLoop
# ---------------------------------------------------------------------------


class TestSelfLearningLoop:
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        from jarvis.core.learning.self_learning_loop import SelfLearningLoop

        loop = SelfLearningLoop(interval_hours=999, min_conversations=99999)
        loop.start()
        assert loop.is_running
        await asyncio.sleep(0.05)
        loop.stop()
        await asyncio.sleep(0.05)

    @pytest.mark.asyncio
    async def test_start_idempotent(self):
        from jarvis.core.learning.self_learning_loop import SelfLearningLoop

        loop = SelfLearningLoop(interval_hours=999, min_conversations=99999)
        task1 = loop.start()
        task2 = loop.start()
        assert task1 is task2
        loop.stop()
        await asyncio.sleep(0.05)


# ---------------------------------------------------------------------------
# Extended ModelManager
# ---------------------------------------------------------------------------


class TestModelManagerExtended:
    def test_version_bumping(self):
        from jarvis.core.brain.model_manager import ModelManager

        assert ModelManager._bump_version([]) == "1.0.0"
        assert ModelManager._bump_version(["1.0.0"]) == "1.0.1"
        assert ModelManager._bump_version(["1.0.0", "1.0.5"]) == "1.0.6"
        assert ModelManager._bump_version(["2.3.7"]) == "2.3.8"

    @pytest.mark.asyncio
    async def test_check_for_new_training_no_dir(self, tmp_path):
        from jarvis.core.brain.model_manager import ModelManager

        mgr = ModelManager(registry_path=str(tmp_path / "registry.yaml"))
        result = await mgr.check_for_new_training()
        assert result is None

    @pytest.mark.asyncio
    async def test_load_new_model_local_path(self, tmp_path):
        from jarvis.core.brain.model_manager import ModelManager

        adapter_dir = tmp_path / "test_adapter"
        adapter_dir.mkdir()
        mgr = ModelManager(registry_path=str(tmp_path / "registry.yaml"))
        result = await mgr.load_new_model(str(adapter_dir))
        assert result is True
        assert mgr._pending_model == str(adapter_dir)

    @pytest.mark.asyncio
    async def test_rollback_no_previous(self, tmp_path):
        from jarvis.core.brain.model_manager import ModelManager

        mgr = ModelManager(registry_path=str(tmp_path / "registry.yaml"))
        result = await mgr.rollback_model()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_performance_metrics_unavailable(self, tmp_path):
        from unittest.mock import AsyncMock

        from jarvis.core.brain.model_manager import ModelManager

        mgr = ModelManager(registry_path=str(tmp_path / "registry.yaml"))
        mgr._brain.is_available = AsyncMock(return_value=False)
        mgr._brain.get_model_info = AsyncMock(return_value={})
        metrics = await mgr.get_model_performance_metrics()
        assert metrics["score"] == 0.0
        assert metrics["available"] is False

    def test_registry_save_and_load(self, tmp_path):
        from jarvis.core.brain.model_manager import ModelManager

        registry_file = tmp_path / "registry.yaml"
        mgr = ModelManager(registry_path=str(registry_file))
        registry = {"models": [{"version": "1.0.0", "name": "test"}]}
        mgr._save_registry(registry)
        loaded = mgr._load_registry()
        assert loaded["models"][0]["name"] == "test"
