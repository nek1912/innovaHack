import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import IST, ist_today_bounds
from app.models.owner import Agent, Payout, Payee


async def get_credit_input(agent_id: uuid.UUID, session: AsyncSession) -> dict:
    """Build credit portion of OPA input."""
    from app.models.credit import CreditAccount

    result = await session.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    credit_account = result.scalar_one_or_none()

    if credit_account is None:
        return {
            "has_credit": False,
            "available": 0,
            "reserved": 0,
            "used": 0,
            "limit": 0,
            "status": "none",
        }

    return {
        "has_credit": True,
        "available": credit_account.available_credit,
        "reserved": credit_account.reserved_credit,
        "used": credit_account.used_credit,
        "limit": credit_account.credit_limit,
        "status": credit_account.status,
    }


async def build_policy_input(
    db: AsyncSession, agent_id: uuid.UUID, payee_id: uuid.UUID, amount_paise: int
) -> dict:
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise ValueError("agent_not_found")

    payee = await db.get(Payee, payee_id)
    if not payee:
        raise ValueError("payee_not_found")

    day_start_utc, day_end_utc = ist_today_bounds()

    result = await db.execute(
        select(func.coalesce(func.sum(Payout.amount_paise), 0)).where(
            Payout.agent_id == agent_id,
            Payout.razorpay_status.in_(["queued", "processing", "processed"]),
            Payout.created_at >= day_start_utc,
            Payout.created_at < day_end_utc,
        )
    )
    daily_spent = result.scalar() or 0
    daily_spent = int(daily_spent)

    return {
        "agent_id": str(agent_id),
        "payee_id": str(payee_id),
        "amount_paise": int(amount_paise),
        "per_tx_cap_paise": int(agent.per_tx_cap_paise),
        "daily_cap_paise": int(agent.daily_cap_paise),
        "daily_spent_paise": daily_spent,
        "approval_threshold_paise": int(agent.approval_threshold_paise),
        "agent_status": agent.status,
        "payee_active": payee.active,
        "credit": await get_credit_input(agent_id, db),
    }
