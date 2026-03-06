"""Application launcher – opens desktop applications safely."""

import asyncio
import logging
import shutil
from typing import Any, Dict, List, Optional

from ..security.permissions import Permission, PermissionManager
from .action_logger import ActionLogger

logger = logging.getLogger(__name__)


class AppLauncher:
    """Launches operating-system applications with permission checks."""

    def __init__(
        self,
        permissions: Optional[PermissionManager] = None,
        action_logger: Optional[ActionLogger] = None,
    ) -> None:
        self._perms = permissions or PermissionManager()
        self._log = action_logger or ActionLogger()

    async def launch(self, app_name: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Launch an application by name.

        Args:
            app_name: The application executable name (e.g., ``"firefox"``).
            args: Optional additional arguments to pass to the app.

        Returns:
            Dict with ``status`` and ``pid`` (if launched successfully).
        """
        self._perms.require(Permission.SYSTEM_EXEC)

        executable = shutil.which(app_name)
        if not executable:
            self._log.log("app.launch", {"app": app_name}, status="error")
            return {"status": "error", "error": f"Application not found: {app_name}"}

        cmd = [executable] + (args or [])
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            self._log.log("app.launch", {"app": app_name, "pid": proc.pid})
            return {"status": "success", "app": app_name, "pid": proc.pid}
        except OSError as exc:
            self._log.log("app.launch", {"app": app_name, "error": str(exc)}, status="error")
            return {"status": "error", "error": str(exc)}
