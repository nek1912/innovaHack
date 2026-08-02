"""Policy input builder: daily spend aggregation + IST day boundaries (Part A/G)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.owner import Agent, Payee, Payout
from app.services.policy_input import build_policy_input
from tests.conftest import make_agent, make_owner, make_payee


async def _agent_payee_objects(client, db):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    return await db.get(Agent, uuid.UUID(agent["id"])), await db.get(Payee, uuid.UUID(payee["id"]))


async def test_daily_spend_sums_only_today(client, db):
    agent, payee = await _agent_payee_objects(client, db)
    now = datetime.now(timezone.utc)

    for status in ("queued", "processing", "processed"):
        db.add(Payout(agent_id=agent.id, payee_id=payee.id, amount_paise=10000,
                      mode="upi", purpose="t", policy_decision="allow",
                      razorpay_status=status, created_at=now))
    # yesterday + rejected don't count
    db.add(Payout(agent_id=agent.id, payee_id=payee.id, amount_paise=99999,
                  mode="upi", purpose="t", policy_decision="allow",
                  razorpay_status="processed",
                  created_at=now - timedelta(days=1)))
    db.add(Payout(agent_id=agent.id, payee_id=payee.id, amount_paise=88888,
                  mode="upi", purpose="t", policy_decision="allow",
                  razorpay_status="rejected", created_at=now))
    await db.commit()

    policy_input = await build_policy_input(db, agent.id, payee.id, 5000)
    assert policy_input["daily_spent_paise"] == 30000
    # JSON-serializable integers — asyncpg returns Decimal for SUM, which OPA
    # transport would choke on (regression: live-stack 500)
    assert type(policy_input["daily_spent_paise"]) is int
    assert type(policy_input["amount_paise"]) is int


async def test_ist_day_boundary_rollover(client, db):
    """Payouts at 23:59:59 IST are excluded, 00:00:01 IST included."""
    agent, payee = await _agent_payee_objects(client, db)

    # compute IST midnight as an instant (the IST-aware midnight converted to UTC)
    from app.services.policy_input import IST

    today_start_ist = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
    boundary_utc = today_start_ist.astimezone(timezone.utc)

    db.add(Payout(agent_id=agent.id, payee_id=payee.id, amount_paise=111,
                  mode="upi", purpose="t", policy_decision="allow",
                  razorpay_status="processed",
                  created_at=boundary_utc - timedelta(seconds=1)))  # yesterday in IST
    db.add(Payout(agent_id=agent.id, payee_id=payee.id, amount_paise=222,
                  mode="upi", purpose="t", policy_decision="allow",
                  razorpay_status="processed",
                  created_at=boundary_utc + timedelta(seconds=1)))  # today in IST
    await db.commit()

    policy_input = await build_policy_input(db, agent.id, payee.id, 1)
    assert policy_input["daily_spent_paise"] == 222


async def test_agent_not_found_raises(client, db):
    with pytest.raises(ValueError) as exc:
        await build_policy_input(db, uuid.uuid4(), uuid.uuid4(), 100)
    assert str(exc.value) == "agent_not_found"


async def test_payee_not_found_raises(client, db):
    agent, _ = await _agent_payee_objects(client, db)
    with pytest.raises(ValueError) as exc:
        await build_policy_input(db, agent.id, uuid.uuid4(), 100)
    assert str(exc.value) == "payee_not_found"


async def test_policy_input_echoes_caps(client, db):
    agent, payee = await _agent_payee_objects(client, db)
    policy_input = await build_policy_input(db, agent.id, payee.id, 5000)
    assert policy_input["per_tx_cap_paise"] == 100000
    assert policy_input["daily_cap_paise"] == 500000
    assert policy_input["approval_threshold_paise"] == 75000
    assert policy_input["agent_status"] == "active"
    assert policy_input["payee_active"] is True
