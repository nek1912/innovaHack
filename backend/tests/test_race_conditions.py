"""Race conditions: concurrent payouts, double approve, webhook timing."""

import asyncio
import uuid

import pytest
from sqlalchemy import select, func

from app.models.owner import AuditLog, Payout
from app.services.razorpayx import RazorpayXError
from tests.conftest import auth_headers, make_agent, make_owner, make_payee, seed_payout


async def _agent_payee(client):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    return owner, agent, payee


def _agent_headers(agent) -> dict:
    return {"X-Api-Key": agent["api_key"]}


# ---- concurrent payout requests ----


async def test_concurrent_identical_requests_only_one_succeeds(client, db, mock_razorpayx):
    """Two identical requests at the same time: one succeeds, one hits duplicate guard."""
    owner, agent, payee = await _agent_payee(client)
    headers = _agent_headers(agent)

    async def do_request():
        return await client.post(
            "/agent/request-payout",
            json={"payee_id": payee["id"], "amount_paise": 50000, "mode": "upi"},
            headers=headers,
        )

    results = await asyncio.gather(do_request(), do_request(), return_exceptions=True)

    statuses = [r.status_code for r in results if not isinstance(r, Exception)]
    assert 200 in statuses, f"Expected one 200, got {statuses}"
    non_200 = [s for s in statuses if s != 200]
    assert all(s in (409, 200) for s in statuses), f"Unexpected statuses: {statuses}"

    payout_count = (await db.execute(select(func.count(Payout.id)))).scalar()
    assert payout_count == 1


async def test_concurrent_different_amounts_both_succeed(client, db, mock_razorpayx):
    """Two requests with different amounts: both should succeed (no duplicate match)."""
    owner, agent, payee = await _agent_payee(client)
    headers = _agent_headers(agent)

    async def do_request(amount):
        return await client.post(
            "/agent/request-payout",
            json={"payee_id": payee["id"], "amount_paise": amount, "mode": "upi"},
            headers=headers,
        )

    r1, r2 = await asyncio.gather(do_request(50000), do_request(50001))
    assert r1.status_code == 200
    assert r2.status_code == 200

    payout_count = (await db.execute(select(func.count(Payout.id)))).scalar()
    assert payout_count == 2


# ---- double approve ----


async def test_double_approve_second_rejected(client, db, mock_opa, mock_razorpayx):
    """Approving the same payout twice: second call returns 404 (no longer pending)."""
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}
    payout_id = (await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent),
    )).json()["id"]

    r1 = await client.post(
        f"/owner/payouts/{payout_id}/approve",
        headers=await auth_headers(owner["token"]),
    )
    assert r1.status_code == 200

    r2 = await client.post(
        f"/owner/payouts/{payout_id}/approve",
        headers=await auth_headers(owner["token"]),
    )
    assert r2.status_code == 404
    assert r2.json()["detail"]["error"] == "payout_not_found"


async def test_double_reject_second_rejected(client, db, mock_opa):
    """Rejecting the same payout twice: second call returns 404."""
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}
    payout_id = (await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent),
    )).json()["id"]

    r1 = await client.post(
        f"/owner/payouts/{payout_id}/reject",
        headers=await auth_headers(owner["token"]),
    )
    assert r1.status_code == 200

    r2 = await client.post(
        f"/owner/payouts/{payout_id}/reject",
        headers=await auth_headers(owner["token"]),
    )
    assert r2.status_code == 404


# ---- webhook timing ----


async def test_webhook_arrives_before_request_response(client, db, mock_razorpayx):
    """Simulate webhook arriving while payout is still 'in flight':
    webhook should update status, and local state should reflect it."""
    owner, agent, payee = await _agent_payee(client)
    from app.models.owner import Agent as AgentModel, Payee as PayeeModel

    agent_obj = await db.get(AgentModel, uuid.UUID(agent["id"]))
    payee_obj = await db.get(PayeeModel, uuid.UUID(payee["id"]))
    payout = await seed_payout(
        db, agent_obj, payee_obj,
        razorpay_status="queued", razorpay_payout_id="pay_timing_1",
    )

    import json, hashlib, hmac

    payload = {"event": "payout.processed", "payload": {"payout": {"entity": {"id": "pay_timing_1", "status": "processed"}}}}
    body = json.dumps(payload).encode()
    sig = hmac.new(b"whsec_test", body, hashlib.sha256).hexdigest()

    res = await client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": sig},
    )
    assert res.status_code == 200

    await db.refresh(payout)
    assert payout.razorpay_status == "processed"


async def test_concurrent_webhooks_same_payout_idempotent(client, db):
    """Two identical webhooks for the same payout: both accepted, only one audit entry."""
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    from app.models.owner import Agent as AgentModel, Payee as PayeeModel

    agent_obj = await db.get(AgentModel, uuid.UUID(agent["id"]))
    payee_obj = await db.get(PayeeModel, uuid.UUID(payee["id"]))
    payout = await seed_payout(
        db, agent_obj, payee_obj,
        razorpay_status="queued", razorpay_payout_id="pay_concurrent_web",
    )

    import json, hashlib, hmac

    payload = {"event": "payout.processed", "payload": {"payout": {"entity": {"id": "pay_concurrent_web", "status": "processed"}}}}
    body = json.dumps(payload).encode()
    sig = hmac.new(b"whsec_test", body, hashlib.sha256).hexdigest()

    async def post_webhook():
        return await client.post(
            "/webhooks/razorpay",
            content=body,
            headers={"X-Razorpay-Signature": sig},
        )

    r1, r2 = await asyncio.gather(post_webhook(), post_webhook())
    assert r1.status_code == 200
    assert r2.status_code == 200

    count = (
        await db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.event_type == "payout_webhook")
        )
    ).scalar()
    assert count == 1


# ---- approve during payout request ----


async def test_approve_during_inflight_payout_request(client, db, mock_opa, mock_razorpayx):
    """Approval request and payout request on same payout should not double-pay."""
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}

    payout_id = (await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent),
    )).json()["id"]

    mock_razorpayx.calls = []
    approve_res = await client.post(
        f"/owner/payouts/{payout_id}/approve",
        headers=await auth_headers(owner["token"]),
    )
    assert approve_res.status_code == 200

    payout_calls = [c for c in mock_razorpayx.calls if c[0] == "create_payout"]
    assert len(payout_calls) == 1
