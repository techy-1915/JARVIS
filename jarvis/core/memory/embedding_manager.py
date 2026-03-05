"""Embedding manager – semantic retrieval helpers."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embeddings for semantic search.

    This is a stub implementation.  Replace ``encode`` with a real
    embedding model (e.g., sentence-transformers) for production use.
    The interface is designed to be compatible with vector databases
    such as ChromaDB or FAISS.
    """

    def __init__(self, model_name: str = "stub") -> None:
        """Initialise the embedding manager.

        Args:
            model_name: Name of the embedding model to use.
        """
        self.model_name = model_name
        self._vectors: Dict[str, List[float]] = {}
        logger.info("EmbeddingManager initialised with model: %s", model_name)

    def encode(self, text: str) -> List[float]:
        """Encode text into a vector representation.

        Args:
            text: Input text.

        Returns:
            A list of floats representing the embedding.
            (Stub: returns character code averages for determinism.)
        """
        if not text:
            return []
        avg = sum(ord(c) for c in text) / len(text)
        return [avg / 128.0] * 64  # 64-dim stub vector

    def index(self, doc_id: str, text: str) -> None:
        """Index a document's text for later similarity search.

        Args:
            doc_id: Unique document identifier.
            text: Document content to embed.
        """
        self._vectors[doc_id] = self.encode(text)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find the most semantically similar documents.

        Args:
            query: The search query.
            top_k: Number of results to return.

        Returns:
            List of dicts with ``doc_id`` and ``score`` keys.
        """
        if not self._vectors:
            return []
        query_vec = self.encode(query)

        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = sum(x ** 2 for x in a) ** 0.5
            mag_b = sum(x ** 2 for x in b) ** 0.5
            if mag_a == 0 or mag_b == 0:
                return 0.0
            return dot / (mag_a * mag_b)

        scored = [
            {"doc_id": doc_id, "score": cosine_similarity(query_vec, vec)}
            for doc_id, vec in self._vectors.items()
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
