from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestrator import orchestrator
from app.core.dependencies import get_current_customer, get_optional_customer
from app.core.logging import logger
from app.db.session import get_db_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.audit_service import create_audit_log
from app.services.conversation_service import (
    get_conversation_detail,
    get_customer_conversations,
    save_ai_chat_turn,
)

router = APIRouter(tags=["AI Chat"])

# Chat actions worth recording in the audit trail.
AUDIT_ACTION_MAP = {
    "SHIPMENT_TRACKING": ("shipment_tracked", "tracked shipment"),
    "SHIPMENT_REGISTER": ("shipment_created", "registered shipment"),
    "TRAVEL_ITINERARY": ("trip_planned", "requested trip itinerary for"),
    "BUDGET_CALCULATION": ("trip_planned", "calculated travel budget for"),
}


def extract_customer_info(request: Request) -> Dict[str, Optional[str]]:
    """
    Best-effort identity from the session cookie or bearer token.

    Anonymous callers now resolve to ``None`` rather than a shared
    ``customer@travelogix.internal`` identity, which previously merged every
    anonymous visitor into a single (claimable) account.
    """
    from app.core.security import TOKEN_TYPE_CUSTOMER, bearer_or_cookie_token, decode_access_token
    from app.core.dependencies import CUSTOMER_COOKIE_NAME

    token = bearer_or_cookie_token(request, CUSTOMER_COOKIE_NAME)
    if not token:
        return {"user_id": None, "email": None, "name": None}

    try:
        payload = decode_access_token(token, token_type=TOKEN_TYPE_CUSTOMER)
    except Exception:
        return {"user_id": None, "email": None, "name": None}

    if str(payload.get("role") or "").upper() != "CUSTOMER":
        return {"user_id": None, "email": None, "name": None}

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
    }


@router.post("", response_model=ChatResponse, summary="Send message to Travelogix AI Assistant")
async def chat_with_ai(
    request_data: ChatRequest,
    raw_request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    customer_info = extract_customer_info(raw_request)
    customer_email = customer_info["email"]
    customer_name = customer_info["name"]
    user_id = customer_info["user_id"]
    is_authenticated = bool(customer_email)

    result = await orchestrator.process_message(
        db=db,
        message=request_data.message,
        conversation_id=request_data.conversation_id if is_authenticated else None,
        user_id=user_id,
        customer_email=customer_email,
        customer_name=customer_name,
    )

    conv_id = request_data.conversation_id if is_authenticated else None
    persisted = False

    # Anonymous turns are answered but never stored: there is no identity to
    # own them, and persisting them under a fixed shared account made every
    # visitor's transcript readable as one user's history.
    if is_authenticated:
        try:
            conv = await save_ai_chat_turn(
                db=db,
                user_message=request_data.message,
                assistant_reply=result["reply"],
                conversation_id=conv_id,
                customer_email=customer_email,
                intent=result.get("intent"),
                source=(result.get("provenance") or {}).get("source"),
                mode=(result.get("provenance") or {}).get("mode", "static"),
                metadata=result.get("data"),
            )
            if conv:
                conv_id = conv.id

            intent = result.get("intent")
            if intent in AUDIT_ACTION_MAP:
                action_code, phrase = AUDIT_ACTION_MAP[intent]
                detail = result.get("tracking_id") or result.get("destination") or ""
                await create_audit_log(
                    db=db,
                    actor=customer_email,
                    action=action_code,
                    entity_type="CHAT",
                    entity_id=conv_id or "chat",
                    description=f"Customer {phrase} {detail}".strip(),
                    metadata={
                        "intent": intent,
                        "tracking_id": result.get("tracking_id"),
                        "destination": result.get("destination"),
                    },
                    is_demo=False,
                )

            # One transaction for the turn and its audit record.
            await db.commit()
            persisted = True
        except Exception as exc:
            await db.rollback()
            logger.exception(f"Could not persist the chat turn: {exc}")

    prov = result.get("provenance") or {}
    source_val = prov.get("source") or "travelogix_assistant"
    mode_val = prov.get("mode") or "static"
    is_mock_val = bool(prov.get("is_mock", False))
    fetched_at_val = prov.get("fetched_at")

    return ChatResponse(
        success=True,
        reply=result["reply"],
        message=result["reply"],
        intent=result["intent"],
        destination=result.get("destination"),
        duration_days=result.get("duration_days"),
        tracking_id=result.get("tracking_id"),
        provenance=prov,
        source=source_val,
        mode=mode_val,
        is_mock=is_mock_val,
        fetched_at=fetched_at_val,
        data=result.get("data"),
        conversation_id=conv_id,
        persisted=persisted,
    )


@router.get("/conversations", summary="List the signed-in customer's conversations")
async def list_my_conversations(
    limit: int = 50,
    offset: int = 0,
    current_customer: Dict[str, Any] = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db_session),
):
    """Customer-scoped replacement for the admin conversations endpoint."""
    conversations = await get_customer_conversations(
        db,
        customer_email=str(current_customer.get("email")),
        limit=max(1, min(limit, 200)),
        offset=max(offset, 0),
    )
    return {"success": True, "conversations": conversations}


@router.get("/conversations/{conversation_id}", summary="Get one of the customer's own conversations")
async def get_my_conversation(
    conversation_id: str,
    current_customer: Dict[str, Any] = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db_session),
):
    detail = await get_conversation_detail(
        db,
        conversation_id,
        customer_email=str(current_customer.get("email")),
    )
    return {"success": True, "conversation": detail}
