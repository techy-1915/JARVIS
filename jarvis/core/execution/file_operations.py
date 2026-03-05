"""File operations execution module."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..security.permissions import Permission, PermissionManager
from ..security.validator import CommandValidator
from .action_logger import ActionLogger

logger = logging.getLogger(__name__)


class FileOperations:
    """Performs file system operations with permission enforcement."""

    def __init__(
        self,
        permissions: Optional[PermissionManager] = None,
        action_logger: Optional[ActionLogger] = None,
        base_dir: Optional[str] = None,
    ) -> None:
        self._perms = permissions or PermissionManager()
        self._log = action_logger or ActionLogger()
        self._validator = CommandValidator()
        self._base = Path(base_dir or ".").resolve()

    def _resolve(self, path: str) -> Path:
        """Resolve a path relative to the base directory."""
        resolved = (self._base / path).resolve()
        if not str(resolved).startswith(str(self._base)):
            raise ValueError(f"Path outside base directory: {path}")
        return resolved

    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file's contents."""
        self._perms.require(Permission.FILE_READ)
        try:
            resolved = self._resolve(path)
            content = resolved.read_text(encoding="utf-8")
            self._log.log("file.read", {"path": str(resolved)})
            return {"status": "success", "content": content}
        except (ValueError, OSError) as exc:
            return {"status": "error", "error": str(exc)}

    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file."""
        self._perms.require(Permission.FILE_WRITE)
        try:
            resolved = self._resolve(path)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            self._log.log("file.write", {"path": str(resolved), "bytes": len(content)})
            return {"status": "success", "path": str(resolved)}
        except (ValueError, OSError) as exc:
            return {"status": "error", "error": str(exc)}

    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file after permission check."""
        self._perms.require(Permission.FILE_DELETE)
        try:
            resolved = self._resolve(path)
            if resolved.is_file():
                resolved.unlink()
                self._log.log("file.delete", {"path": str(resolved)})
                return {"status": "success", "deleted": str(resolved)}
            return {"status": "error", "error": "Not a file"}
        except (ValueError, OSError) as exc:
            return {"status": "error", "error": str(exc)}
