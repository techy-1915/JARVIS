"""Conversation logger – records every user/assistant interaction to JSONL files."""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_STORAGE_PATH = "training/datasets"


class ConversationLogger:
    """Appends conversation turns to daily JSONL files.

    Each entry follows the instruction-tuning format::

        {
            "instruction": "<user request>",
            "input": "<extra context>",
            "output": "<assistant response>",
            "metadata": {
                "timestamp": "2026-03-07T10:30:00",
                "model_used": "llama3.1:8b",
                "feedback_score": null,
                "conversation_id": "<uuid>"
            }
        }

    Files are named ``conversations_YYYY_MM_DD.jsonl`` and stored under
    *storage_path*.
    """

    def __init__(self, storage_path: str = _DEFAULT_STORAGE_PATH) -> None:
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _today_file(self) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y_%m_%d")
        return self._storage_path / f"conversations_{date_str}.jsonl"

    def _append(self, entry: Dict[str, Any]) -> None:
        path = self._today_file()
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def log_interaction(
        self,
        user_prompt: str,
        assistant_response: str,
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
    ) -> str:
        """Record a single user/assistant exchange.

        Args:
            user_prompt: The user's message.
            assistant_response: Jarvis's reply.
            context: Additional context injected into the prompt (e.g. memories).
            metadata: Arbitrary key/value pairs saved alongside the entry.
            conversation_id: Reuse an existing conversation ID or generate one.

        Returns:
            The conversation ID string.
        """
        conv_id = conversation_id or str(uuid.uuid4())
        meta: Dict[str, Any] = dict(metadata or {})
        meta.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        meta.setdefault("conversation_id", conv_id)

        entry: Dict[str, Any] = {
            "instruction": user_prompt,
            "input": context,
            "output": assistant_response,
            "metadata": meta,
        }

        try:
            self._append(entry)
            logger.debug("Logged conversation %s", conv_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to log conversation: %s", exc)

        return conv_id

    async def get_recent(
        self,
        days: int = 1,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return logged entries from the most recent *days* files.

        Args:
            days: How many daily files to look back (default 1 = today only).
            limit: Cap on the number of entries returned.

        Returns:
            List of entry dicts ordered oldest-first.
        """
        entries: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for delta in range(days):
            from datetime import timedelta

            date = now - timedelta(days=delta)
            date_str = date.strftime("%Y_%m_%d")
            path = self._storage_path / f"conversations_{date_str}.jsonl"
            if not path.exists():
                continue
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to read %s: %s", path, exc)

        # Oldest-first
        entries.sort(
            key=lambda e: e.get("metadata", {}).get("timestamp", ""),
        )
        if limit is not None:
            entries = entries[-limit:]
        return entries

    async def get_by_conversation_id(
        self, conversation_id: str, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Return all entries belonging to a specific conversation.

        Args:
            conversation_id: The ID to filter by.
            days: How far back to search.
        """
        all_entries = await self.get_recent(days=days)
        return [
            e
            for e in all_entries
            if e.get("metadata", {}).get("conversation_id") == conversation_id
        ]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_logger: Optional[ConversationLogger] = None


def get_conversation_logger() -> ConversationLogger:
    """Return the module-level singleton ConversationLogger instance."""
    global _default_logger
    if _default_logger is None:
        _default_logger = ConversationLogger()
    return _default_logger
