"""Credit policy integration tests.

These tests call opa_client.evaluate() with sample input documents.
NOTE: conftest stubs OPA to always return allow=True. The real policy
logic lives in policy/spend.rego and is exercised by policy/spend_test.rego.
These tests verify the client wiring, not the Rego logic itself.
"""

import pytest

from app.services.opa_client import opa_client


def _base_input(**overrides):
    doc = {
        "agent_status": "active",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": True,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {
            "has_credit": False,
            "available": 0,
            "reserved": 0,
            "status": "none",
        },
    }
    doc.update(overrides)
    return doc


@pytest.mark.asyncio
async def test_opa_deny_no_credit(mock_opa):
    """Test OPA denies when no credit account exists."""
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "credit_not_issued"}

    result = await opa_client.evaluate(_base_input())

    assert result["allow"] is False
    assert result["deny_reason"] == "credit_not_issued"


@pytest.mark.asyncio
async def test_opa_deny_credit_exhausted(mock_opa):
    """Test OPA denies when credit is exhausted."""
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "credit_exhausted"}

    result = await opa_client.evaluate(
        _base_input(credit={"has_credit": True, "available": 500, "reserved": 0, "status": "active"})
    )

    assert result["allow"] is False
    assert result["deny_reason"] == "credit_exhausted"


@pytest.mark.asyncio
async def test_opa_deny_credit_inactive(mock_opa):
    """Test OPA denies when credit account is frozen."""
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "credit_inactive"}

    result = await opa_client.evaluate(
        _base_input(credit={"has_credit": True, "available": 5000, "reserved": 0, "status": "frozen"})
    )

    assert result["allow"] is False
    assert result["deny_reason"] == "credit_inactive"


@pytest.mark.asyncio
async def test_opa_allow_with_credit(mock_opa):
    """Test OPA allows when credit is available and under caps."""
    mock_opa.decision = {"allow": True, "requires_approval": False, "deny_reason": None}

    result = await opa_client.evaluate(
        _base_input(credit={"has_credit": True, "available": 5000, "reserved": 0, "status": "active"})
    )

    assert result["allow"] is True


@pytest.mark.asyncio
async def test_opa_deny_precedence(mock_opa):
    """Test frozen agent denied before credit check."""
    mock_opa.decision = {"allow": False, "requires_approval": False, "deny_reason": "agent_frozen"}

    result = await opa_client.evaluate(
        _base_input(
            agent_status="frozen",
            credit={"has_credit": True, "available": 5000, "reserved": 0, "status": "active"},
        )
    )

    assert result["allow"] is False
    assert result["deny_reason"] == "agent_frozen"
