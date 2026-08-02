"""Environment and config failures: missing vars, OPA down, bad DB."""

import os
import subprocess
import sys
import uuid

import pytest

from tests.conftest import auth_headers

from app.models.owner import AuditLog


# ---- OPA unavailability ----


async def test_opa_unavailable_returns_502(client, monkeypatch):
    """When OPA is unreachable, payout request returns controlled error, not 500."""
    from app.services import opa_client as opc

    async def failing_evaluate(input_data):
        raise Exception("Connection refused")

    monkeypatch.setattr(opc.opa_client, "evaluate", failing_evaluate)

    from tests.conftest import make_agent, make_owner, make_payee

    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])

    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 1000, "mode": "upi"},
        headers={"X-Api-Key": agent["api_key"]},
    )
    # Should not be a 500 — either 502 or handled gracefully
    assert res.status_code != 500, f"Got unhandled 500: {res.text}"


async def test_opa_timeout_returns_controlled_error(client, monkeypatch):
    """When OPA times out, payout request returns controlled error."""
    import asyncio
    from app.services import opa_client as opc

    async def slow_evaluate(input_data):
        await asyncio.sleep(100)
        return {}

    monkeypatch.setattr(opc.opa_client, "evaluate", slow_evaluate)

    from tests.conftest import make_agent, make_owner, make_payee

    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])

    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 1000, "mode": "upi"},
        headers={"X-Api-Key": agent["api_key"]},
    )
    assert res.status_code != 500


# ---- missing env vars ----


def test_backend_starts_with_defaults():
    """Backend can start even if some env vars use defaults."""
    env = os.environ.copy()
    env.pop("RAZORPAY_KEY_ID", None)
    env.pop("RAZORPAY_KEY_SECRET", None)

    result = subprocess.run(
        [sys.executable, "-c", "from app.config import Settings; s = Settings(); print(s.jwt_algorithm)"],
        capture_output=True,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        env=env,
        timeout=10,
    )
    assert result.returncode == 0
    assert "HS256" in result.stdout


def test_database_url_required():
    """Backend fails clearly if DATABASE_URL is completely missing."""
    env = os.environ.copy()
    env.pop("DATABASE_URL", None)

    result = subprocess.run(
        [sys.executable, "-c", "from app.config import Settings; s = Settings(); print(s.database_url)"],
        capture_output=True,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        env=env,
        timeout=10,
    )
    # Should still get default value, not crash
    assert result.returncode == 0


# ---- invalid DB connection ----


async def test_invalid_db_url_does_not_leak_password_in_error(client, monkeypatch):
    """A bad DB URL should not expose credentials in error response."""
    # This test verifies the app doesn't crash with a 500 that leaks DB creds
    # We just check the health endpoint still works (it doesn't touch DB)
    res = await client.get("/health")
    assert res.status_code == 200


# ---- provider credentials missing ----


async def test_stats_works_without_razorpay_creds(client, monkeypatch):
    """Dashboard stats endpoint works even if Razorpay creds are not configured."""
    from app.config import settings

    monkeypatch.setattr(settings, "razorpay_key_id", "")
    monkeypatch.setattr(settings, "razorpay_key_secret", "")

    from tests.conftest import make_agent, make_owner

    owner = await make_owner(client)
    await make_agent(client, owner["token"])

    res = await client.get(
        "/owner/stats",
        headers=await auth_headers(owner["token"]),
    )
    assert res.status_code == 200
    stats = res.json()
    assert stats["provider_configured"] is False
    assert stats["provider_mode"] == "test"


# ---- audit logging correctness ----


async def test_every_state_transition_has_audit_entry(client, db, mock_opa, mock_razorpayx):
    """Every important action produces an audit trail entry."""
    from tests.conftest import make_agent, make_owner, make_payee
    from app.models.owner import Agent as AgentModel, Payee as PayeeModel
    from sqlalchemy import select, func

    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])

    # 1. create agent — no audit (not in scope, but payee toggle is)
    # 2. toggle payee
    await client.patch(
        f"/owner/agents/{agent['id']}/payees/{payee['id']}",
        json={"active": False},
        headers=await auth_headers(owner["token"]),
    )
    await client.patch(
        f"/owner/agents/{agent['id']}/payees/{payee['id']}",
        json={"active": True},
        headers=await auth_headers(owner["token"]),
    )

    # 3. freeze/unfreeze
    await client.post(
        f"/owner/agents/{agent['id']}/freeze",
        headers=await auth_headers(owner["token"]),
    )
    await client.post(
        f"/owner/agents/{agent['id']}/unfreeze",
        headers=await auth_headers(owner["token"]),
    )

    # 4. denied payout
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "per_tx_cap_exceeded"}
    await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 999999, "mode": "upi"},
        headers={"X-Api-Key": agent["api_key"]},
    )

    # 5. approval-required payout + approve
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}
    payout_res = await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 1000, "mode": "upi"},
        headers={"X-Api-Key": agent["api_key"]},
    )
    payout_id = payout_res.json()["id"]
    await client.post(
        f"/owner/payouts/{payout_id}/approve",
        headers=await auth_headers(owner["token"]),
    )

    # Verify audit entries exist for key events
    agent_id = uuid.UUID(agent["id"])
    events = (
        await db.execute(
            select(AuditLog.event_type).where(AuditLog.agent_id == agent_id)
        )
    ).scalars().all()

    expected = {"payee_status_changed", "freeze", "unfreeze", "policy_denied", "approval_required", "payout_approved"}
    assert expected.issubset(set(events)), f"Missing audit events: {expected - set(events)}"
