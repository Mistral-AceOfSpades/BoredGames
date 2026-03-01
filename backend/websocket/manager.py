"""WebSocket connection manager for real-time game moderation events."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections grouped by session ID."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info("WebSocket connected to session %s", session_id)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id] = [
                ws for ws in self.active_connections[session_id] if ws != websocket
            ]
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info("WebSocket disconnected from session %s", session_id)

    async def send_to_session(self, session_id: str, message: dict[str, Any]):
        """Broadcast a message to all connections in a session."""
        if session_id not in self.active_connections:
            return
        payload = json.dumps(message)
        disconnected = []
        for ws in self.active_connections[session_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)
        # Clean up broken connections
        for ws in disconnected:
            self.disconnect(ws, session_id)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]):
        """Send a message to a specific client."""
        await websocket.send_text(json.dumps(message))


# Singleton instance
manager = ConnectionManager()
