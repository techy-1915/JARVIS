"""Tests for the JARVIS memory modules."""

import pytest
from jarvis.core.memory.short_term_memory import ShortTermMemory
from jarvis.core.memory.knowledge_memory import KnowledgeMemory
from jarvis.core.memory.embedding_manager import EmbeddingManager
from jarvis.core.memory.memory_store import MemoryStore


class TestShortTermMemory:
    def test_add_and_retrieve(self):
        mem = ShortTermMemory(max_messages=5)
        mem.add_message("user", "Hello")
        mem.add_message("assistant", "Hi there!")
        ctx = mem.get_context()
        assert len(ctx) == 2
        assert ctx[0]["role"] == "user"
        assert ctx[1]["content"] == "Hi there!"

    def test_rolling_window(self):
        mem = ShortTermMemory(max_messages=3)
        for i in range(5):
            mem.add_message("user", f"msg {i}")
        assert len(mem) == 3

    def test_clear(self):
        mem = ShortTermMemory()
        mem.add_message("user", "test")
        mem.clear()
        assert len(mem) == 0

    def test_context_limit(self):
        mem = ShortTermMemory()
        for i in range(10):
            mem.add_message("user", f"msg {i}")
        ctx = mem.get_context(limit=3)
        assert len(ctx) == 3


class TestKnowledgeMemory:
    def test_add_and_search(self):
        km = KnowledgeMemory()
        km.add_document("Python is a great programming language", title="Python")
        results = km.search("Python")
        assert len(results) >= 1
        assert "Python" in results[0]["title"]

    def test_get_by_id(self):
        km = KnowledgeMemory()
        doc_id = km.add_document("test content", title="Test")
        doc = km.get(doc_id)
        assert doc is not None
        assert doc["title"] == "Test"

    def test_delete(self):
        km = KnowledgeMemory()
        doc_id = km.add_document("to be deleted")
        assert km.delete(doc_id) is True
        assert km.get(doc_id) is None

    def test_list_documents(self):
        km = KnowledgeMemory()
        km.add_document("doc 1", title="Doc 1")
        km.add_document("doc 2", title="Doc 2")
        docs = km.list_documents()
        assert len(docs) >= 2


class TestEmbeddingManager:
    def test_encode_returns_vector(self):
        em = EmbeddingManager()
        vec = em.encode("Hello world")
        assert isinstance(vec, list)
        assert len(vec) == 64

    def test_search_returns_results(self):
        em = EmbeddingManager()
        em.index("doc1", "Python programming")
        em.index("doc2", "JavaScript development")
        results = em.search("Python")
        assert len(results) >= 1
        assert results[0]["doc_id"] in ("doc1", "doc2")


class TestMemoryStore:
    def test_remember_and_recall(self, tmp_path):
        store = MemoryStore(store_path=tmp_path / "mem.json")
        store.remember("username", "Alice")
        assert store.recall("username") == "Alice"

    def test_recall_default(self, tmp_path):
        store = MemoryStore(store_path=tmp_path / "mem.json")
        assert store.recall("nonexistent", default="fallback") == "fallback"

    def test_add_interaction(self, tmp_path):
        store = MemoryStore(store_path=tmp_path / "mem.json")
        store.add_interaction("Hello", "Hi there!")
        ctx = store.get_context()
        assert len(ctx) == 2

    def test_learn_and_search(self, tmp_path):
        store = MemoryStore(store_path=tmp_path / "mem.json")
        store.learn("FastAPI is a modern Python web framework", title="FastAPI")
        results = store.search_knowledge("FastAPI")
        assert len(results) >= 1
