"""Central memory store – coordinates all memory layers."""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from .short_term_memory import ShortTermMemory
from .long_term_memory import LongTermMemory
from .knowledge_memory import KnowledgeMemory
from .embedding_manager import EmbeddingManager

logger = logging.getLogger(__name__)


class MemoryStore:
    """Coordinates short-term, long-term, and knowledge memory layers.

    Provides a unified interface for storing and retrieving information
    across all memory systems.
    """

    def __init__(self, store_path: Optional[Path] = None) -> None:
        """Initialise all memory subsystems.

        Args:
            store_path: Optional path for long-term memory persistence.
        """
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(store_path)
        self.knowledge = KnowledgeMemory()
        self.embeddings = EmbeddingManager()
        logger.info("MemoryStore initialised")

    def add_interaction(self, user_input: str, assistant_response: str) -> None:
        """Record a complete user/assistant exchange.

        Args:
            user_input: The user's message.
            assistant_response: The assistant's reply.
        """
        self.short_term.add_message("user", user_input)
        self.short_term.add_message("assistant", assistant_response)

    def get_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent conversation context for the LLM.

        Args:
            limit: Number of recent messages to include.

        Returns:
            List of role/content dicts.
        """
        return self.short_term.get_context(limit)

    def remember(self, key: str, value: Any) -> None:
        """Persist a preference or fact to long-term memory."""
        self.long_term.set(key, value)

    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored preference or fact."""
        return self.long_term.get(key, default)

    def learn(self, content: str, title: str = "", tags: Optional[List[str]] = None) -> str:
        """Add a document to knowledge memory and index it for search.

        Args:
            content: Document text.
            title: Optional document title.
            tags: Optional tags.

        Returns:
            The document ID.
        """
        doc_id = self.knowledge.add_document(content, title, tags)
        self.embeddings.index(doc_id, content)
        return doc_id

    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge memory using keyword and semantic methods.

        Returns combined and deduplicated results.
        """
        keyword_results = self.knowledge.search(query, limit)
        semantic_results = self.embeddings.search(query, limit)

        seen_ids = {r["id"] for r in keyword_results}
        for sem in semantic_results:
            if sem["doc_id"] not in seen_ids:
                doc = self.knowledge.get(sem["doc_id"])
                if doc:
                    keyword_results.append(doc)
        return keyword_results[:limit]
