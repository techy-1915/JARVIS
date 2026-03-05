"""Long-term memory – persistent user preferences and facts."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = Path("jarvis/data/long_term_memory.json")


class LongTermMemory:
    """Stores user preferences and persistent facts on disk.

    Uses a simple JSON file as the backing store.  For production use
    this should be swapped for a proper database.
    """

    def __init__(self, store_path: Optional[Path] = None) -> None:
        """Initialise and load existing data from disk.

        Args:
            store_path: Path to the JSON persistence file.
        """
        self._path: Path = store_path or DEFAULT_STORE_PATH
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load data from the JSON file, or return empty dict if not found."""
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load long-term memory: %s", exc)
        return {}

    def _save(self) -> None:
        """Persist current data to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, default=str)

    def set(self, key: str, value: Any) -> None:
        """Store or update a key-value pair.

        Args:
            key: Unique identifier for the memory item.
            value: Value to store.
        """
        self._data[key] = {
            "value": value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored value.

        Args:
            key: The memory key.
            default: Value to return if key is not found.

        Returns:
            The stored value, or ``default``.
        """
        entry = self._data.get(key)
        if entry is None:
            return default
        return entry.get("value", default)

    def delete(self, key: str) -> bool:
        """Remove a key from memory.

        Args:
            key: The key to remove.

        Returns:
            True if the key existed and was removed.
        """
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False

    def list_keys(self) -> List[str]:
        """Return all stored keys."""
        return list(self._data.keys())

    def clear(self) -> None:
        """Erase all long-term memory."""
        self._data = {}
        self._save()
