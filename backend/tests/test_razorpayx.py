"""RazorpayX client unit tests: mode mapping, error mapping, provider-id races."""

import uuid

import pytest
from sqlalchemy import select

from app.models.owner import Payee
from app.services.razorpayx import (
    MODE_MAP,
    RazorpayXError,
    _provider_error_status,
    ensure_payee_provider_ids,
)
from tests.conftest import auth_headers, make_agent, make_owner, make_payee


def test_mode_map_uppercase():
    assert MODE_MAP == {"upi": "UPI", "imps": "IMPS", "neft": "NEFT", "rtgs": "RTGS"}


def test_provider_error_status_mapping():
    status, code, msg = _provider_error_status(RazorpayXError(500, "server_error", "x"))
    assert (status, code) == (502, "provider_failure")
    assert "retry later" in msg

    status, code, msg = _provider_error_status(RazorpayXError(400, "bad_request", "invalid ifsc"))
    assert (status, code) == (422, "provider_rejected")
    assert "invalid ifsc" in msg


async def test_unsupported_mode_rejected(mock_razorpayx):
    from app.services.razorpayx import RazorpayXClient

    # fresh unpatched instance — validation happens before any network call
    client = RazorpayXClient()
    with pytest.raises(ValueError):
        await client.create_payout(
            fund_account_id="fa", amount_paise=100, mode="bitcoin",
            purpose="p", idempotency_key="k",
        )


async def test_ensure_payee_provider_ids_creates_and_reuses(client, db, mock_razorpayx):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee_resp = await make_payee(client, owner["token"], agent["id"])
    payee = await db.get(Payee, uuid.UUID(payee_resp["id"]))

    await ensure_payee_provider_ids(db, payee)
    assert payee.razorpay_contact_id == "cnt_test"
    assert payee.razorpay_fund_account_id == "fa_test"
    assert [c[0] for c in mock_razorpayx.calls] == ["create_contact", "create_fund_account"]

    # second run: ids present, no provider calls
    mock_razorpayx.calls = []
    await ensure_payee_provider_ids(db, payee)
    assert mock_razorpayx.calls == []


async def test_ensure_payee_provider_ids_adopts_concurrent_write(client, db, mock_razorpayx, monkeypatch):
    """Another request populated the IDs between our create and re-check:
    we must adopt theirs and not create a duplicate fund account."""
    import app.services.razorpayx as rzx

    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee_resp = await make_payee(client, owner["token"], agent["id"])
    payee = await db.get(Payee, uuid.UUID(payee_resp["id"]))

    async def racing_create_contact(name, contact_type="customer"):
        # simulate the concurrent request winning: it commits contact id,
        # which ensure_payee_provider_ids then sees after db.refresh
        payee.razorpay_contact_id = "cnt_concurrent"
        await db.commit()
        return {"id": "cnt_mine", "name": name}

    # patch the singleton attribute itself — the autouse stub is replaced for this test
    monkeypatch.setattr(rzx.razorpayx_client, "create_contact", racing_create_contact)
    await ensure_payee_provider_ids(db, payee)

    assert payee.razorpay_contact_id == "cnt_concurrent"  # adopted theirs, not "cnt_mine"
    # fund account created against the adopted contact, with no duplicate contact
    fund_call = [c for c in mock_razorpayx.calls if c[0] == "create_fund_account"]
    assert len(fund_call) == 1


async def test_ensure_payee_provider_ids_raises_provider_error(client, db, mock_razorpayx):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee_resp = await make_payee(client, owner["token"], agent["id"])
    payee = await db.get(Payee, uuid.UUID(payee_resp["id"]))

    mock_razorpayx.errors["create_contact"] = RazorpayXError(403, "forbidden", "IP not allowed")
    with pytest.raises(RazorpayXError):
        await ensure_payee_provider_ids(db, payee)
