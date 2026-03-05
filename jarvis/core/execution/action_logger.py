"""Action logger – records all executed actions for audit and replay."""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = Path("jarvis/logs/actions.jsonl")


class ActionLogger:
    """Writes a structured audit trail of all system actions.

    Each action is appended as a JSON line to a log file so the file
    can be streamed and processed incrementally.
    """

    def __init__(self, log_path: Optional[Path] = None) -> None:
        """Initialise the action logger.

        Args:
            log_path: Path to the JSONL log file.
        """
        self._path = log_path or DEFAULT_LOG_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._in_memory: List[Dict[str, Any]] = []

    def log(
        self,
        action_type: str,
        details: Dict[str, Any],
        status: str = "success",
        agent: Optional[str] = None,
    ) -> str:
        """Record a single action.

        Args:
            action_type: Category of action (e.g., ``"file.write"``).
            details: Structured details about the action.
            status: ``"success"`` or ``"error"``.
            agent: Name of the agent or module that triggered the action.

        Returns:
            The generated action ID.
        """
        record: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "agent": agent,
            "status": status,
            "details": details,
        }
        self._in_memory.append(record)
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            logger.warning("Could not write action log: %s", exc)
        return record["id"]

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent in-memory action records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of action dicts, most recent last.
        """
        return self._in_memory[-limit:]
