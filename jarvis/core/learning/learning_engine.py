"""Learning engine – logs interactions and builds training datasets."""

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Dataset category constants
CATEGORY_CONVERSATION = "conversations"
CATEGORY_CODING = "coding"
CATEGORY_REASONING = "reasoning"


class LearningEngine:
    """Background learning pipeline that logs interactions and produces datasets.

    Interactions are appended to JSONL files under *dataset_dir*.  A background
    thread periodically flushes buffered entries so the caller is never blocked.
    """

    def __init__(
        self,
        dataset_dir: str = "datasets",
        flush_interval: float = 30.0,
    ) -> None:
        self.dataset_dir = Path(dataset_dir)
        self.flush_interval = flush_interval
        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Ensure category subdirectories exist
        for category in (CATEGORY_CONVERSATION, CATEGORY_CODING, CATEGORY_REASONING):
            (self.dataset_dir / category).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background flush thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._flush_loop,
            name="learning-engine-flush",
            daemon=True,
        )
        self._thread.start()
        logger.info("LearningEngine started (flush_interval=%.1fs)", self.flush_interval)

    def stop(self) -> None:
        """Stop the background flush thread and flush remaining entries."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._flush_buffer()
        logger.info("LearningEngine stopped")

    def log_interaction(
        self,
        user_input: str,
        assistant_response: str,
        intent: str = CATEGORY_CONVERSATION,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a user–assistant interaction for later dataset generation.

        Args:
            user_input: The user's raw text input.
            assistant_response: JARVIS's response text.
            intent: Routing category (conversations, coding, reasoning).
            metadata: Optional extra fields (session_id, model, latency_ms, …).
        """
        category = self._intent_to_category(intent)
        entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "input": user_input,
            "output": assistant_response,
        }
        if metadata:
            entry["metadata"] = metadata

        with self._lock:
            self._buffer.append(entry)

    def get_dataset_stats(self) -> Dict[str, int]:
        """Return the number of logged entries per category.

        Returns:
            Mapping of category name → entry count (sum of all JSONL files).
        """
        stats: Dict[str, int] = {}
        for category in (CATEGORY_CONVERSATION, CATEGORY_CODING, CATEGORY_REASONING):
            cat_dir = self.dataset_dir / category
            count = 0
            for jsonl_file in cat_dir.glob("*.jsonl"):
                count += self._count_lines(jsonl_file)
            stats[category] = count
        return stats

    def build_dataset(self, category: str) -> List[Dict[str, Any]]:
        """Load and return all entries for *category*.

        Args:
            category: One of CATEGORY_CONVERSATION, CATEGORY_CODING,
                      CATEGORY_REASONING.

        Returns:
            List of interaction dicts.
        """
        cat_dir = self.dataset_dir / category
        entries: List[Dict[str, Any]] = []
        for jsonl_file in sorted(cat_dir.glob("*.jsonl")):
            with jsonl_file.open() as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            logger.warning("Skipping malformed JSONL line in %s", jsonl_file)
        return entries

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _intent_to_category(intent: str) -> str:
        """Map a routing intent string to a dataset category."""
        if intent in ("coding", "code", CATEGORY_CODING):
            return CATEGORY_CODING
        if intent in ("reasoning", "reason", CATEGORY_REASONING):
            return CATEGORY_REASONING
        return CATEGORY_CONVERSATION

    def _flush_loop(self) -> None:
        """Periodically flush the in-memory buffer to disk."""
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=self.flush_interval)
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Write buffered entries to their respective JSONL files."""
        with self._lock:
            if not self._buffer:
                return
            batch = self._buffer[:]
            self._buffer.clear()

        date_tag = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        buckets: Dict[str, List[Dict[str, Any]]] = {
            CATEGORY_CONVERSATION: [],
            CATEGORY_CODING: [],
            CATEGORY_REASONING: [],
        }
        for entry in batch:
            category = entry.get("category", CATEGORY_CONVERSATION)
            buckets.setdefault(category, []).append(entry)

        for category, entries in buckets.items():
            if not entries:
                continue
            out_file = self.dataset_dir / category / f"{date_tag}.jsonl"
            try:
                with out_file.open("a") as fh:
                    for entry in entries:
                        fh.write(json.dumps(entry) + "\n")
                logger.debug("Flushed %d entries to %s", len(entries), out_file)
            except OSError as exc:
                logger.error("Failed to write dataset file %s: %s", out_file, exc)

    @staticmethod
    def _count_lines(path: Path) -> int:
        """Count non-empty lines in a file."""
        try:
            return sum(1 for line in path.open() if line.strip())
        except OSError:
            return 0


# Module-level singleton
_engine: Optional[LearningEngine] = None
_engine_lock = threading.Lock()


def get_learning_engine(dataset_dir: str = "datasets") -> LearningEngine:
    """Return (and lazily create) the module-level LearningEngine singleton."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = LearningEngine(dataset_dir=dataset_dir)
            _engine.start()
    return _engine
