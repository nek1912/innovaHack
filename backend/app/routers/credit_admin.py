import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.auth import get_current_owner
from app.models.owner import Owner, Agent
from app.models.credit import CreditAccount, CreditTransaction
from app.services.risk import calculate_risk

router = APIRouter(prefix="/owner/credit", tags=["owner-credit"])


@router.post("/freeze/{agent_id}")
async def freeze_credit(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Freeze credit for an agent."""
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise HTTPException(status_code=404, detail="Credit account not found")

    if credit_account.status == "frozen":
        raise HTTPException(status_code=400, detail="Credit already frozen")

    credit_account.status = "frozen"

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one()
    agent.status = "frozen"

    transaction = CreditTransaction(
        id=uuid.uuid4(),
        credit_account_id=credit_account.id,
        payout_id=None,
        type="FREEZE",
        amount=0,
        balance_after=credit_account.available_credit,
        reason="Manual freeze by owner",
    )
    db.add(transaction)

    await db.commit()

    return {
        "id": str(credit_account.id),
        "status": "frozen",
        "agent_status": "frozen",
    }


@router.post("/unfreeze/{agent_id}")
async def unfreeze_credit(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Unfreeze credit for an agent."""
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise HTTPException(status_code=404, detail="Credit account not found")

    if credit_account.status != "frozen":
        raise HTTPException(status_code=400, detail="Credit is not frozen")

    credit_account.status = "active"

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one()
    agent.status = "active"

    transaction = CreditTransaction(
        id=uuid.uuid4(),
        credit_account_id=credit_account.id,
        payout_id=None,
        type="UNFREEZE",
        amount=0,
        balance_after=credit_account.available_credit,
        reason="Manual unfreeze by owner",
    )
    db.add(transaction)

    await db.commit()

    return {
        "id": str(credit_account.id),
        "status": "active",
        "agent_status": "active",
    }


@router.get("/dashboard")
async def credit_dashboard(
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get credit dashboard summary."""
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.owner_id == owner.id)
    )
    accounts = result.scalars().all()

    total_limit = sum(a.credit_limit for a in accounts)
    total_available = sum(a.available_credit for a in accounts)
    total_used = sum(a.used_credit for a in accounts)
    total_reserved = sum(a.reserved_credit for a in accounts)
    active_count = sum(1 for a in accounts if a.status == "active")
    frozen_count = sum(1 for a in accounts if a.status == "frozen")

    return {
        "total_accounts": len(accounts),
        "active_accounts": active_count,
        "frozen_accounts": frozen_count,
        "total_credit_limit": total_limit,
        "total_available": total_available,
        "total_used": total_used,
        "total_reserved": total_reserved,
    }


@router.get("/accounts")
async def list_credit_accounts(
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """List all credit accounts for this owner."""
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.owner_id == owner.id)
    )
    accounts = result.scalars().all()
    return {
        "accounts": [
            {
                "id": str(a.id),
                "agent_id": str(a.agent_id),
                "credit_limit": a.credit_limit,
                "available_credit": a.available_credit,
                "used_credit": a.used_credit,
                "reserved_credit": a.reserved_credit,
                "status": a.status,
            }
            for a in accounts
        ]
    }


@router.get("/risk")
async def risk_summary(
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get risk summary for all agents."""
    risk_data = await calculate_risk(owner.id, db)
    return risk_data
