"""WebSocket manager for real-time JARVIS updates."""

import logging
from typing import Any, Dict, List, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts.

    Maintains a set of connected clients and provides methods for
    sending messages to individual clients or broadcasting to all.
    """

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("WebSocket connected (%d total)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket."""
        self._connections.discard(websocket)
        logger.info("WebSocket disconnected (%d remaining)", len(self._connections))

    async def send(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """Send a JSON message to a specific client."""
        try:
            await websocket.send_json(data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send WebSocket message: %s", exc)
            self.disconnect(websocket)

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """Broadcast a JSON message to all connected clients."""
        dead: List[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_json(data)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def connection_count(self) -> int:
        """Number of active WebSocket connections."""
        return len(self._connections)


# Global singleton used by routers
ws_manager = ConnectionManager()
