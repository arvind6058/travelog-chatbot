import asyncio
import json
from typing import Any, Dict, Set

from fastapi import WebSocket

from app.core.logging import logger
from app.core.redis import get_redis


class ConnectionManager:
    def __init__(self) -> None:
        # Active connections mapped by channel (e.g. "tracking:TLX-2026-100001")
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        self.active_connections.setdefault(channel, set()).add(websocket)
        logger.info(f"WebSocket client connected to channel '{channel}'")

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        logger.info(f"WebSocket client disconnected from channel '{channel}'")

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]) -> None:
        connections = list(self.active_connections.get(channel, ()))

        # One slow subscriber must not stall the others (or the HTTP request
        # that triggered the broadcast).
        if connections:
            results = await asyncio.gather(
                *(asyncio.wait_for(ws.send_json(message), timeout=5) for ws in connections),
                return_exceptions=True,
            )
            for websocket, outcome in zip(connections, results):
                if isinstance(outcome, Exception):
                    logger.warning(f"Error sending message to client: {outcome}")
                    self.disconnect(websocket, channel)

        # Publish for other workers. get_redis() is synchronous; awaiting it
        # raised TypeError on every call, which the old code swallowed — the
        # Redis fan-out never worked.
        try:
            redis = get_redis()
            if redis is not None:
                await redis.publish(f"events:{channel}", json.dumps(message, default=str))
        except Exception as exc:
            logger.debug(f"Redis publish skipped: {exc}")


manager = ConnectionManager()
