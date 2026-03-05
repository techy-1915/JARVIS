"""File manager tool – safe file operations."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .tool_base import ToolBase

logger = logging.getLogger(__name__)


class FileManagerTool(ToolBase):
    """Performs safe file system operations within an allowed base directory."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        super().__init__(name="file_manager", description="File system operations")
        self._base_dir = Path(base_dir or os.getcwd()).resolve()

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "name": "file_manager",
            "parameters": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list", "delete", "exists"],
                },
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["operation", "path"],
        }

    def _safe_path(self, path: str) -> Optional[Path]:
        """Resolve and validate that path stays within the base directory."""
        resolved = (self._base_dir / path).resolve()
        if not str(resolved).startswith(str(self._base_dir)):
            logger.warning("Path traversal attempt blocked: %s", path)
            return None
        return resolved

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Perform the requested file operation.

        Args:
            operation: One of ``read``, ``write``, ``list``, ``delete``, ``exists``.
            path: File or directory path (relative to base dir).
            content: Content to write (required for ``write``).

        Returns:
            Standardised result dict.
        """
        operation: str = kwargs.get("operation", "")
        raw_path: str = kwargs.get("path", "")

        safe = self._safe_path(raw_path)
        if safe is None:
            return self._error("Path is outside the allowed directory")

        try:
            if operation == "read":
                return self._success({"content": safe.read_text(encoding="utf-8")})
            elif operation == "write":
                content: str = kwargs.get("content", "")
                safe.parent.mkdir(parents=True, exist_ok=True)
                safe.write_text(content, encoding="utf-8")
                return self._success({"written": str(safe)})
            elif operation == "list":
                if safe.is_dir():
                    entries = [e.name for e in safe.iterdir()]
                    return self._success({"entries": entries})
                return self._error("Path is not a directory")
            elif operation == "delete":
                if safe.is_file():
                    safe.unlink()
                    return self._success({"deleted": str(safe)})
                return self._error("Path is not a file")
            elif operation == "exists":
                return self._success({"exists": safe.exists()})
            else:
                return self._error(f"Unknown operation: {operation}")
        except OSError as exc:
            return self._error(f"File operation failed: {exc}")
