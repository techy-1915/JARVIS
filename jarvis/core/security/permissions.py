"""Permission manager – controls what actions are allowed."""

import logging
from enum import Enum
from typing import Set

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Available permission flags."""

    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_DELETE = "file.delete"
    BROWSER_USE = "browser.use"
    SYSTEM_EXEC = "system.exec"
    NETWORK_ACCESS = "network.access"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    AGENT_SPAWN = "agent.spawn"
    ADMIN = "admin"


DEFAULT_PERMISSIONS: Set[Permission] = {
    Permission.FILE_READ,
    Permission.NETWORK_ACCESS,
    Permission.MEMORY_READ,
    Permission.MEMORY_WRITE,
}


class PermissionManager:
    """Manages runtime permissions for JARVIS operations."""

    def __init__(self) -> None:
        self._granted: Set[Permission] = set(DEFAULT_PERMISSIONS)

    def grant(self, permission: Permission) -> None:
        """Grant a permission."""
        self._granted.add(permission)
        logger.info("Granted permission: %s", permission)

    def revoke(self, permission: Permission) -> None:
        """Revoke a permission."""
        self._granted.discard(permission)
        logger.info("Revoked permission: %s", permission)

    def has(self, permission: Permission) -> bool:
        """Check if a permission is currently granted."""
        return permission in self._granted or Permission.ADMIN in self._granted

    def require(self, permission: Permission) -> None:
        """Assert a permission is held, raising if not.

        Raises:
            PermissionError: If the permission is not granted.
        """
        if not self.has(permission):
            raise PermissionError(f"Permission denied: {permission}")

    def list_granted(self) -> list:
        """Return list of currently granted permission names."""
        return [p.value for p in self._granted]
