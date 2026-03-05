"""Browser controller – high-level browser automation coordinator."""

import logging
from typing import Any, Dict, Optional

from ..security.permissions import Permission, PermissionManager
from ..tools.browser_tool import BrowserTool
from .action_logger import ActionLogger

logger = logging.getLogger(__name__)


class BrowserController:
    """Coordinates browser automation through the BrowserTool."""

    def __init__(
        self,
        permissions: Optional[PermissionManager] = None,
        action_logger: Optional[ActionLogger] = None,
    ) -> None:
        self._perms = permissions or PermissionManager()
        self._log = action_logger or ActionLogger()
        self._browser = BrowserTool()

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate the browser to a URL."""
        self._perms.require(Permission.BROWSER_USE)
        result = await self._browser.execute(action="open", url=url)
        self._log.log("browser.navigate", {"url": url})
        return result

    async def screenshot(self) -> Dict[str, Any]:
        """Take a screenshot of the current browser state."""
        self._perms.require(Permission.BROWSER_USE)
        return await self._browser.execute(action="screenshot")

    async def close(self) -> Dict[str, Any]:
        """Close the browser."""
        return await self._browser.execute(action="close")
