"""API client – executes HTTP API requests safely."""

import logging
from typing import Any, Dict, Optional

import httpx

from ..security.permissions import Permission, PermissionManager
from .action_logger import ActionLogger

logger = logging.getLogger(__name__)


class APIClient:
    """Makes HTTP API calls with permission enforcement and logging."""

    def __init__(
        self,
        permissions: Optional[PermissionManager] = None,
        action_logger: Optional[ActionLogger] = None,
        timeout: float = 30.0,
    ) -> None:
        self._perms = permissions or PermissionManager()
        self._log = action_logger or ActionLogger()
        self._timeout = timeout

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform an HTTP GET request."""
        self._perms.require(Permission.NETWORK_ACCESS)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                self._log.log("api.get", {"url": url, "status": resp.status_code})
                return {"status": "success", "data": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text}
        except httpx.HTTPStatusError as exc:
            return {"status": "error", "error": str(exc)}
        except httpx.RequestError as exc:
            return {"status": "error", "error": f"Request failed: {exc}"}

    async def post(self, url: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform an HTTP POST request."""
        self._perms.require(Permission.NETWORK_ACCESS)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=json)
                resp.raise_for_status()
                self._log.log("api.post", {"url": url, "status": resp.status_code})
                return {"status": "success", "data": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text}
        except httpx.HTTPStatusError as exc:
            return {"status": "error", "error": str(exc)}
        except httpx.RequestError as exc:
            return {"status": "error", "error": f"Request failed: {exc}"}
