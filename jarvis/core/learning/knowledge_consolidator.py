"""Knowledge consolidator – clusters and summarises stored vector memories."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_ARCHIVE_PATH = "data/vector_db/archive"


def _cosine_distance(a: List[float], b: List[float]) -> float:
    """Compute cosine distance between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    if mag_a == 0.0 or mag_b == 0.0:
        return 1.0
    return 1.0 - dot / (mag_a * mag_b)


class KnowledgeConsolidator:
    """Periodically consolidates the vector memory to remove duplicates and
    summarise clusters of related knowledge.

    The process (intended to run weekly):

    1. Retrieve all memories from the vector store.
    2. Cluster similar memories using a simple greedy algorithm.
    3. Summarise each cluster via the LLM brain.
    4. Remove duplicates – keep the best (longest) representative.
    5. Store consolidated knowledge back to the vector store.
    6. Archive old raw memories to cold storage.
    """

    def __init__(
        self,
        archive_path: str = _DEFAULT_ARCHIVE_PATH,
    ) -> None:
        self._archive_path = Path(archive_path)
        self._archive_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _embed_text(self, text: str) -> List[float]:
        """Embed *text* using the same model as VectorMemory."""
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")
            return model.encode(text).tolist()
        except ImportError:
            from ..memory.vector_memory import _hash_embed

            return _hash_embed(text)

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def cluster_memories(
        self, memories: List[Dict[str, Any]], eps: float = 0.3
    ) -> List[List[Dict[str, Any]]]:
        """Group memories into clusters using greedy distance-threshold algorithm.

        Two memories are placed in the same cluster when their cosine distance
        is <= *eps*.

        Args:
            memories: List of memory dicts (each must have a ``"text"`` key).
            eps: Distance threshold; lower → tighter clusters.

        Returns:
            List of clusters, where each cluster is a list of memory dicts.
        """
        if not memories:
            return []

        # Pre-compute embeddings
        embeddings: List[List[float]] = []
        for mem in memories:
            embeddings.append(self._embed_text(mem.get("text", "")))

        clusters: List[List[int]] = []  # indices into memories
        assigned = [False] * len(memories)

        for i in range(len(memories)):
            if assigned[i]:
                continue
            cluster = [i]
            assigned[i] = True
            for j in range(i + 1, len(memories)):
                if assigned[j]:
                    continue
                if _cosine_distance(embeddings[i], embeddings[j]) <= eps:
                    cluster.append(j)
                    assigned[j] = True
            clusters.append(cluster)

        return [[memories[idx] for idx in cluster] for cluster in clusters]

    async def summarize_cluster(
        self,
        cluster: List[Dict[str, Any]],
        brain: Optional[Any] = None,
    ) -> str:
        """Summarise a cluster of related memories into a single statement.

        If *brain* is provided (a BrainInterface), it is used to generate the
        summary.  Otherwise falls back to concatenating the first few texts.

        Args:
            cluster: List of memory dicts with ``"text"`` keys.
            brain: Optional BrainInterface for LLM-based summarisation.

        Returns:
            A concise summary string.
        """
        texts = [m.get("text", "") for m in cluster if m.get("text")]
        if not texts:
            return ""

        if brain is not None:
            combined = "\n".join(f"- {t}" for t in texts[:10])
            prompt = (
                f"Summarise the following related facts into one concise statement:\n{combined}"
            )
            try:
                summary = await brain.think(prompt, [])
                return summary.strip()
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM summarisation failed: %s", exc)

        # Fallback: return the longest text as the representative
        return max(texts, key=len)

    async def deduplicate_cluster(
        self, cluster: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Choose the best representative from a cluster.

        Currently selects the entry with the longest text.

        Args:
            cluster: List of memory dicts.

        Returns:
            The selected representative dict.
        """
        return max(cluster, key=lambda m: len(m.get("text", "")))

    async def archive_memories(
        self,
        memory_ids: List[str],
        archive_path: Optional[str] = None,
        all_memories: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Move memories to cold-storage JSON archive.

        Args:
            memory_ids: IDs of memories to archive.
            archive_path: Override the default archive directory.
            all_memories: Full memory dicts (used to preserve text).  If None,
                          only IDs are archived.

        Returns:
            True on success.
        """
        import json

        target_dir = Path(archive_path) if archive_path else self._archive_path
        target_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M%S")
        archive_file = target_dir / f"archive_{date_str}.json"

        # Build lookup from all_memories if available
        lookup: Dict[str, Dict[str, Any]] = {}
        if all_memories:
            for m in all_memories:
                mid = m.get("id", "")
                if mid:
                    lookup[mid] = m

        payload = [
            lookup.get(mid, {"id": mid}) for mid in memory_ids
        ]

        try:
            archive_file.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.info("Archived %d memories to %s", len(memory_ids), archive_file)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to archive memories: %s", exc)
            return False

    async def consolidate_knowledge(
        self,
        eps: float = 0.3,
        brain: Optional[Any] = None,
    ) -> Dict[str, int]:
        """Run the full consolidation pipeline.

        Steps:
        1. Retrieve all memories.
        2. Cluster similar memories.
        3. For each cluster with >1 member: summarise, pick representative,
           delete duplicates, store consolidated summary.
        4. Archive deleted memories.

        Args:
            eps: Clustering distance threshold.
            brain: Optional BrainInterface for LLM summarisation.

        Returns:
            Stats dict: ``{total, clusters, consolidated, archived}``.
        """
        from ..memory.vector_memory import get_vector_memory

        vm = get_vector_memory()
        total_count = await vm.count()
        if total_count == 0:
            return {"total": 0, "clusters": 0, "consolidated": 0, "archived": 0}

        # Retrieve all memories via similarity search on a broad query
        # (We use an empty query which returns random results when using fallback)
        all_memories = await vm.retrieve_similar("", top_k=min(total_count, 10000))
        clusters = await self.cluster_memories(all_memories, eps=eps)

        archived_ids: List[str] = []
        consolidated_count = 0

        for cluster in clusters:
            if len(cluster) <= 1:
                continue  # Nothing to consolidate

            # Summarise
            summary = await self.summarize_cluster(cluster, brain=brain)

            # Pick representative
            representative = await self.deduplicate_cluster(cluster)

            # Archive duplicates (all except the representative)
            dup_ids = [
                m["id"] for m in cluster if m["id"] != representative.get("id", "")
            ]
            archived_ids.extend(dup_ids)

            # Delete duplicates from vector store
            for dup_id in dup_ids:
                await vm.delete_memory(dup_id)

            # Update representative with consolidated summary
            if summary and representative.get("id"):
                meta = representative.get("metadata", {})
                meta["consolidated"] = True
                meta["consolidated_at"] = datetime.now(timezone.utc).isoformat()
                await vm.update_memory(representative["id"], summary, meta)
                consolidated_count += 1

        # Archive deleted memories
        if archived_ids:
            await self.archive_memories(archived_ids, all_memories=all_memories)

        stats = {
            "total": total_count,
            "clusters": len(clusters),
            "consolidated": consolidated_count,
            "archived": len(archived_ids),
        }
        logger.info("Knowledge consolidation complete: %s", stats)
        return stats


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_consolidator: Optional[KnowledgeConsolidator] = None


def get_knowledge_consolidator() -> KnowledgeConsolidator:
    """Return the module-level singleton KnowledgeConsolidator instance."""
    global _default_consolidator
    if _default_consolidator is None:
        _default_consolidator = KnowledgeConsolidator()
    return _default_consolidator
