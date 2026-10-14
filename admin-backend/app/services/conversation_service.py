import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.conversation import AIMessage, Conversation

DEFAULT_CONVERSATION_TITLE = "Travel & Logistics Inquiry"


async def get_or_create_conversation(
    db: AsyncSession,
    conversation_id: Optional[str] = None,
    customer_email: Optional[str] = None,
    title: str = DEFAULT_CONVERSATION_TITLE,
) -> Conversation:
    """
    Fetch the caller's conversation, or start a new one.

    Ownership is enforced: previously any caller who supplied another
    customer's ``conversation_id`` was handed that conversation (and, when its
    email was still the placeholder, was even made its owner).
    """
    if conversation_id:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conv = result.scalar_one_or_none()
        if conv is not None:
            if not customer_email or (conv.customer_email or "").lower() != customer_email.lower():
                raise AppException(
                    message="That conversation does not belong to you.",
                    code="CONVERSATION_FORBIDDEN",
                    status_code=403,
                )
            return conv

    conv = Conversation(
        id=conversation_id or str(uuid.uuid4()),
        customer_email=customer_email or "",
        title=title,
        status="ACTIVE",
        is_demo=False,
    )
    db.add(conv)
    await db.flush()
    return conv


async def _next_sequence(db: AsyncSession, conversation_id: str) -> int:
    """Compute the next sequence number with a single aggregate query."""
    result = await db.execute(
        select(func.coalesce(func.max(AIMessage.sequence), 0)).where(
            AIMessage.conversation_id == conversation_id
        )
    )
    return int(result.scalar_one())


async def save_ai_chat_turn(
    db: AsyncSession,
    user_message: str,
    assistant_reply: str,
    conversation_id: Optional[str] = None,
    customer_email: Optional[str] = None,
    intent: Optional[str] = None,
    source: Optional[str] = None,
    mode: str = "live",
    metadata: Optional[Dict[str, Any]] = None,
) -> Conversation:
    conv = await get_or_create_conversation(db, conversation_id, customer_email)
    seq = await _next_sequence(db, conv.id)

    meta_str = json.dumps(metadata) if metadata else None

    db.add(
        AIMessage(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            sequence=seq + 1,
            role="user",
            content=user_message,
            intent=intent,
            mode=mode,
            source=source,
            metadata_json=meta_str,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.add(
        AIMessage(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            sequence=seq + 2,
            role="assistant",
            content=assistant_reply,
            intent=intent,
            mode=mode,
            source=source,
            metadata_json=meta_str,
            created_at=datetime.now(timezone.utc),
        )
    )

    if seq == 0:
        conv.title = user_message[:40] + ("..." if len(user_message) > 40 else "")

    conv.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return conv


async def _conversation_summaries(
    db: AsyncSession,
    conversations: List[Conversation],
) -> List[Dict[str, Any]]:
    """
    Build list rows with ONE aggregate query instead of one query per
    conversation (which also loaded every message body just to count them).
    """
    if not conversations:
        return []

    ids = [c.id for c in conversations]

    counts_res = await db.execute(
        select(AIMessage.conversation_id, func.count(AIMessage.id))
        .where(AIMessage.conversation_id.in_(ids))
        .group_by(AIMessage.conversation_id)
    )
    counts = {row[0]: int(row[1]) for row in counts_res.all()}

    # Newest message body per conversation, fetched in one pass.
    last_res = await db.execute(
        select(AIMessage.conversation_id, AIMessage.content)
        .where(AIMessage.conversation_id.in_(ids))
        .order_by(AIMessage.conversation_id, AIMessage.sequence.asc())
    )
    last_message: Dict[str, str] = {}
    for conversation_id, content in last_res.all():
        last_message[conversation_id] = content

    return [
        {
            "id": c.id,
            "title": c.title,
            "customer_email": c.customer_email,
            "status": c.status,
            "message_count": counts.get(c.id, 0),
            "last_message": last_message.get(c.id, ""),
            "is_demo": c.is_demo,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in conversations
    ]


async def get_all_conversations(
    db: AsyncSession,
    limit: Optional[int] = None,
    offset: int = 0,
    include_demo: bool = True,
) -> List[Dict[str, Any]]:
    stmt = select(Conversation)
    if not include_demo:
        stmt = stmt.where(Conversation.is_demo.is_(False))
    stmt = stmt.order_by(desc(Conversation.updated_at)).offset(max(offset, 0))
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return await _conversation_summaries(db, list(result.scalars().all()))


async def get_customer_conversations(
    db: AsyncSession,
    customer_email: str,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    stmt = (
        select(Conversation)
        .where(func.lower(Conversation.customer_email) == customer_email.lower())
        .order_by(desc(Conversation.updated_at))
        .offset(max(offset, 0))
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return await _conversation_summaries(db, list(result.scalars().all()))


async def get_conversation_detail(
    db: AsyncSession,
    conversation_id: str,
    customer_email: Optional[str] = None,
) -> Dict[str, Any]:
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise AppException(
            message=f"Conversation '{conversation_id}' not found.",
            code="CONVERSATION_NOT_FOUND",
            status_code=404,
        )

    # A customer may only read their own transcript (admins pass no email).
    if customer_email and (conv.customer_email or "").lower() != customer_email.lower():
        raise AppException(
            message="That conversation does not belong to you.",
            code="CONVERSATION_FORBIDDEN",
            status_code=403,
        )

    m_res = await db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == conv.id)
        .order_by(AIMessage.sequence.asc())
    )
    messages = list(m_res.scalars().all())

    return {
        "id": conv.id,
        "title": conv.title,
        "customer_email": conv.customer_email,
        "status": conv.status,
        "is_demo": conv.is_demo,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "intent": m.intent,
                "mode": m.mode,
                "source": m.source,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }
