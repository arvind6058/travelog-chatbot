import re
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import logger
from app.core.security import ADMIN_ROLES, TOKEN_TYPE_ADMIN, TOKEN_TYPE_CUSTOMER, decode_access_token
from app.realtime.manager import manager

router = APIRouter(prefix="/realtime", tags=["Realtime Telemetry"])

TRACKING_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
DRIVER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# Channels any anonymous client may subscribe to: per-shipment tracking only.
PUBLIC_CHANNEL_PREFIXES = ("tracking:",)


def _decode(token: Optional[str], token_type: str) -> Optional[dict]:
    if not token:
        return None
    try:
        payload = decode_access_token(token, token_type=token_type)
    except Exception:
        return None
    return payload


def authorise_socket(
    token: Optional[str],
    channel: str,
    *,
    require_admin: bool = False,
) -> bool:
    """
    Decide whether a socket may join a channel.

    Rules:
      * admin channels require a valid ADMIN token with an administrative role;
      * public tracking channels (``tracking:<id>``) are open;
      * everything else (fleet/driver telemetry) requires an admin token.

    Previously ``/ws/admin/all`` and the generic ``/ws/{channel}/{item_id}``
    route performed no check at all, so anyone could stream the whole fleet feed.
    """
    admin_payload = _decode(token, TOKEN_TYPE_ADMIN)
    is_admin = bool(admin_payload) and str(admin_payload.get("role") or "").upper() in ADMIN_ROLES

    if require_admin or channel == "admin:all":
        return is_admin

    if channel.startswith(PUBLIC_CHANNEL_PREFIXES):
        return True

    # Fleet telemetry (drivers:*) and any other channel: admins, or the
    # customer holding a valid session (read-only tracking consumers).
    if is_admin:
        return True
    return _decode(token, TOKEN_TYPE_CUSTOMER) is not None


async def _reject(websocket: WebSocket, reason: str = "Unauthorized") -> None:
    await websocket.close(code=4001, reason=reason)


async def _run_channel(websocket: WebSocket, channel: str) -> None:
    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pragma: no cover - transport level
        logger.debug(f"WebSocket error on '{channel}': {exc}")
    finally:
        # `finally`, not `except`: a cancelled task used to leave the socket in
        # active_connections forever, growing the set unboundedly.
        manager.disconnect(websocket, channel)


@router.websocket("/ws/tracking/{tracking_id}")
async def websocket_shipment_tracking(
    websocket: WebSocket,
    tracking_id: str,
    token: Optional[str] = Query(None),
):
    if not TRACKING_ID_RE.match(tracking_id or ""):
        await _reject(websocket, "Invalid tracking id")
        return
    channel = f"tracking:{tracking_id}"
    if not authorise_socket(token, channel):
        await _reject(websocket)
        return
    await _run_channel(websocket, channel)


@router.websocket("/ws/drivers/{driver_id}")
async def websocket_driver_tracking(
    websocket: WebSocket,
    driver_id: str,
    token: Optional[str] = Query(None),
):
    if not DRIVER_ID_RE.match(driver_id or ""):
        await _reject(websocket, "Invalid driver id")
        return
    channel = f"drivers:{driver_id}"
    if not authorise_socket(token, channel):
        await _reject(websocket)
        return
    await _run_channel(websocket, channel)


@router.websocket("/ws/admin/all")
async def websocket_admin_all(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    channel = "admin:all"
    if not authorise_socket(token, channel, require_admin=True):
        logger.warning("Rejected an unauthenticated subscription to the admin realtime channel.")
        await _reject(websocket, "Admin token required")
        return
    await _run_channel(websocket, channel)


@router.websocket("/ws/{channel}/{item_id}")
async def websocket_generic_channel(
    websocket: WebSocket,
    channel: str,
    item_id: str,
    token: Optional[str] = Query(None),
):
    # The client no longer picks an unvalidated channel name.
    if not re.match(r"^[A-Za-z]{1,24}$", channel or "") or not re.match(r"^[A-Za-z0-9_-]{1,64}$", item_id or ""):
        await _reject(websocket, "Invalid channel")
        return
    channel_key = f"{channel}:{item_id}"
    if not authorise_socket(token, channel_key):
        await _reject(websocket)
        return
    await _run_channel(websocket, channel_key)
