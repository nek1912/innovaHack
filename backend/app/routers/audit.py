import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_owner
from app.db import get_db
from app.deps import raise_error
from app.models.owner import AuditLog, Agent, Owner
from app.schemas.payout import AuditEntry, AuditList

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditList)
async def get_audit_log(
    agent_id: uuid.UUID | None = Query(None),
    event_type: str | None = Query(None),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    # Scoped to this owner's agents OR entries where this owner is the actor
    owned_agent_ids = select(Agent.id).where(Agent.owner_id == owner.id)
    scope = (
        (AuditLog.agent_id.in_(owned_agent_ids))
        | (AuditLog.owner_id == owner.id)
    )
    query = query.where(scope)
    count_query = count_query.where(scope)

    if agent_id:
        # only allow filtering to an agent this owner actually owns
        result = await db.execute(
            select(Agent.id).where(Agent.id == agent_id, Agent.owner_id == owner.id)
        )
        if result.scalar_one_or_none() is None:
            raise_error(404, "agent_not_found", "Agent not found")
        query = query.where(AuditLog.agent_id == agent_id)
        count_query = count_query.where(AuditLog.agent_id == agent_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
        count_query = count_query.where(AuditLog.event_type == event_type)
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
        count_query = count_query.where(AuditLog.created_at >= from_date)
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)
        count_query = count_query.where(AuditLog.created_at <= to_date)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    )
    entries = result.scalars().all()

    return AuditList(
        entries=[
            AuditEntry(
                id=e.id,
                request_id=e.request_id,
                agent_id=e.agent_id,
                owner_id=e.owner_id,
                event_type=e.event_type,
                detail=e.detail,
                created_at=e.created_at.isoformat(),
            )
            for e in entries
        ],
        total=total,
    )
