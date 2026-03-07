"""Vector memory using ChromaDB for persistent semantic storage."""

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------

try:
    import chromadb
    from chromadb.config import Settings

    _CHROMA_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CHROMA_AVAILABLE = False
    logger.warning("chromadb not installed – VectorMemory will operate in stub mode")

try:
    from sentence_transformers import SentenceTransformer

    _ST_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ST_AVAILABLE = False
    logger.warning(
        "sentence-transformers not installed – VectorMemory will use simple hash embeddings"
    )


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------


def _hash_embed(text: str, dim: int = 384) -> List[float]:
    """Deterministic pseudo-embedding via repeated SHA-256 hashing.

    Used only when *sentence-transformers* is unavailable so the rest of
    the system can still operate (with degraded semantic quality).
    """
    digest = hashlib.sha256(text.encode()).hexdigest()
    # Extend hash to desired dimension by re-hashing with index suffix
    floats: List[float] = []
    seed = digest
    while len(floats) < dim:
        seed = hashlib.sha256(seed.encode()).hexdigest()
        floats.extend([int(seed[i : i + 2], 16) / 255.0 for i in range(0, len(seed) - 1, 2)])
    return floats[:dim]


# ---------------------------------------------------------------------------
# VectorMemory
# ---------------------------------------------------------------------------


class VectorMemory:
    """Persistent semantic vector memory backed by ChromaDB.

    Falls back to in-memory storage when ChromaDB is not installed.

    Usage::

        vm = VectorMemory()
        mem_id = await vm.store_memory("Paris is the capital of France", {"type": "fact"})
        results = await vm.retrieve_similar("capital of France", top_k=3)
    """

    _DEFAULT_PERSIST_DIR = "data/vector_db"
    _DEFAULT_COLLECTION = "jarvis_memory"
    _DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        persist_directory: str = _DEFAULT_PERSIST_DIR,
        collection_name: str = _DEFAULT_COLLECTION,
        embedding_model: str = _DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        self._persist_dir = persist_directory
        self._collection_name = collection_name
        self._embedding_model_name = embedding_model
        self._embedding_model: Optional[Any] = None
        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None
        # Fallback in-memory store when ChromaDB is unavailable
        self._fallback: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    # ------------------------------------------------------------------
    # Initialisation (lazy)
    # ------------------------------------------------------------------

    def _ensure_initialized(self) -> None:
        """Lazy-initialize ChromaDB client and embedding model."""
        if self._initialized:
            return
        self._initialized = True

        # Embedding model
        if _ST_AVAILABLE:
            try:
                self._embedding_model = SentenceTransformer(self._embedding_model_name)
            except Exception as exc:
                logger.warning("Failed to load SentenceTransformer: %s", exc)

        # ChromaDB client
        if _CHROMA_AVAILABLE:
            try:
                self._client = chromadb.PersistentClient(
                    path=self._persist_dir,
                    settings=Settings(anonymized_telemetry=False),
                )
                self._collection = self._client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(
                    "VectorMemory initialized with ChromaDB at '%s'", self._persist_dir
                )
            except Exception as exc:
                logger.warning("ChromaDB initialization failed: %s – using fallback", exc)
                self._client = None
                self._collection = None
        else:
            logger.info("VectorMemory using in-memory fallback (ChromaDB not available)")

    def _embed(self, text: str) -> List[float]:
        """Return an embedding vector for *text*."""
        if self._embedding_model is not None:
            try:
                vec = self._embedding_model.encode(text)
                return vec.tolist()
            except Exception as exc:
                logger.warning("Embedding failed: %s – using hash fallback", exc)
        return _hash_embed(text)

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def store_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Embed and persist *text* with optional *metadata*.

        Returns:
            The generated memory ID (UUID4 string).
        """
        self._ensure_initialized()
        memory_id = str(uuid.uuid4())
        meta = dict(metadata or {})
        meta.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        meta.setdefault("text", text)

        if self._collection is not None:
            try:
                embedding = self._embed(text)
                self._collection.add(
                    ids=[memory_id],
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[meta],
                )
                logger.debug("Stored memory %s", memory_id)
                return memory_id
            except Exception as exc:
                logger.error("Failed to store memory in ChromaDB: %s", exc)

        # Fallback path
        self._fallback[memory_id] = {"text": text, "metadata": meta}
        return memory_id

    async def retrieve_similar(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve the *top_k* memories most similar to *query*.

        Returns:
            List of dicts with keys ``"id"``, ``"text"``, ``"metadata"``,
            and ``"distance"``.
        """
        self._ensure_initialized()

        if self._collection is not None:
            try:
                embedding = self._embed(query)
                count = self._collection.count()
                k = min(top_k, max(count, 1))
                results = self._collection.query(
                    query_embeddings=[embedding],
                    n_results=k,
                    include=["documents", "metadatas", "distances"],
                )
                items: List[Dict[str, Any]] = []
                ids = results.get("ids", [[]])[0]
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                dists = results.get("distances", [[]])[0]
                for mem_id, doc, meta, dist in zip(ids, docs, metas, dists):
                    items.append(
                        {
                            "id": mem_id,
                            "text": doc,
                            "metadata": meta or {},
                            "distance": dist,
                        }
                    )
                return items
            except Exception as exc:
                logger.error("Failed to retrieve from ChromaDB: %s", exc)

        # Fallback: return all memories up to top_k (no semantic ranking)
        items = [
            {"id": k, "text": v["text"], "metadata": v["metadata"], "distance": 0.0}
            for k, v in list(self._fallback.items())[:top_k]
        ]
        return items

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete the memory with the given *memory_id*.

        Returns:
            True if the memory was found and deleted, False otherwise.
        """
        self._ensure_initialized()

        if self._collection is not None:
            try:
                self._collection.delete(ids=[memory_id])
                return True
            except Exception as exc:
                logger.error("Failed to delete memory %s: %s", memory_id, exc)
                return False

        if memory_id in self._fallback:
            del self._fallback[memory_id]
            return True
        return False

    async def update_memory(
        self, memory_id: str, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing memory in-place.

        Returns:
            True on success, False if the memory was not found.
        """
        self._ensure_initialized()
        meta = dict(metadata or {})
        meta.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        meta.setdefault("text", text)

        if self._collection is not None:
            try:
                embedding = self._embed(text)
                self._collection.update(
                    ids=[memory_id],
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[meta],
                )
                return True
            except Exception as exc:
                logger.error("Failed to update memory %s: %s", memory_id, exc)
                return False

        if memory_id in self._fallback:
            self._fallback[memory_id] = {"text": text, "metadata": meta}
            return True
        return False

    async def clear_all(self) -> bool:
        """Delete all memories from the collection.

        Returns:
            True on success.
        """
        self._ensure_initialized()

        if self._collection is not None:
            try:
                self._client.delete_collection(self._collection_name)
                self._collection = self._client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                return True
            except Exception as exc:
                logger.error("Failed to clear ChromaDB collection: %s", exc)
                return False

        self._fallback.clear()
        return True

    async def count(self) -> int:
        """Return the total number of stored memories."""
        self._ensure_initialized()

        if self._collection is not None:
            try:
                return self._collection.count()
            except Exception as exc:
                logger.error("Failed to count memories: %s", exc)

        return len(self._fallback)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_vm: Optional[VectorMemory] = None


def get_vector_memory() -> VectorMemory:
    """Return the module-level singleton VectorMemory instance."""
    global _default_vm
    if _default_vm is None:
        _default_vm = VectorMemory()
    return _default_vm
