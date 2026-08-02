import pytest
import uuid
from unittest.mock import patch

from app.services.credit_engine import issue_credit, reserve_credit, commit_spend, release_reservation
from app.services.repayment import process_manual_repayment, create_repayment_schedule
from datetime import date, timedelta
from app.models.credit import CreditAccount
from app.models.owner import Owner, Agent, Payee, Payout


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
async def test_payee(db, test_agent):
    payee = Payee(
        id=uuid.uuid4(),
        agent_id=test_agent.id,
        label=f"payee-{uuid.uuid4().hex[:6]}",
        vpa="payee@upi",
    )
    db.add(payee)
    await db.commit()
    return payee


@pytest.fixture
async def test_payout(db, test_agent, test_payee):
    payout = Payout(
        id=uuid.uuid4(),
        agent_id=test_agent.id,
        payee_id=test_payee.id,
        amount_paise=1000,
        mode="upi",
        purpose="test",
        policy_decision="allow",
    )
    db.add(payout)
    await db.commit()
    return payout


@pytest.mark.asyncio
async def test_full_flow(db, test_owner, test_agent, test_payee, test_payout):
    with patch("app.services.credit_engine.calculate_score", return_value=(70, "owner_verified", 500000)):
        credit_account = await issue_credit(
            owner_id=test_owner.id,
            agent_id=test_agent.id,
            session=db,
        )
    assert credit_account.available_credit > 0

    reserve_amount = 1000
    await reserve_credit(
        credit_account_id=credit_account.id,
        amount=reserve_amount,
        session=db,
    )
    assert credit_account.reserved_credit == reserve_amount

    await commit_spend(
        credit_account_id=credit_account.id,
        payout_id=test_payout.id,
        amount=reserve_amount,
        session=db,
    )
    assert credit_account.used_credit == reserve_amount
    assert credit_account.reserved_credit == 0

    repayment = await create_repayment_schedule(
        credit_account_id=credit_account.id,
        amount=reserve_amount,
        due_date=date.today() + timedelta(days=30),
        session=db,
    )
    await db.commit()

    await process_manual_repayment(
        repayment_id=repayment.id,
        session=db,
    )

    assert credit_account.available_credit == credit_account.credit_limit
    assert credit_account.used_credit == 0


@pytest.mark.asyncio
async def test_provider_failure_flow(db, test_owner, test_agent):
    with patch("app.services.credit_engine.calculate_score", return_value=(70, "owner_verified", 500000)):
        credit_account = await issue_credit(
            owner_id=test_owner.id,
            agent_id=test_agent.id,
            session=db,
        )
    initial_available = credit_account.available_credit

    reserve_amount = 1000
    await reserve_credit(
        credit_account_id=credit_account.id,
        amount=reserve_amount,
        session=db,
    )

    await release_reservation(
        credit_account_id=credit_account.id,
        amount=reserve_amount,
        session=db,
    )

    assert credit_account.available_credit == initial_available
    assert credit_account.reserved_credit == 0
    assert credit_account.used_credit == 0


@pytest.mark.asyncio
async def test_default_flow(db, test_owner, test_agent, test_payee, test_payout):
    with patch("app.services.credit_engine.calculate_score", return_value=(70, "owner_verified", 500000)):
        credit_account = await issue_credit(
            owner_id=test_owner.id,
            agent_id=test_agent.id,
            session=db,
        )

    reserve_amount = 1000
    await reserve_credit(
        credit_account_id=credit_account.id,
        amount=reserve_amount,
        session=db,
    )
    await commit_spend(
        credit_account_id=credit_account.id,
        payout_id=test_payout.id,
        amount=reserve_amount,
        session=db,
    )

    repayment = await create_repayment_schedule(
        credit_account_id=credit_account.id,
        amount=reserve_amount,
        due_date=date.today() - timedelta(days=10),
        session=db,
    )
    await db.commit()

    repayment.status = "late"
    await db.commit()

    from app.services.repayment import run_repayment_scheduler
    await run_repayment_scheduler(db)
    await db.commit()

    await db.refresh(test_agent)
    assert test_agent.status == "frozen"
    assert credit_account.status == "frozen"
