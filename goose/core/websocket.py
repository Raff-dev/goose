"""WebSocket connection manager for real-time updates."""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket  # type: ignore[import-not-found]
from starlette.websockets import WebSocketDisconnect


class ConnectionManager:
    """Manages WebSocket connections for broadcasting updates.

    This is used to push real-time updates to all connected dashboard clients.
    """

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a message to all connected clients.

        Args:
            message: JSON-serializable dict to send.
        """
        text = json.dumps(message)
        disconnected = []

        for connection in self._connections:
            try:
                await connection.send_text(text)
            except WebSocketDisconnect:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        """Number of active connections."""
        return len(self._connections)


# Global instance for the application
manager = ConnectionManager()
