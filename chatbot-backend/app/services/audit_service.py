import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def create_audit_log(
    db: AsyncSession,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None,
    is_demo: bool = False,
) -> AuditLog:
    """
    Stage an audit record in the caller's transaction.

    Only flushes: the caller decides the commit boundary, so an audit row can
    never be persisted for a mutation that was later rolled back.
    """
    log_entry = AuditLog(
        id=str(uuid.uuid4()),
        actor=actor or "system",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        metadata_json=json.dumps(metadata) if metadata else None,
        is_demo=is_demo,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log_entry)
    await db.flush()
    return log_entry


async def get_audit_logs(
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    include_demo: bool = True,
) -> List[AuditLog]:
    stmt = select(AuditLog)
    if not include_demo:
        stmt = stmt.where(AuditLog.is_demo.is_(False))
    stmt = (
        stmt.order_by(desc(AuditLog.timestamp))
        .offset(max(offset, 0))
        .limit(max(1, min(limit, 500)))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_audit_logs(db: AsyncSession, include_demo: bool = True) -> int:
    stmt = select(func.count(AuditLog.id))
    if not include_demo:
        stmt = stmt.where(AuditLog.is_demo.is_(False))
    return int((await db.execute(stmt)).scalar_one())
