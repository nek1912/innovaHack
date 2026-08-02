import uuid
from datetime import datetime, date, timezone, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit import CreditAccount, RepaymentSchedule, CreditTransaction
from app.models.owner import Agent

# Grace period before defaulting (e.g., 7 days)
GRACE_PERIOD_DAYS = 7


async def create_repayment_schedule(
    credit_account_id: uuid.UUID,
    amount: int,
    due_date: date,
    session: AsyncSession,
) -> RepaymentSchedule:
    """Create a new repayment schedule entry."""

    repayment = RepaymentSchedule(
        id=uuid.uuid4(),
        credit_account_id=credit_account_id,
        due_date=due_date,
        amount=amount,
        status="pending",
        paid_amount=0,
        repayment_method="manual",
        provider_transaction_id=None,
    )
    session.add(repayment)
    return repayment


async def process_manual_repayment(
    repayment_id: uuid.UUID,
    session: AsyncSession,
) -> RepaymentSchedule:
    """Process a manual repayment (simulated)."""

    result = await session.execute(
        select(RepaymentSchedule).where(RepaymentSchedule.id == repayment_id)
    )
    repayment = result.scalar_one_or_none()

    if not repayment:
        raise ValueError("Repayment not found")

    if repayment.status not in ("pending", "late"):
        raise ValueError(f"Cannot repay in status: {repayment.status}")

    # Load credit account
    result = await session.execute(
        select(CreditAccount)
        .where(CreditAccount.id == repayment.credit_account_id)
        .with_for_update()
    )
    credit_account = result.scalar_one()

    # Update repayment
    repayment.status = "paid"
    repayment.paid_amount = repayment.amount
    repayment.repayment_method = "manual"
    repayment.updated_at = datetime.now(timezone.utc)

    # Restore credit
    credit_account.available_credit += repayment.amount
    credit_account.used_credit -= repayment.amount
    credit_account.updated_at = datetime.now(timezone.utc)

    # Create transaction record
    transaction = CreditTransaction(
        id=uuid.uuid4(),
        credit_account_id=credit_account.id,
        payout_id=None,
        type="REPAY",
        amount=repayment.amount,
        balance_after=credit_account.available_credit,
        reason=f"Manual repayment for schedule {repayment.id}",
    )
    session.add(transaction)

    return repayment


async def run_repayment_scheduler(session: AsyncSession) -> list[dict]:
    """
    Run the repayment scheduler.

    Finds overdue repayments and updates their status.
    Returns list of actions taken.
    """
    today = date.today()
    actions = []

    # Find pending repayments that are overdue
    result = await session.execute(
        select(RepaymentSchedule).where(
            and_(
                RepaymentSchedule.due_date < today,
                RepaymentSchedule.status == "pending",
            )
        )
    )
    overdue_pending = result.scalars().all()

    for repayment in overdue_pending:
        repayment.status = "late"
        repayment.updated_at = datetime.now(timezone.utc)
        actions.append({
            "type": "marked_late",
            "repayment_id": str(repayment.id),
            "due_date": str(repayment.due_date),
        })

    # Find late repayments past grace period
    default_cutoff = today - timedelta(days=GRACE_PERIOD_DAYS)
    result = await session.execute(
        select(RepaymentSchedule).where(
            and_(
                RepaymentSchedule.due_date < default_cutoff,
                RepaymentSchedule.status == "late",
            )
        )
    )
    late_defaults = result.scalars().all()

    for repayment in late_defaults:
        repayment.status = "defaulted"
        repayment.updated_at = datetime.now(timezone.utc)

        # Load credit account
        result = await session.execute(
            select(CreditAccount)
            .where(CreditAccount.id == repayment.credit_account_id)
            .with_for_update()
        )
        credit_account = result.scalar_one()

        # Create default transaction
        transaction = CreditTransaction(
            id=uuid.uuid4(),
            credit_account_id=credit_account.id,
            payout_id=None,
            type="DEFAULT",
            amount=repayment.amount - repayment.paid_amount,
            balance_after=credit_account.available_credit,
            reason=f"Defaulted: repayment {repayment.id} overdue by {GRACE_PERIOD_DAYS}+ days",
        )
        session.add(transaction)

        # Freeze agent
        result = await session.execute(
            select(Agent).where(Agent.id == credit_account.agent_id)
        )
        agent = result.scalar_one()
        agent.status = "frozen"

        # Freeze credit account
        credit_account.status = "frozen"

        # Create freeze transaction
        freeze_tx = CreditTransaction(
            id=uuid.uuid4(),
            credit_account_id=credit_account.id,
            payout_id=None,
            type="FREEZE",
            amount=0,
            balance_after=credit_account.available_credit,
            reason=f"Frozen due to default on repayment {repayment.id}",
        )
        session.add(freeze_tx)

        actions.append({
            "type": "defaulted",
            "repayment_id": str(repayment.id),
            "agent_id": str(credit_account.agent_id),
        })

    return actions
