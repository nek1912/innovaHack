"""Payout request / approval workflows with mocked OPA + RazorpayX (Part A)."""

import uuid
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


async def _request(client, agent, payee_id, amount=50000, mode="upi"):
    return await client.post(
        "/agent/request-payout",
        json={"payee_id": payee_id, "amount_paise": amount, "mode": mode},
        headers=_agent_headers(agent),
    )


async def _audit_events(db, agent_id, event_type=None):
    q = select(AuditLog).where(AuditLog.agent_id == uuid.UUID(agent_id))
    if event_type:
        q = q.where(AuditLog.event_type == event_type)
    return (await db.execute(q)).scalars().all()


# ---- allow path ----


async def test_payout_allowed_creates_real_payout(client, db, mock_razorpayx):
    owner, agent, payee = await _agent_payee(client)
    res = await _request(client, agent, payee["id"])

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "queued"
    assert body["policy_decision"] == "allow"

    payout = (await db.execute(select(Payout))).scalar_one()
    assert payout.razorpay_payout_id == "pay_test"
    assert payout.razorpay_status == "queued"

    # provider was called: contact -> fund account -> payout with idempotency key
    keys = [c[0] for c in mock_razorpayx.calls]
    assert keys == ["create_contact", "create_fund_account", "create_payout"]
    payout_call = mock_razorpayx.calls[-1][1]
    assert payout_call["idempotency_key"] == str(payout.id)
    assert payout_call["fund_account_id"] == "fa_test"

    # audits recorded
    events = await _audit_events(db, agent["id"])
    assert [e.event_type for e in events] == ["provider_payout_created"]


async def test_payout_allow_path_reuses_provider_ids(client, db, mock_razorpayx):
    owner, agent, payee = await _agent_payee(client)
    await _request(client, agent, payee["id"])

    mock_razorpayx.calls = []
    # different amount so the 60s duplicate window doesn't reject it
    await _request(client, agent, payee["id"], amount=50001)
    # second request: no contact/fund-account calls, only the payout
    assert [c[0] for c in mock_razorpayx.calls] == ["create_payout"]


# ---- deny paths (OPA decision) ----


async def test_deny_per_tx_cap(client, db, mock_opa):
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "per_tx_cap_exceeded"}
    res = await _request(client, agent, payee["id"])
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "per_tx_cap_exceeded"
    events = await _audit_events(db, agent["id"], "policy_denied")
    assert len(events) == 1
    assert events[0].detail["reason"] == "per_tx_cap_exceeded"


async def test_deny_daily_cap(client, mock_opa):
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "daily_cap_exceeded"}
    res = await _request(client, agent, payee["id"])
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "daily_cap_exceeded"


async def test_deny_agent_frozen(client, mock_opa):
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "agent_frozen"}
    res = await _request(client, agent, payee["id"])
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "agent_frozen"


async def test_deny_unknown_reason_maps_to_policy_denied(client, mock_opa):
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "something_new"}
    res = await _request(client, agent, payee["id"])
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "policy_denied"


# ---- approval path ----


async def test_approval_required_no_provider_call(client, db, mock_opa, mock_razorpayx):
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}
    res = await _request(client, agent, payee["id"])

    assert res.status_code == 200
    assert res.json()["status"] == "pending_approval"
    assert res.json()["policy_decision"] == "approval_required"
    assert mock_razorpayx.calls == []  # nothing sent to provider

    payout = (await db.execute(select(Payout))).scalar_one()
    assert payout.policy_decision == "approval_required"
    events = await _audit_events(db, agent["id"], "approval_required")
    assert len(events) == 1


async def test_approve_executes_payout(client, db, mock_opa, mock_razorpayx):
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}
    payout_id = (await _request(client, agent, payee["id"])).json()["id"]

    mock_razorpayx.calls = []
    res = await client.post(
        f"/owner/payouts/{payout_id}/approve", headers=await auth_headers(owner["token"])
    )
    assert res.status_code == 200

    payout = await db.get(Payout, uuid.UUID(payout_id))
    assert payout.policy_decision == "allow"
    assert payout.approved_by is not None
    assert payout.razorpay_payout_id == "pay_test"
    assert payout.razorpay_status == "queued"
    assert mock_razorpayx.calls[-1][0] == "create_payout"
    assert mock_razorpayx.calls[-1][1]["idempotency_key"] == payout_id

    events = await _audit_events(db, agent["id"], "payout_approved")
    assert len(events) == 1


async def test_approve_not_pending_payout(client, mock_opa):
    owner, agent, payee = await _agent_payee(client)
    res = await _request(client, agent, payee["id"])  # allow path
    payout_id = res.json()["id"]
    res = await client.post(
        f"/owner/payouts/{payout_id}/approve", headers=await auth_headers(owner["token"])
    )
    assert res.status_code == 404
    assert res.json()["detail"]["error"] == "payout_not_found"


async def test_approve_other_owners_payout_forbidden(client, mock_opa):
    owner, agent, payee = await _agent_payee(client)
    other = await make_owner(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}
    payout_id = (await _request(client, agent, payee["id"])).json()["id"]
    res = await client.post(
        f"/owner/payouts/{payout_id}/approve", headers=await auth_headers(other["token"])
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "unauthorized_owner_access"


async def test_reject_payout(client, db, mock_opa, mock_razorpayx):
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}
    payout_id = (await _request(client, agent, payee["id"])).json()["id"]

    res = await client.post(
        f"/owner/payouts/{payout_id}/reject", headers=await auth_headers(owner["token"])
    )
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"

    payout = await db.get(Payout, uuid.UUID(payout_id))
    assert payout.policy_decision == "rejected"
    assert mock_razorpayx.calls == []
    events = await _audit_events(db, agent["id"], "payout_rejected")
    assert len(events) == 1


async def test_reject_other_owners_payout_forbidden(client, mock_opa):
    owner, agent, payee = await _agent_payee(client)
    other = await make_owner(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}
    payout_id = (await _request(client, agent, payee["id"])).json()["id"]
    res = await client.post(
        f"/owner/payouts/{payout_id}/reject", headers=await auth_headers(other["token"])
    )
    assert res.status_code == 403


# ---- provider failures ----


async def test_provider_4xx_failure_maps_to_422(client, db, mock_razorpayx):
    owner, agent, payee = await _agent_payee(client)
    mock_razorpayx.errors["create_payout"] = RazorpayXError(400, "bad_request", "invalid fund account")
    res = await _request(client, agent, payee["id"])

    assert res.status_code == 422
    assert res.json()["detail"]["error"] == "provider_rejected"

    payout = (await db.execute(select(Payout))).scalar_one()
    assert payout.razorpay_status == "local_error"  # persisted, not lost

    events = await _audit_events(db, agent["id"], "provider_failure")
    assert len(events) == 1
    assert events[0].detail["provider_error_code"] == "bad_request"


async def test_provider_timeout_maps_to_502(client, db, mock_razorpayx):
    owner, agent, payee = await _agent_payee(client)
    mock_razorpayx.errors["create_payout"] = RazorpayXError(504, "provider_timeout", "Payment provider timed out")
    res = await _request(client, agent, payee["id"])

    assert res.status_code == 502
    assert "retry later" in res.json()["detail"]["message"]
    payout = (await db.execute(select(Payout))).scalar_one()
    assert payout.razorpay_status == "local_error"


async def test_provider_failure_during_contact_creation(client, db, mock_razorpayx):
    owner, agent, payee = await _agent_payee(client)
    mock_razorpayx.errors["create_contact"] = RazorpayXError(500, "server_error", "boom")
    res = await _request(client, agent, payee["id"])
    assert res.status_code == 502
    assert res.json()["detail"]["error"] == "provider_failure"
    events = await _audit_events(db, agent["id"], "provider_failure")
    assert len(events) == 1


# ---- request validation / guards ----


async def test_payout_unknown_payee(client):
    owner, agent, _ = await _agent_payee(client)
    res = await _request(client, agent, str(uuid.uuid4()))
    assert res.status_code == 404
    assert res.json()["detail"]["error"] == "payee_not_found"


async def test_payout_payee_of_another_agent(client):
    owner, agent, _ = await _agent_payee(client)
    other_owner, other_agent, other_payee = await _agent_payee(client)
    res = await _request(client, agent, other_payee["id"])
    assert res.status_code == 404
    assert res.json()["detail"]["error"] == "payee_not_found"


async def test_payout_invalid_mode(client):
    owner, agent, payee = await _agent_payee(client)
    res = await _request(client, agent, payee["id"], mode="bitcoin")
    assert res.status_code == 422


async def test_payout_zero_amount(client):
    owner, agent, payee = await _agent_payee(client)
    res = await _request(client, agent, payee["id"], amount=0)
    assert res.status_code == 422


# ---- duplicate request risk ----


async def test_duplicate_request_within_window_rejected(client, db):
    owner, agent, payee = await _agent_payee(client)
    first = await _request(client, agent, payee["id"])
    assert first.status_code == 200

    second = await _request(client, agent, payee["id"])
    assert second.status_code == 409
    assert second.json()["detail"]["error"] == "duplicate_request_risk"

    events = await _audit_events(db, agent["id"], "duplicate_request_risk")
    assert len(events) == 1


# ---- dashboard stats (Part F) ----


async def test_dashboard_stats(client, db, mock_opa):
    owner, agent, payee = await _agent_payee(client)

    # one policy violation (denied request recorded in audit)
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "daily_cap_exceeded"}
    await _request(client, agent, payee["id"])

    # seed provider outcomes directly
    mock_opa.decision = {"allow": True, "requires_approval": False, "deny_reason": None}
    from app.models.owner import Agent as AgentModel, Payee as PayeeModel

    agent_obj = await db.get(AgentModel, uuid.UUID(agent["id"]))
    payee_obj = await db.get(PayeeModel, uuid.UUID(payee["id"]))
    await seed_payout(db, agent_obj, payee_obj, razorpay_status="processed", razorpay_payout_id="pay_1")
    await seed_payout(db, agent_obj, payee_obj, razorpay_status="failed", razorpay_payout_id="pay_2")
    await seed_payout(db, agent_obj, payee_obj, razorpay_status="stale", razorpay_payout_id="pay_3")
    await seed_payout(db, agent_obj, payee_obj, policy_decision="approval_required")

    res = await client.get("/owner/stats", headers=await auth_headers(owner["token"]))
    assert res.status_code == 200
    stats = res.json()
    assert stats["pending_approvals"] == 1
    assert stats["policy_violations"] == 1
    assert stats["payment_success_rate"] == 50  # 1 processed of 2 terminal
    assert stats["stale_payouts"] == 1
    assert stats["provider_mode"] == "test"
    assert stats["provider_configured"] is True  # test creds + debit identifier set
    assert stats["today_limit_paise"] == agent["daily_cap_paise"]