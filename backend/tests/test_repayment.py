import pytest
import uuid
from datetime import date, timedelta

from app.services.repayment import (
    create_repayment_schedule,
    process_manual_repayment,
    run_repayment_scheduler,
)
from app.models.credit import RepaymentSchedule, CreditTransaction
from app.models.credit import CreditAccount
from app.models.owner import Owner, Agent


@pytest.fixture
async def test_owner(db):
    owner = Owner(
        id=uuid.uuid4(),
        name="Test Owner",
        email=f"owner-{uuid.uuid4().hex[:8]}@test.dev",
        password_hash="hash",
        kyc_status="live",
    )
    db.add(owner)
    await db.commit()
    return owner


@pytest.fixture
async def test_agent(db, test_owner):
    agent = Agent(
        id=uuid.uuid4(),
        owner_id=test_owner.id,
        name=f"agent-{uuid.uuid4().hex[:6]}",
        api_key_hash="hash",
        status="active",
        per_tx_cap_paise=100000,
        daily_cap_paise=500000,
        approval_threshold_paise=75000,
    )
    db.add(agent)
    await db.commit()
    return agent


@pytest.fixture
async def test_credit_account(db, test_owner, test_agent):
    account = CreditAccount(
        id=uuid.uuid4(),
        owner_id=test_owner.id,
        agent_id=test_agent.id,
        credit_limit=500000,
        available_credit=500000,
        used_credit=0,
        reserved_credit=0,
        currency="INR",
        status="active",
    )
    db.add(account)
    await db.commit()
    return account


@pytest.fixture
async def test_repayment(db, test_credit_account):
    repayment = RepaymentSchedule(
        id=uuid.uuid4(),
        credit_account_id=test_credit_account.id,
        due_date=date.today() + timedelta(days=30),
        amount=5000,
        status="pending",
        paid_amount=0,
        repayment_method="manual",
    )
    db.add(repayment)
    await db.commit()
    return repayment


@pytest.mark.asyncio
async def test_create_repayment(db, test_credit_account):
    due_date = date.today() + timedelta(days=30)
    amount = 5000

    repayment = await create_repayment_schedule(
        credit_account_id=test_credit_account.id,
        amount=amount,
        due_date=due_date,
        session=db,
    )

    assert repayment is not None
    assert repayment.amount == amount
    assert repayment.due_date == due_date
    assert repayment.status == "pending"
    assert repayment.paid_amount == 0


@pytest.mark.asyncio
async def test_manual_repay(db, test_credit_account, test_repayment):
    initial_available = test_credit_account.available_credit
    initial_used = test_credit_account.used_credit

    repayment = await process_manual_repayment(
        repayment_id=test_repayment.id,
        session=db,
    )

    assert repayment.status == "paid"
    assert repayment.paid_amount == repayment.amount
    assert test_credit_account.available_credit == initial_available + repayment.amount
    assert test_credit_account.used_credit == initial_used - repayment.amount


@pytest.mark.asyncio
async def test_scheduler_marks_late(db, test_credit_account):
    repayment = await create_repayment_schedule(
        credit_account_id=test_credit_account.id,
        amount=1000,
        due_date=date.today() - timedelta(days=1),
        session=db,
    )
    await db.commit()

    actions = await run_repayment_scheduler(db)

    assert len(actions) == 1
    assert actions[0]["type"] == "marked_late"

    await db.refresh(repayment)
    assert repayment.status == "late"


@pytest.mark.asyncio
async def test_scheduler_defaults(db, test_credit_account, test_agent):
    repayment = await create_repayment_schedule(
        credit_account_id=test_credit_account.id,
        amount=1000,
        due_date=date.today() - timedelta(days=10),
        session=db,
    )
    await db.commit()

    repayment.status = "late"
    await db.commit()

    actions = await run_repayment_scheduler(db)
    await db.commit()

    default_actions = [a for a in actions if a["type"] == "defaulted"]
    assert len(default_actions) == 1

    await db.refresh(test_agent)
    assert test_agent.status == "frozen"
