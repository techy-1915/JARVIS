"""Automatic dataset builder – collects high-quality conversations and converts them
to instruction-tuning format ready for fine-tuning."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT_PATH = "training/datasets"
_SIMILARITY_THRESHOLD = 0.9  # ratio-based dedup threshold


def _simple_similarity(a: str, b: str) -> float:
    """Fast token-overlap-based similarity in [0, 1]."""
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


class AutoDatasetBuilder:
    """Builds fine-tuning datasets from stored conversations and feedback scores.

    Pipeline::

        Stored Conversations
          ↓
        Filter High-Quality (score >= min_score)
          ↓
        Convert to Instruction Format
          ↓
        Deduplicate Similar Examples
          ↓
        Append to Training Dataset (JSONL)
    """

    def __init__(
        self,
        output_path: str = _DEFAULT_OUTPUT_PATH,
    ) -> None:
        self._output_path = Path(output_path)
        self._output_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Pipeline stages
    # ------------------------------------------------------------------

    async def collect_conversations(
        self,
        since: Optional[datetime] = None,
        min_score: float = 0.7,
        days_back: int = 1,
    ) -> List[Dict[str, Any]]:
        """Retrieve logged conversations and filter by quality score.

        Args:
            since: Ignore entries older than this timestamp (UTC).
            min_score: Minimum feedback score to include.
            days_back: How many daily log files to search.

        Returns:
            List of raw conversation entry dicts.
        """
        from .conversation_logger import get_conversation_logger
        from .feedback_manager import get_feedback_manager

        conv_logger = get_conversation_logger()
        feedback_mgr = get_feedback_manager()

        entries = await conv_logger.get_recent(days=days_back)
        high_quality_ids = {
            item["conversation_id"]
            for item in await feedback_mgr.get_high_quality_conversations(
                min_score=min_score, limit=10000
            )
        }

        filtered: List[Dict[str, Any]] = []
        for entry in entries:
            meta = entry.get("metadata", {})
            conv_id = meta.get("conversation_id", "")
            ts_str = meta.get("timestamp", "")

            # Timestamp filter
            if since and ts_str:
                try:
                    entry_ts = datetime.fromisoformat(ts_str)
                    if entry_ts < since:
                        continue
                except ValueError:
                    pass

            # Quality filter: use feedback score if available, otherwise use
            # an implicit score based on output length/content
            if conv_id in high_quality_ids:
                filtered.append(entry)
            else:
                # Compute implicit score on-the-fly for entries without explicit feedback
                implicit = await feedback_mgr.calculate_implicit_score(
                    entry.get("output", ""), meta
                )
                if implicit >= min_score:
                    filtered.append(entry)

        return filtered

    async def filter_quality(
        self, conversations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove entries with empty instruction or output.

        Args:
            conversations: Raw entry dicts from the conversation logger.

        Returns:
            Cleaned list.
        """
        result = []
        for entry in conversations:
            instruction = entry.get("instruction", "").strip()
            output = entry.get("output", "").strip()
            if instruction and output:
                result.append(entry)
        return result

    async def convert_to_instruction_format(
        self, conversations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert raw entries to Alpaca instruction format.

        Returns:
            List of dicts with ``instruction``, ``input``, ``output``,
            and ``metadata`` keys.
        """
        examples: List[Dict[str, Any]] = []
        for entry in conversations:
            examples.append(
                {
                    "instruction": entry.get("instruction", "").strip(),
                    "input": entry.get("input", "").strip(),
                    "output": entry.get("output", "").strip(),
                    "metadata": entry.get("metadata", {}),
                }
            )
        return examples

    async def deduplicate_examples(
        self,
        examples: List[Dict[str, Any]],
        similarity_threshold: float = _SIMILARITY_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """Remove near-duplicate examples.

        Two examples are considered duplicates when their instruction +
        output text overlap exceeds *similarity_threshold*.

        Args:
            examples: Instruction-format dicts.
            similarity_threshold: Jaccard similarity threshold (0.0–1.0).

        Returns:
            Deduplicated list.
        """
        unique: List[Dict[str, Any]] = []
        seen_texts: List[str] = []

        for ex in examples:
            candidate = f"{ex.get('instruction','')} {ex.get('output','')}".strip()
            is_dup = any(
                _simple_similarity(candidate, seen) >= similarity_threshold
                for seen in seen_texts
            )
            if not is_dup:
                unique.append(ex)
                seen_texts.append(candidate)

        logger.debug(
            "Deduplication: %d → %d examples (threshold=%.2f)",
            len(examples),
            len(unique),
            similarity_threshold,
        )
        return unique

    async def save_training_dataset(
        self, examples: List[Dict[str, Any]], filename: str
    ) -> str:
        """Append *examples* to a JSONL file.

        Args:
            examples: List of instruction-format dicts.
            filename: Filename (relative names are resolved under *output_path*).

        Returns:
            Absolute path to the saved file.
        """
        path = Path(filename)
        if not path.is_absolute():
            path = self._output_path / filename

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            for ex in examples:
                fh.write(json.dumps(ex, ensure_ascii=False) + "\n")

        logger.info("Saved %d examples to %s", len(examples), path)
        return str(path)

    async def run_pipeline(
        self,
        min_score: float = 0.7,
        days_back: int = 1,
        since: Optional[datetime] = None,
        similarity_threshold: float = _SIMILARITY_THRESHOLD,
        output_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the full collection → filter → convert → dedup → save pipeline.

        Returns:
            Summary dict with keys ``"collected"``, ``"after_filter"``,
            ``"after_dedup"``, ``"saved"``, ``"filename"``.
        """
        if output_filename is None:
            date_str = datetime.now(timezone.utc).strftime("%Y_%m_%d")
            output_filename = f"training_{date_str}.jsonl"

        # 1. Collect
        raw = await self.collect_conversations(
            since=since, min_score=min_score, days_back=days_back
        )
        collected = len(raw)

        # 2. Filter
        filtered = await self.filter_quality(raw)

        # 3. Convert
        examples = await self.convert_to_instruction_format(filtered)
        after_filter = len(examples)

        # 4. Deduplicate
        deduped = await self.deduplicate_examples(examples, similarity_threshold)
        after_dedup = len(deduped)

        # 5. Save
        saved_path = ""
        if deduped:
            saved_path = await self.save_training_dataset(deduped, output_filename)

        summary = {
            "collected": collected,
            "after_filter": after_filter,
            "after_dedup": after_dedup,
            "saved": after_dedup,
            "filename": saved_path,
        }
        logger.info("Dataset pipeline complete: %s", summary)
        return summary


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_builder: Optional[AutoDatasetBuilder] = None


def get_auto_dataset_builder() -> AutoDatasetBuilder:
    """Return the module-level singleton AutoDatasetBuilder instance."""
    global _default_builder
    if _default_builder is None:
        _default_builder = AutoDatasetBuilder()
    return _default_builder
