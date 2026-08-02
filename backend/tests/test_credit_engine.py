import uuid
from unittest.mock import patch

import pytest

from app.models.credit import CreditAccount, CreditTransaction
from app.models.owner import Owner, Agent
from app.services.credit_engine import (
    issue_credit,
    reserve_credit,
    commit_spend,
    release_reservation,
)
from tests.conftest import make_agent, make_owner


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


@pytest.mark.asyncio
async def test_issue_credit(db, test_owner, test_agent):
    """Test credit issuance creates account and transaction."""
    with patch("app.services.credit_engine.calculate_score", return_value=(70, "owner_verified", 200000)):
        credit_account = await issue_credit(
            owner_id=test_owner.id,
            agent_id=test_agent.id,
            session=db,
        )

    assert credit_account is not None
    assert credit_account.agent_id == test_agent.id
    assert credit_account.owner_id == test_owner.id
    assert credit_account.credit_limit > 0
    assert credit_account.available_credit == credit_account.credit_limit
    assert credit_account.used_credit == 0
    assert credit_account.reserved_credit == 0
    assert credit_account.status == "active"


@pytest.mark.asyncio
async def test_reserve_credit(db, test_credit_account):
    """Test credit reservation reduces available and increases reserved."""
    initial_available = test_credit_account.available_credit
    reserve_amount = 1000

    transaction = await reserve_credit(
        credit_account_id=test_credit_account.id,
        amount=reserve_amount,
        session=db,
    )

    assert transaction.type == "RESERVE"
    assert transaction.amount == reserve_amount
    assert test_credit_account.available_credit == initial_available - reserve_amount
    assert test_credit_account.reserved_credit == reserve_amount


@pytest.mark.asyncio
async def test_reserve_exceeds_available(db, test_credit_account):
    """Test reservation fails when insufficient credit."""
    amount = test_credit_account.available_credit + 1

    with pytest.raises(ValueError, match="Insufficient available credit"):
        await reserve_credit(
            credit_account_id=test_credit_account.id,
            amount=amount,
            session=db,
        )


@pytest.mark.asyncio
async def test_commit_spend(db, test_credit_account):
    """Test commit moves reserved to used."""
    reserve_amount = 1000
    await reserve_credit(
        credit_account_id=test_credit_account.id,
        amount=reserve_amount,
        session=db,
    )

    # Use None for payout_id since we're testing credit engine, not payout creation
    transaction = await commit_spend(
        credit_account_id=test_credit_account.id,
        payout_id=None,
        amount=reserve_amount,
        session=db,
    )

    assert transaction.type == "SPEND"
    assert transaction.payout_id is None
    assert test_credit_account.reserved_credit == 0
    assert test_credit_account.used_credit == reserve_amount


@pytest.mark.asyncio
async def test_release_reservation(db, test_credit_account):
    """Test release restores available credit."""
    reserve_amount = 1000
    await reserve_credit(
        credit_account_id=test_credit_account.id,
        amount=reserve_amount,
        session=db,
    )

    transaction = await release_reservation(
        credit_account_id=test_credit_account.id,
        amount=reserve_amount,
        session=db,
    )

    assert transaction.type == "RELEASE"
    assert test_credit_account.reserved_credit == 0
    assert test_credit_account.available_credit == test_credit_account.credit_limit


@pytest.mark.asyncio
async def test_concurrent_reserve(db, test_credit_account):
    """Test concurrent reservations - only one should succeed when credit is tight."""
    import asyncio
    from app.db import async_session

    async def try_reserve():
        async with async_session() as session:
            try:
                await reserve_credit(
                    credit_account_id=test_credit_account.id,
                    amount=600,
                    session=session,
                )
                await session.commit()
                return True
            except ValueError:
                await session.rollback()
                return False

    # Both try 600, but only 1000 available.
    # First commits (1000→400), second fails (400 < 600).
    # ponytail: true concurrency needs separate threads/processes;
    # asyncio.gather on one event loop serializes at DB lock level.
    test_credit_account.available_credit = 1000
    await db.commit()

    results = await asyncio.gather(
        try_reserve(),
        try_reserve(),
        return_exceptions=True,
    )

    successes = sum(1 for r in results if r is True)
    assert successes == 1
