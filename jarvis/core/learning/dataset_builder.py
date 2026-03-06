"""Dataset builder – converts raw interaction logs into fine-tuning datasets."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from .learning_engine import (
    CATEGORY_CODING,
    CATEGORY_CONVERSATION,
    CATEGORY_REASONING,
    LearningEngine,
)

logger = logging.getLogger(__name__)


class DatasetBuilder:
    """Converts raw JSONL interaction logs into structured training datasets.

    Supported output formats:
    - ``alpaca`` – {instruction, input, output} triplets for Alpaca-style fine-tuning.
    - ``chatml``  – {messages: [{role, content}, …]} for ChatML / OpenAI-style fine-tuning.
    """

    _FORMATS = ("alpaca", "chatml")

    def __init__(self, learning_engine: LearningEngine) -> None:
        self.engine = learning_engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_conversation_dataset(self, fmt: str = "alpaca") -> List[Dict[str, Any]]:
        """Build a fine-tuning dataset from conversational interactions.

        Args:
            fmt: Output format – ``"alpaca"`` or ``"chatml"``.

        Returns:
            List of formatted training examples.
        """
        return self._build(CATEGORY_CONVERSATION, fmt)

    def build_coding_dataset(self, fmt: str = "alpaca") -> List[Dict[str, Any]]:
        """Build a fine-tuning dataset from coding interactions.

        Args:
            fmt: Output format – ``"alpaca"`` or ``"chatml"``.

        Returns:
            List of formatted training examples.
        """
        return self._build(CATEGORY_CODING, fmt)

    def build_reasoning_dataset(self, fmt: str = "alpaca") -> List[Dict[str, Any]]:
        """Build a fine-tuning dataset from reasoning interactions.

        Args:
            fmt: Output format – ``"alpaca"`` or ``"chatml"``.

        Returns:
            List of formatted training examples.
        """
        return self._build(CATEGORY_REASONING, fmt)

    def export_all(self, output_dir: str = "datasets/export", fmt: str = "alpaca") -> Dict[str, str]:
        """Export all three category datasets to JSON files.

        Args:
            output_dir: Directory to write exported files.
            fmt: Output format – ``"alpaca"`` or ``"chatml"``.

        Returns:
            Mapping of category name → output file path.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        result: Dict[str, str] = {}

        for category in (CATEGORY_CONVERSATION, CATEGORY_CODING, CATEGORY_REASONING):
            entries = self._build(category, fmt)
            out_file = out_path / f"{category}_{fmt}.json"
            with out_file.open("w") as fh:
                json.dump(entries, fh, indent=2)
            logger.info("Exported %d %s examples → %s", len(entries), category, out_file)
            result[category] = str(out_file)

        return result

    def clean_dataset(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove low-quality entries from a dataset.

        Current rules:
        - Drop entries where input or output is blank.
        - Drop entries where output is an error message (starts with "[Error").
        - Deduplicate by (input, output) pair.

        Args:
            entries: Raw training examples.

        Returns:
            Cleaned list of examples.
        """
        seen: set = set()
        cleaned: List[Dict[str, Any]] = []
        for entry in entries:
            inp = entry.get("instruction") or entry.get("input", "")
            out = entry.get("output", "")
            if not inp.strip() or not out.strip():
                continue
            if out.startswith("[Error") or out.startswith("[Streaming error"):
                continue
            key = (inp.strip().lower(), out.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(entry)
        return cleaned

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build(self, category: str, fmt: str) -> List[Dict[str, Any]]:
        if fmt not in self._FORMATS:
            raise ValueError(f"Unknown format '{fmt}'. Choose from: {self._FORMATS}")
        raw = self.engine.build_dataset(category)
        formatter = self._format_alpaca if fmt == "alpaca" else self._format_chatml
        return [formatter(entry, category) for entry in raw]

    @staticmethod
    def _format_alpaca(entry: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Convert a raw entry to Alpaca format.

        Alpaca convention: ``instruction`` = the user task, ``input`` = optional
        context (empty string when not needed), ``output`` = the expected response.
        """
        system_context = {
            CATEGORY_CODING: "You are JARVIS, an expert programming assistant.",
            CATEGORY_REASONING: "You are JARVIS, an analytical reasoning assistant.",
            CATEGORY_CONVERSATION: "You are JARVIS, a helpful AI assistant.",
        }.get(category, "You are JARVIS, a helpful AI assistant.")
        return {
            "instruction": system_context,
            "input": entry.get("input", ""),
            "output": entry.get("output", ""),
        }

    @staticmethod
    def _format_chatml(entry: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Convert a raw entry to ChatML format."""
        system_content = {
            CATEGORY_CODING: "You are JARVIS, an expert programming assistant.",
            CATEGORY_REASONING: "You are JARVIS, an analytical reasoning assistant.",
            CATEGORY_CONVERSATION: "You are JARVIS, a helpful AI assistant.",
        }.get(category, "You are JARVIS, a helpful AI assistant.")
        return {
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": entry.get("input", "")},
                {"role": "assistant", "content": entry.get("output", "")},
            ]
        }
