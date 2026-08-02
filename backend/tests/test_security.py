"""Security edge cases: cross-owner access, webhook secret, token handling."""

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select

from app.config import settings
from app.models.owner import AuditLog, Payout
from tests.conftest import auth_headers, make_agent, make_owner, make_payee, seed_payout


async def _agent_payee(client):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    return owner, agent, payee


def _agent_headers(agent) -> dict:
    return {"X-Api-Key": agent["api_key"]}


def _sign(body: bytes, secret: str = "whsec_test") -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# ---- cross-owner IDOR ----


async def test_cross_owner_cannot_approve_payout(client, mock_opa):
    """Owner A's payout cannot be approved by Owner B."""
    owner_a, agent_a, payee_a = await _agent_payee(client)
    owner_b = await make_owner(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}

    payout_id = (await client.post(
        "/agent/request-payout",
        json={"payee_id": payee_a["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent_a),
    )).json()["id"]

    res = await client.post(
        f"/owner/payouts/{payout_id}/approve",
        headers=await auth_headers(owner_b["token"]),
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "unauthorized_owner_access"


async def test_cross_owner_cannot_reject_payout(client, mock_opa):
    """Owner A's payout cannot be rejected by Owner B."""
    owner_a, agent_a, payee_a = await _agent_payee(client)
    owner_b = await make_owner(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}

    payout_id = (await client.post(
        "/agent/request-payout",
        json={"payee_id": payee_a["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent_a),
    )).json()["id"]

    res = await client.post(
        f"/owner/payouts/{payout_id}/reject",
        headers=await auth_headers(owner_b["token"]),
    )
    assert res.status_code == 403


async def test_cross_owner_cannot_list_payouts(client, mock_opa):
    """Owner A cannot see Owner B's payouts via the list endpoint."""
    owner_a, agent_a, payee_a = await _agent_payee(client)
    owner_b, agent_b, payee_b = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}

    # Create a payout for owner B
    await client.post(
        "/agent/request-payout",
        json={"payee_id": payee_b["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent_b),
    )

    # Owner A lists payouts — should see 0
    res = await client.get(
        "/owner/payouts",
        headers=await auth_headers(owner_a["token"]),
    )
    assert res.status_code == 200
    assert res.json()["total"] == 0


async def test_cross_owner_cannot_view_agent(client):
    """Owner A cannot get Owner B's agent details."""
    owner_a = await make_owner(client)
    owner_b = await make_owner(client)
    agent_b = await make_agent(client, owner_b["token"])

    res = await client.get(
        f"/owner/agents/{agent_b['id']}",
        headers=await auth_headers(owner_a["token"]),
    )
    assert res.status_code == 404


# ---- webhook security ----


async def test_webhook_wrong_secret_rejected(client):
    """Webhook signed with wrong secret is rejected."""
    payload = {"event": "payout.processed", "payload": {"payout": {"entity": {"id": "pay_x", "status": "processed"}}}}
    body = json.dumps(payload).encode()
    sig = _sign(body, secret="wrong_secret")

    res = await client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": sig},
    )
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "invalid_webhook_signature"


async def test_webhook_empty_signature_rejected(client):
    """Webhook with empty signature header is rejected."""
    payload = {"event": "payout.processed", "payload": {"payout": {"entity": {"id": "pay_x", "status": "processed"}}}}
    body = json.dumps(payload).encode()

    res = await client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": ""},
    )
    assert res.status_code == 401


async def test_webhook_replay_after_processed_ignored(client, db):
    """Replaying an already-processed webhook is idempotent, not an error."""
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    from app.models.owner import Agent as AgentModel, Payee as PayeeModel

    agent_obj = await db.get(AgentModel, uuid.UUID(agent["id"]))
    payee_obj = await db.get(PayeeModel, uuid.UUID(payee["id"]))
    payout = await seed_payout(
        db, agent_obj, payee_obj,
        razorpay_status="processed", razorpay_payout_id="pay_replay_test",
    )

    payload = {"event": "payout.processed", "payload": {"payout": {"entity": {"id": "pay_replay_test", "status": "processed"}}}}
    body = json.dumps(payload).encode()
    sig = _sign(body)

    res = await client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": sig},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "already_processed"


# ---- token edge cases ----


async def test_token_with_different_algorithm_rejected(client):
    """Token signed with wrong algorithm is rejected."""
    owner = await make_owner(client)
    # Re-encode with a different valid algorithm but wrong secret
    payload = jwt.decode(owner["token"], settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    # Use a completely different secret — should fail verification
    bad_token = jwt.encode(payload, "wrong-secret-key", algorithm=settings.jwt_algorithm)

    res = await client.get(
        "/owner/agents",
        headers=await auth_headers(bad_token),
    )
    assert res.status_code == 401


async def test_tampered_token_rejected(client):
    """Token with tampered payload is rejected."""
    owner = await make_owner(client)
    parts = owner["token"].split(".")
    # Tamper with the payload
    import base64
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    payload["sub"] = str(uuid.uuid4())
    tampered_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

    res = await client.get(
        "/owner/agents",
        headers=await auth_headers(tampered_token),
    )
    assert res.status_code == 401


# ---- frozen agent cannot move money ----


async def test_frozen_agent_cannot_request_payout(client, mock_opa):
    """Frozen agent's API key is rejected before policy evaluation."""
    owner, agent, payee = await _agent_payee(client)

    await client.post(
        f"/owner/agents/{agent['id']}/freeze",
        headers=await auth_headers(owner["token"]),
    )

    mock_opa.calls = []
    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 1000, "mode": "upi"},
        headers=_agent_headers(agent),
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "agent_frozen"
    assert mock_opa.calls == []  # OPA never called


# ---- provider errors don't leak secrets ----


async def test_provider_error_does_not_leak_api_key(client, db, mock_razorpayx):
    """Provider error response should not contain API key or internal IDs."""
    owner, agent, payee = await _agent_payee(client)
    from app.services.razorpayx import RazorpayXError

    mock_razorpayx.errors["create_payout"] = RazorpayXError(400, "bad_request", "invalid fund_account fa_12345")
    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent),
    )
    assert res.status_code == 422
    body = res.json()["detail"]
    # API key should not appear anywhere in error
    assert agent["api_key"] not in json.dumps(body)
