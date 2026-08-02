import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner import Agent, Payee
from app.models.credit import CreditAccount, CreditTransaction


async def list_allowed_payees(agent_id: uuid.UUID, session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Payee).where(Payee.agent_id == agent_id, Payee.active == True)
    )
    payees = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "label": p.label,
            "vpa": p.vpa,
            "bank_account": p.bank_account_number[:4] + "****" if p.bank_account_number else None,
        }
        for p in payees
    ]


async def check_credit(agent_id: uuid.UUID, session: AsyncSession) -> dict:
    result = await session.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        return {"has_credit": False, "message": "No credit account"}
    return {
        "has_credit": True,
        "available": account.available_credit,
        "reserved": account.reserved_credit,
        "used": account.used_credit,
        "limit": account.credit_limit,
        "status": account.status,
    }


async def get_agent_status(agent_id: uuid.UUID, session: AsyncSession) -> dict:
    result = await session.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return {"error": "Agent not found"}
    return {
        "id": str(agent.id),
        "name": agent.name,
        "status": agent.status,
        "per_tx_cap": agent.per_tx_cap_paise,
        "daily_cap": agent.daily_cap_paise,
        "approval_threshold": agent.approval_threshold_paise,
    }


async def list_recent_transactions(agent_id: uuid.UUID, session: AsyncSession, limit: int = 10) -> list[dict]:
    result = await session.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        return []

    result = await session.execute(
        select(CreditTransaction)
        .where(CreditTransaction.credit_account_id == account.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()
    return [
        {
            "id": str(tx.id),
            "type": tx.type,
            "amount": tx.amount,
            "balance_after": tx.balance_after,
            "reason": tx.reason,
            "created_at": tx.created_at.isoformat(),
        }
        for tx in transactions
    ]
