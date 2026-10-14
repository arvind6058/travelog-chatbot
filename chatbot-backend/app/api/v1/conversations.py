from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_customer, get_db_session
from app.services.conversation_service import (
    get_conversation_detail,
    get_customer_conversations,
    get_or_create_conversation,
)
from app.api.v1.chat import extract_customer_info

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field("Travel & Logistics Inquiry", description="Title for the conversation")


@router.post("", summary="Create a new conversation")
async def create_conversation_endpoint(
    payload: Optional[CreateConversationRequest] = None,
    raw_request: Request = None,
    db: AsyncSession = Depends(get_db_session),
):
    customer_info = extract_customer_info(raw_request)
    customer_email = customer_info.get("email")
    title = payload.title if payload and payload.title else "Travel & Logistics Inquiry"

    conv = await get_or_create_conversation(db, customer_email=customer_email, title=title)
    await db.commit()

    return {
        "success": True,
        "conversation_id": conv.id,
        "conversation": {
            "id": conv.id,
            "title": conv.title,
            "customer_email": conv.customer_email,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
        },
    }


@router.get("", summary="List customer's conversations")
async def list_conversations_endpoint(
    limit: int = 50,
    offset: int = 0,
    current_customer: Dict[str, Any] = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db_session),
):
    conversations = await get_customer_conversations(
        db,
        customer_email=str(current_customer.get("email")),
        limit=max(1, min(limit, 200)),
        offset=max(offset, 0),
    )
    return {"success": True, "conversations": conversations}


@router.get("/{conversation_id}", summary="Get conversation detail")
async def get_conversation_endpoint(
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


@router.get("/{conversation_id}/messages", summary="Get messages in a conversation")
async def get_conversation_messages_endpoint(
    conversation_id: str,
    current_customer: Dict[str, Any] = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db_session),
):
    detail = await get_conversation_detail(
        db,
        conversation_id,
        customer_email=str(current_customer.get("email")),
    )
    return {
        "success": True,
        "conversation_id": conversation_id,
        "messages": detail.get("messages", []),
    }
