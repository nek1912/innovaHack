"""Schema contract: backend responses match frontend TypeScript types."""

import uuid
from datetime import datetime, timezone

from tests.conftest import auth_headers, make_agent, make_owner, make_payee, seed_payout


async def _agent_payee(client):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    return owner, agent, payee


def _agent_headers(agent) -> dict:
    return {"X-Api-Key": agent["api_key"]}


# ---- AgentResponse fields ----


async def test_agent_response_has_all_frontend_fields(client):
    """AgentResponse must include all fields the frontend Agent type expects."""
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])

    # Frontend type: { id, name, status, per_tx_cap_paise, daily_cap_paise, approval_threshold_paise, api_key? }
    assert "id" in agent
    assert "name" in agent
    assert "status" in agent
    assert "per_tx_cap_paise" in agent
    assert "daily_cap_paise" in agent
    assert "approval_threshold_paise" in agent
    assert "api_key" in agent  # only on creation
    assert isinstance(agent["id"], str)
    assert isinstance(agent["per_tx_cap_paise"], int)


async def test_agent_get_response_omits_api_key(client):
    """GET /owner/agents/{id} should NOT include api_key (only creation returns it)."""
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])

    res = await client.get(
        f"/owner/agents/{agent['id']}",
        headers=await auth_headers(owner["token"]),
    )
    body = res.json()
    assert "api_key" not in body or body.get("api_key") is None


# ---- PayeeResponse fields ----


async def test_payee_response_has_all_frontend_fields(client):
    """PayeeResponse must include all fields the frontend Payee type expects."""
    owner, agent, payee = await _agent_payee(client)

    # Frontend type: { id, label, vpa, bank_account_number, bank_ifsc, active }
    assert "id" in payee
    assert "label" in payee
    assert "vpa" in payee
    assert "bank_account_number" in payee
    assert "bank_ifsc" in payee
    assert "active" in payee
    assert isinstance(payee["active"], bool)


# ---- PayoutDetail fields ----


async def test_payout_detail_has_all_frontend_fields(client, mock_opa, mock_razorpayx):
    """PayoutDetail must include all fields the frontend PayoutDetail type expects."""
    owner, agent, payee = await _agent_payee(client)
    mock_opa.decision = {"allow": False, "requires_approval": True, "deny_reason": None}

    await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent),
    )

    res = await client.get(
        "/owner/payouts",
        headers=await auth_headers(owner["token"]),
    )
    body = res.json()
    assert body["total"] >= 1
    p = body["payouts"][0]

    # Frontend type: { id, agent_id, agent_name, payee_id, payee_label, amount_paise, mode, purpose, policy_decision, policy_reason, razorpay_payout_id, razorpay_status, created_at }
    required_fields = [
        "id", "agent_id", "agent_name", "payee_id", "payee_label",
        "amount_paise", "mode", "policy_decision", "created_at",
    ]
    for field in required_fields:
        assert field in p, f"Missing field: {field}"

    assert isinstance(p["amount_paise"], int)
    assert isinstance(p["created_at"], str)


# ---- DashboardStats fields ----


async def test_dashboard_stats_has_all_frontend_fields(client, mock_opa):
    """DashboardStats must include all fields the frontend expects."""
    owner, agent, payee = await _agent_payee(client)

    res = await client.get(
        "/owner/stats",
        headers=await auth_headers(owner["token"]),
    )
    stats = res.json()

    # Frontend type fields
    required = [
        "total_agents", "active_agents", "frozen_agents", "total_payees",
        "today_spend_paise", "today_limit_paise", "pending_approvals",
        "failed_payouts", "payment_success_rate",
    ]
    for field in required:
        assert field in stats, f"Missing field: {field}"

    assert isinstance(stats["total_agents"], int)
    assert isinstance(stats["provider_configured"], bool)


# ---- PayoutResponse fields ----


async def test_payout_response_has_required_fields(client, mock_opa, mock_razorpayx):
    """PayoutResponse from request-payout must include id, status, policy_decision."""
    owner, agent, payee = await _agent_payee(client)

    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent),
    )
    body = res.json()
    assert "id" in body
    assert "status" in body
    assert "policy_decision" in body


# ---- OwnerToken fields ----


async def test_register_response_has_access_token(client):
    """Register endpoint returns { access_token, token_type }."""
    res = await client.post(
        "/owner/register",
        json={"name": "Schema Test", "email": f"schema-{uuid.uuid4()}@test.dev", "password": "password123"},
    )
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


# ---- Null safety ----


async def test_payout_with_null_purpose_rendered_safely(client, mock_opa, mock_razorpayx):
    """A payout with purpose=None should not crash the list endpoint."""
    owner, agent, payee = await _agent_payee(client)

    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 50000, "mode": "upi"},
        headers=_agent_headers(agent),
    )
    assert res.status_code == 200

    # List should handle null purpose gracefully
    list_res = await client.get(
        "/owner/payouts",
        headers=await auth_headers(owner["token"]),
    )
    assert list_res.status_code == 200
    for p in list_res.json()["payouts"]:
        assert "purpose" in p  # should be present, even if null


async def test_empty_agent_list_returns_empty_array(client):
    """Agent list for new owner returns empty array, not null."""
    owner = await make_owner(client)
    res = await client.get(
        "/owner/agents",
        headers=await auth_headers(owner["token"]),
    )
    assert res.status_code == 200
    assert res.json()["agents"] == []


async def test_empty_payout_list_returns_empty_array(client):
    """Payout list for new owner returns empty array with total=0."""
    owner = await make_owner(client)
    res = await client.get(
        "/owner/payouts",
        headers=await auth_headers(owner["token"]),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["payouts"] == []
    assert body["total"] == 0


async def test_empty_payee_list_returns_empty_array(client):
    """Payee list for agent with no payees returns empty array."""
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    res = await client.get(
        f"/owner/agents/{agent['id']}/payees",
        headers=await auth_headers(owner["token"]),
    )
    assert res.status_code == 200
    assert res.json()["payees"] == []
