import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner import Agent, Payout
from app.models.credit import CreditAccount, CreditTransaction


async def calculate_risk(owner_id: uuid.UUID, session: AsyncSession) -> dict:
    """
    Calculate risk summary for all agents under an owner.

    Returns dict with risk levels and factors.
    """
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    # Get all agents for owner
    result = await session.execute(
        select(Agent).where(Agent.owner_id == owner_id)
    )
    agents = result.scalars().all()

    agent_risks = []
    total_violations = 0
    total_failures = 0
    total_defaults = 0
    total_frozen = 0

    for agent in agents:
        # Count policy violations
        result = await session.execute(
            select(func.count(Payout.id)).where(
                Payout.agent_id == agent.id,
                Payout.created_at >= thirty_days_ago,
                Payout.policy_decision == "deny",
            )
        )
        violations = result.scalar() or 0
        total_violations += violations

        # Count provider failures
        result = await session.execute(
            select(func.count(Payout.id)).where(
                Payout.agent_id == agent.id,
                Payout.created_at >= thirty_days_ago,
                Payout.razorpay_status.in_(["reversed", "rejected"]),
            )
        )
        failures = result.scalar() or 0
        total_failures += failures

        # Count defaults
        result = await session.execute(
            select(func.count(CreditTransaction.id)).where(
                CreditTransaction.credit_account_id == CreditAccount.id,
                CreditAccount.agent_id == agent.id,
                CreditTransaction.type == "DEFAULT",
                CreditTransaction.created_at >= thirty_days_ago,
            )
        )
        defaults = result.scalar() or 0
        total_defaults += defaults

        # Check if frozen
        is_frozen = agent.status == "frozen"
        if is_frozen:
            total_frozen += 1

        # Calculate agent risk score
        risk_score = 0
        risk_score += violations * 10
        risk_score += failures * 15
        risk_score += defaults * 25
        risk_score += 20 if is_frozen else 0

        # Determine risk level
        if risk_score >= 50:
            risk_level = "CRITICAL"
        elif risk_score >= 30:
            risk_level = "HIGH"
        elif risk_score >= 10:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        agent_risks.append({
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "violations": violations,
            "failures": failures,
            "defaults": defaults,
            "is_frozen": is_frozen,
        })

    # Overall risk
    overall_score = total_violations * 10 + total_failures * 15 + total_defaults * 25 + total_frozen * 20
    if overall_score >= 100:
        overall_risk = "CRITICAL"
    elif overall_score >= 50:
        overall_risk = "HIGH"
    elif overall_score >= 20:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    return {
        "overall_risk": overall_risk,
        "overall_score": overall_score,
        "total_violations": total_violations,
        "total_failures": total_failures,
        "total_defaults": total_defaults,
        "total_frozen": total_frozen,
        "agents": agent_risks,
    }
