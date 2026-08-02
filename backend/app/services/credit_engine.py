import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import log_audit
from app.models.credit import CreditAccount, CreditTransaction
from app.models.owner import Agent
from app.services.underwriting import calculate_score


async def issue_credit(
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    session: AsyncSession,
) -> CreditAccount:
    """Issue credit to an agent after underwriting."""

    result = await session.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("Credit account already exists for this agent")

    result = await session.execute(
        select(Agent).where(Agent.id == agent_id, Agent.owner_id == owner_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise ValueError("Agent not found or does not belong to owner")

    score, reason, approved_limit = await calculate_score(owner_id, agent_id, session)

    credit_account = CreditAccount(
        id=uuid.uuid4(),
        owner_id=owner_id,
        agent_id=agent_id,
        credit_limit=approved_limit,
        available_credit=approved_limit,
        used_credit=0,
        reserved_credit=0,
        currency="INR",
        status="active",
    )
    session.add(credit_account)
    await session.flush()

    transaction = CreditTransaction(
        id=uuid.uuid4(),
        credit_account_id=credit_account.id,
        payout_id=None,
        type="ISSUE",
        amount=approved_limit,
        balance_after=approved_limit,
        reason=f"Credit issued: score={score}, {reason}",
    )
    session.add(transaction)

    await log_audit(
        session,
        request_id=uuid.uuid4(),
        event_type="credit_issued",
        detail={
            "credit_account_id": str(credit_account.id),
            "agent_id": str(agent_id),
            "credit_limit": approved_limit,
            "score": score,
            "reason": reason,
        },
        agent_id=agent_id,
    )

    return credit_account


async def reserve_credit(
    credit_account_id: uuid.UUID,
    amount: int,
    session: AsyncSession,
) -> CreditTransaction:
    """Reserve credit before payout execution. Uses SELECT FOR UPDATE."""

    result = await session.execute(
        select(CreditAccount)
        .where(CreditAccount.id == credit_account_id)
        .with_for_update()
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise ValueError("Credit account not found")

    if credit_account.status != "active":
        raise ValueError(f"Credit account is {credit_account.status}")

    if credit_account.available_credit < amount:
        raise ValueError("Insufficient available credit")

    credit_account.available_credit -= amount
    credit_account.reserved_credit += amount
    credit_account.updated_at = datetime.now(timezone.utc)

    transaction = CreditTransaction(
        id=uuid.uuid4(),
        credit_account_id=credit_account.id,
        payout_id=None,
        type="RESERVE",
        amount=amount,
        balance_after=credit_account.available_credit,
        reason="Reserved for payout",
    )
    session.add(transaction)

    await log_audit(
        session,
        request_id=uuid.uuid4(),
        event_type="credit_reserved",
        detail={
            "credit_account_id": str(credit_account_id),
            "amount": amount,
            "available_after": credit_account.available_credit,
        },
    )

    return transaction


async def commit_spend(
    credit_account_id: uuid.UUID,
    payout_id: uuid.UUID,
    amount: int,
    session: AsyncSession,
) -> CreditTransaction:
    """Commit reserved credit after successful provider execution."""

    result = await session.execute(
        select(CreditAccount)
        .where(CreditAccount.id == credit_account_id)
        .with_for_update()
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise ValueError("Credit account not found")

    credit_account.reserved_credit -= amount
    credit_account.used_credit += amount
    credit_account.updated_at = datetime.now(timezone.utc)

    transaction = CreditTransaction(
        id=uuid.uuid4(),
        credit_account_id=credit_account.id,
        payout_id=payout_id,
        type="SPEND",
        amount=amount,
        balance_after=credit_account.available_credit,
        reason=f"Committed spend for payout {payout_id}",
    )
    session.add(transaction)

    await log_audit(
        session,
        request_id=uuid.uuid4(),
        event_type="credit_committed",
        detail={
            "credit_account_id": str(credit_account_id),
            "payout_id": str(payout_id),
            "amount": amount,
        },
    )

    return transaction


async def release_reservation(
    credit_account_id: uuid.UUID,
    amount: int,
    session: AsyncSession,
) -> CreditTransaction:
    """Release reservation on provider failure."""

    result = await session.execute(
        select(CreditAccount)
        .where(CreditAccount.id == credit_account_id)
        .with_for_update()
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise ValueError("Credit account not found")

    credit_account.available_credit += amount
    credit_account.reserved_credit -= amount
    credit_account.updated_at = datetime.now(timezone.utc)

    transaction = CreditTransaction(
        id=uuid.uuid4(),
        credit_account_id=credit_account.id,
        payout_id=None,
        type="RELEASE",
        amount=amount,
        balance_after=credit_account.available_credit,
        reason="Released reservation on provider failure",
    )
    session.add(transaction)

    await log_audit(
        session,
        request_id=uuid.uuid4(),
        event_type="credit_released",
        detail={
            "credit_account_id": str(credit_account_id),
            "amount": amount,
            "available_after": credit_account.available_credit,
        },
    )

    return transaction
