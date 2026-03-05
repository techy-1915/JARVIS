"""Knowledge memory – documents and structured data retrieval."""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KnowledgeMemory:
    """Stores and retrieves structured knowledge documents.

    Provides a lightweight in-memory document store.  For production,
    integrate with a vector database via ``EmbeddingManager``.
    """

    def __init__(self) -> None:
        self._documents: Dict[str, Dict[str, Any]] = {}

    def add_document(
        self,
        content: str,
        title: str = "",
        tags: Optional[List[str]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """Add a document to the knowledge store.

        Args:
            content: The document text.
            title: Optional document title.
            tags: Optional list of searchable tags.
            doc_id: Optional explicit ID; generated from content hash if not given.

        Returns:
            The assigned document ID.
        """
        if doc_id is None:
            doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]

        self._documents[doc_id] = {
            "id": doc_id,
            "title": title,
            "content": content,
            "tags": tags or [],
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.debug("Knowledge: added document %s (%s)", doc_id, title)
        return doc_id

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword search over stored documents.

        Args:
            query: Search terms (space-separated).
            limit: Maximum number of results.

        Returns:
            List of matching document dicts, ranked by keyword hits.
        """
        query_lower = query.lower()
        scored: List[tuple] = []
        for doc in self._documents.values():
            score = (
                doc["content"].lower().count(query_lower)
                + doc["title"].lower().count(query_lower) * 2
            )
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:limit]]

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        return self._documents.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        """Remove a document from the store."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False

    def list_documents(self) -> List[Dict[str, Any]]:
        """Return a summary list of all documents."""
        return [
            {"id": d["id"], "title": d["title"], "tags": d["tags"]}
            for d in self._documents.values()
        ]
