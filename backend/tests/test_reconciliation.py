"""Reconciliation: provider truth drives status (Part A/D)."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func

from app.models.owner import Agent, AuditLog, Payee, Payout
from app.services.razorpayx import RazorpayXError
from app.services.reconciliation import reconcile_stale_payouts
from tests.conftest import auth_headers, make_agent, make_owner, make_payee


async def _stuck_payout(client, db, status="queued", created_minutes_ago=60) -> Payout:
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    agent_obj = await db.get(Agent, uuid.UUID(agent["id"]))
    payee_obj = await db.get(Payee, uuid.UUID(payee["id"]))
    payout = Payout(
        agent_id=agent_obj.id,
        payee_id=payee_obj.id,
        amount_paise=50000,
        mode="upi",
        purpose="test",
        policy_decision="allow",
        razorpay_status=status,
        razorpay_payout_id="pay_rec_1",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=created_minutes_ago),
    )
    db.add(payout)
    await db.commit()
    return payout


async def test_reconcile_applies_provider_truth(client, db, mock_razorpayx):
    payout = await _stuck_payout(client, db)
    mock_razorpayx.fetched = {"id": "pay_rec_1", "status": "processed"}

    await reconcile_stale_payouts()

    await db.refresh(payout)  # reload — identity map holds stale state otherwise
    assert payout.razorpay_status == "processed"

    entries = (
        await db.execute(
            select(AuditLog).where(AuditLog.event_type == "payout_reconciled")
        )
    ).scalars().all()
    assert len(entries) == 1
    assert entries[0].detail["old_status"] == "queued"
    assert entries[0].detail["new_status"] == "processed"


async def test_reconcile_marks_stale_on_provider_404(client, db, mock_razorpayx):
    payout = await _stuck_payout(client, db)
    mock_razorpayx.errors["fetch_payout"] = RazorpayXError(404, "not_found", "no such payout")

    await reconcile_stale_payouts()

    await db.refresh(payout)
    assert payout.razorpay_status == "stale"

    entries = (
        await db.execute(select(AuditLog).where(AuditLog.event_type == "payout_stale"))
    ).scalars().all()
    assert len(entries) == 1
    assert entries[0].detail["reason"] == "provider_not_found"


async def test_reconcile_skips_on_provider_5xx(client, db, mock_razorpayx):
    payout = await _stuck_payout(client, db)
    mock_razorpayx.errors["fetch_payout"] = RazorpayXError(500, "server_error", "boom")

    await reconcile_stale_payouts()

    await db.refresh(payout)
    assert payout.razorpay_status == "queued"  # unchanged, never marked stale

    count = (
        await db.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.event_type.in_(["payout_stale", "payout_reconciled"])
            )
        )
    ).scalar()
    assert count == 0


async def test_reconcile_skips_fresh_and_local_error_timeouts(client, db, mock_razorpayx):
    # too fresh: below threshold, provider never queried
    fresh = await _stuck_payout(client, db, created_minutes_ago=1)
    await reconcile_stale_payouts()
    assert mock_razorpayx.calls == []
    await db.refresh(fresh)
    assert fresh.razorpay_status == "queued"


async def test_reconcile_leaves_unknown_provider_status(client, db, mock_razorpayx):
    payout = await _stuck_payout(client, db)
    mock_razorpayx.fetched = {"id": "pay_rec_1", "status": "mystery_state"}
    await reconcile_stale_payouts()
    await db.refresh(payout)
    assert payout.razorpay_status == "queued"
