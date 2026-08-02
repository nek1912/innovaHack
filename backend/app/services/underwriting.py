import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner import Owner, Agent, Payout
from app.models.credit import CreditAccount, CreditTransaction, CreditDecision


async def calculate_score(
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    session: AsyncSession,
) -> tuple[int, str, int]:
    """
    Calculate credit score and approved limit.

    Returns: (score, reason_string, approved_limit_paise)
    Score range: 0-100
    """

    score = 50  # Base score
    reasons = []

    # Factor 1: Owner KYC status
    result = await session.execute(select(Owner).where(Owner.id == owner_id))
    owner = result.scalar_one()
    if owner.kyc_status == "live":
        score += 15
        reasons.append("owner_verified")
    elif owner.kyc_status == "test_only":
        score += 5
        reasons.append("owner_test_mode")
    else:
        score -= 10
        reasons.append("owner_kyc_pending")

    # Factor 2: Successful tasks (processed payouts)
    result = await session.execute(
        select(func.count(Payout.id)).where(
            Payout.agent_id == agent_id,
            Payout.razorpay_status == "processed"
        )
    )
    successful_tasks = result.scalar() or 0
    if successful_tasks > 10:
        score += 15
        reasons.append(f"experienced_agent({successful_tasks}_tasks)")
    elif successful_tasks > 0:
        score += 5
        reasons.append(f"some_experience({successful_tasks}_tasks)")
    else:
        reasons.append("new_agent")

    # Factor 3: Successful repayments
    result = await session.execute(
        select(func.count(CreditTransaction.id)).where(
            CreditTransaction.credit_account_id == CreditAccount.id,
            CreditAccount.agent_id == agent_id,
            CreditTransaction.type == "REPAY"
        )
    )
    successful_repays = result.scalar() or 0
    if successful_repays > 5:
        score += 10
        reasons.append(f"good_repayment_history({successful_repays})")

    # Factor 4: Active days
    result = await session.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one()
    active_days = (datetime.now(timezone.utc) - agent.created_at).days
    if active_days > 30:
        score += 5
        reasons.append(f"long_active({active_days}_days)")

    # Factor 5: Policy violations (negative)
    result = await session.execute(
        select(func.count(Payout.id)).where(
            Payout.agent_id == agent_id,
            Payout.policy_decision == "deny"
        )
    )
    violations = result.scalar() or 0
    if violations > 0:
        score -= min(violations * 2, 15)
        reasons.append(f"policy_violations({violations})")

    # Factor 6: Provider failures (negative)
    result = await session.execute(
        select(func.count(Payout.id)).where(
            Payout.agent_id == agent_id,
            Payout.razorpay_status.in_(["reversed", "rejected"])
        )
    )
    failures = result.scalar() or 0
    if failures > 0:
        score -= min(failures * 3, 15)
        reasons.append(f"provider_failures({failures})")

    # Factor 7: Defaults (negative)
    result = await session.execute(
        select(func.count(CreditTransaction.id)).where(
            CreditTransaction.credit_account_id == CreditAccount.id,
            CreditAccount.agent_id == agent_id,
            CreditTransaction.type == "DEFAULT"
        )
    )
    defaults = result.scalar() or 0
    if defaults > 0:
        score -= min(defaults * 10, 30)
        reasons.append(f"defaults({defaults})")

    # Clamp score
    score = max(0, min(100, score))

    # Calculate approved limit based on score
    if score >= 80:
        limit = 1_000_000  # ₹10,000
    elif score >= 60:
        limit = 5_00_000   # ₹5,000
    elif score >= 40:
        limit = 2_00_000   # ₹2,000
    else:
        limit = 0          # No credit approved

    reason_string = "; ".join(reasons)

    # Record decision
    decision = CreditDecision(
        id=uuid.uuid4(),
        agent_id=agent_id,
        decision="approved" if limit > 0 else "rejected",
        score=score,
        reason=reason_string,
        approved_limit=limit if limit > 0 else None,
        model_version="v1",
    )
    session.add(decision)

    return score, reason_string, limit
