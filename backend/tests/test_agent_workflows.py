"""Agent & payee management workflows, including ownership (IDOR) guards."""

import uuid
from sqlalchemy import select

from app.models.owner import AuditLog, Payee
from tests.conftest import auth_headers, make_agent, make_owner, make_payee


async def _second_owner_and_agent(client):
    other = await make_owner(client)
    other_agent = await make_agent(client, other["token"])
    return other, other_agent


async def test_create_agent_returns_api_key_once(client):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    assert agent["api_key"].startswith("af_")
    assert agent["status"] == "active"
    assert agent["per_tx_cap_paise"] == 100000


async def test_list_agents_scoped_to_owner(client):
    owner_a = await make_owner(client)
    owner_b = await make_owner(client)
    await make_agent(client, owner_a["token"])
    await make_agent(client, owner_a["token"])
    await make_agent(client, owner_b["token"])

    res = await client.get("/owner/agents", headers=await auth_headers(owner_a["token"]))
    assert len(res.json()["agents"]) == 2


async def test_get_other_owners_agent_is_404(client):
    owner = await make_owner(client)
    other, other_agent = await _second_owner_and_agent(client)
    res = await client.get(
        f"/owner/agents/{other_agent['id']}", headers=await auth_headers(owner["token"])
    )
    assert res.status_code == 404


async def test_freeze_and_unfreeze_own_agent(client, db):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])

    res = await client.post(
        f"/owner/agents/{agent['id']}/freeze", headers=await auth_headers(owner["token"])
    )
    assert res.status_code == 200
    assert res.json()["status"] == "frozen"

    res = await client.post(
        f"/owner/agents/{agent['id']}/unfreeze", headers=await auth_headers(owner["token"])
    )
    assert res.status_code == 200
    assert res.json()["status"] == "active"

    events = (
        await db.execute(
            select(AuditLog.event_type).where(AuditLog.agent_id == uuid.UUID(agent["id"]))
        )
    ).scalars().all()
    assert "freeze" in events and "unfreeze" in events


async def test_freeze_other_owners_agent_blocked(client, db):
    owner = await make_owner(client)
    other, other_agent = await _second_owner_and_agent(client)
    res = await client.post(
        f"/owner/agents/{other_agent['id']}/freeze", headers=await auth_headers(owner["token"])
    )
    assert res.status_code == 404

    # no freeze audit event recorded for that agent
    events = (
        await db.execute(
            select(AuditLog.event_type).where(AuditLog.agent_id == uuid.UUID(other_agent["id"]))
        )
    ).scalars().all()
    assert "freeze" not in events


async def test_create_payee_vpa_and_bank(client, db):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])

    vpa_payee = await make_payee(client, owner["token"], agent["id"])
    assert vpa_payee["vpa"] == "payee@upi"

    bank = await client.post(
        f"/owner/agents/{agent['id']}/payees",
        json={"label": "Bank", "bank_account_number": "1234567890", "bank_ifsc": "HDFC0001234"},
        headers=await auth_headers(owner["token"]),
    )
    assert bank.status_code == 200
    assert bank.json()["bank_ifsc"] == "HDFC0001234"

    assert (await db.execute(select(Payee))).scalars().all().__len__() == 2


async def test_create_payee_requires_destination(client):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    res = await client.post(
        f"/owner/agents/{agent['id']}/payees",
        json={"label": "NoDetails"},
        headers=await auth_headers(owner["token"]),
    )
    assert res.status_code == 422


async def test_create_payee_under_other_owners_agent_blocked(client):
    owner = await make_owner(client)
    other, other_agent = await _second_owner_and_agent(client)
    res = await client.post(
        f"/owner/agents/{other_agent['id']}/payees",
        json={"label": "Sneaky", "vpa": "sneaky@upi"},
        headers=await auth_headers(owner["token"]),
    )
    assert res.status_code == 404


async def test_payee_deactivate_and_inactive_block(client):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])

    # deactivate via the toggle endpoint
    res = await client.patch(
        f"/owner/agents/{agent['id']}/payees/{payee['id']}",
        json={"active": False},
        headers=await auth_headers(owner["token"]),
    )
    assert res.status_code == 200
    assert res.json()["active"] is False

    # payout request to inactive payee is blocked before policy
    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": payee["id"], "amount_paise": 1000, "mode": "upi"},
        headers={"X-Api-Key": agent["api_key"]},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "payee_inactive"

    # other owner cannot toggle this payee
    other = await make_owner(client)
    res = await client.patch(
        f"/owner/agents/{agent['id']}/payees/{payee['id']}",
        json={"active": True},
        headers=await auth_headers(other["token"]),
    )
    assert res.status_code == 404
