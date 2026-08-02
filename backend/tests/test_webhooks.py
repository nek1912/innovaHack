"""Webhook processing: signature, idempotency, unknown payouts (Part A)."""

import hashlib
import hmac
import json
import uuid

from sqlalchemy import select, func

from app.models.owner import AuditLog, Payout
from tests.conftest import auth_headers, make_agent, make_owner, make_payee, seed_payout


def _sign(body: bytes) -> str:
    return hmac.new(b"whsec_test", body, hashlib.sha256).hexdigest()


async def _post(client, payload: dict, secret: str = "whsec_test"):
    body = json.dumps(payload).encode()
    signature = _sign(body) if secret else "bad"
    return await client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": signature},
    )


def _event(event: str, payout_id: str, status_details: dict | None = None) -> dict:
    entity = {"id": payout_id, "status": event.split(".")[-1]}
    if status_details:
        entity["status_details"] = status_details
    return {"event": event, "payload": {"payout": {"entity": entity}}}


async def test_webhook_processed_updates_status(client, db):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])

    from app.models.owner import Agent, Payee

    agent_obj = await db.get(Agent, uuid.UUID(agent["id"]))
    payee_obj = await db.get(Payee, uuid.UUID(payee["id"]))
    payout = await seed_payout(
        db, agent_obj, payee_obj,
        razorpay_status="queued", razorpay_payout_id="pay_web_1",
    )

    res = await _post(client, _event("payout.processed", "pay_web_1", {"reason": "completed"}))
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    await db.refresh(payout)  # identity map holds stale state otherwise
    assert payout.razorpay_status == "processed"

    entries = (
        await db.execute(
            select(AuditLog).where(AuditLog.event_type == "payout_webhook")
        )
    ).scalars().all()
    assert len(entries) == 1
    assert entries[0].detail["new_status"] == "processed"
    assert entries[0].detail["status_details"] == {"reason": "completed"}


async def test_webhook_replay_is_idempotent(client, db):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    from app.models.owner import Agent, Payee

    agent_obj = await db.get(Agent, uuid.UUID(agent["id"]))
    payee_obj = await db.get(Payee, uuid.UUID(payee["id"]))
    payout = await seed_payout(db, agent_obj, payee_obj, razorpay_status="queued", razorpay_payout_id="pay_web_2")

    payload = _event("payout.processed", "pay_web_2")
    first = await _post(client, payload)
    second = await _post(client, payload)
    assert first.status_code == 200 and second.status_code == 200
    assert second.json()["status"] == "already_processed"

    count = (
        await db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.event_type == "payout_webhook")
        )
    ).scalar()
    assert count == 1


async def test_webhook_invalid_signature_rejected(client):
    body = json.dumps(_event("payout.processed", "pay_x")).encode()
    res = await client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": "not-the-hmac"},
    )
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "invalid_webhook_signature"


async def test_webhook_unknown_payout_audited(client, db):
    res = await _post(client, _event("payout.processed", "pay_unknown_999"))
    assert res.status_code == 200
    assert res.json()["status"] == "unknown_payout"

    entries = (
        await db.execute(
            select(AuditLog).where(AuditLog.event_type == "webhook_unknown_payout")
        )
    ).scalars().all()
    assert len(entries) == 1
    assert entries[0].detail["razorpay_payout_id"] == "pay_unknown_999"


async def test_webhook_malformed_payload(client):
    body = b"{not valid json"
    signature = _sign(body)
    res = await client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": signature}
    )
    assert res.status_code == 400
    assert res.json()["detail"]["error"] == "invalid_payload"


async def test_webhook_missing_payout_entity_ignored(client):
    res = await _post(client, {"event": "payout.processed", "payload": {}})
    assert res.status_code == 200
    assert res.json()["status"] == "ignored"


async def test_webhook_unknown_event_ignored(client, db):
    """An event type outside the payout status map is ignored, not applied."""
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    payee = await make_payee(client, owner["token"], agent["id"])
    from app.models.owner import Agent, Payee

    agent_obj = await db.get(Agent, uuid.UUID(agent["id"]))
    payee_obj = await db.get(Payee, uuid.UUID(payee["id"]))
    payout = await seed_payout(db, agent_obj, payee_obj, razorpay_status="queued", razorpay_payout_id="pay_web_3")

    res = await _post(client, _event("payment.captured", "pay_web_3"))
    assert res.status_code == 200
    assert res.json()["status"] == "ignored_event"

    await db.refresh(payout)
    assert payout.razorpay_status == "queued"  # unchanged
