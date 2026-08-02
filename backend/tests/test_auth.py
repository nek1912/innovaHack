"""Auth workflows: registration, login, JWT, API keys (Part A)."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select

from app.auth import hash_api_key
from app.models.owner import Agent, Owner
from tests.conftest import auth_headers, make_agent, make_owner


@pytest.mark.asyncio
async def test_register_returns_token(client, db):
    email = f"reg-{uuid.uuid4()}@test.dev"
    res = await client.post(
        "/owner/register",
        json={"name": "Reg", "email": email, "password": "password123"},
    )
    assert res.status_code == 200
    assert res.json()["access_token"]

    owner = (await db.execute(select(Owner).where(Owner.email == email))).scalar_one()
    assert owner.password_hash != "password123"  # bcrypt-hashed
    assert owner.password_hash.startswith("$2")


@pytest.mark.asyncio
async def test_register_duplicate_email_conflict(client):
    email = f"dup-{uuid.uuid4()}@test.dev"
    body = {"name": "A", "email": email, "password": "password123"}
    assert (await client.post("/owner/register", json=body)).status_code == 200
    res = await client.post("/owner/register", json=body)
    assert res.status_code == 409
    assert res.json()["detail"]["error"] == "email_exists"


@pytest.mark.asyncio
async def test_register_rejects_weak_password(client):
    res = await client.post(
        "/owner/register",
        json={"name": "A", "email": f"weak-{uuid.uuid4()}@test.dev", "password": "short"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_rejects_bad_email(client):
    res = await client.post(
        "/owner/register",
        json={"name": "A", "email": "not-an-email", "password": "password123"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success_and_wrong_password(client):
    owner = await make_owner(client)
    ok = await client.post("/owner/login", json={"email": owner["email"], "password": "password123"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    bad = await client.post("/owner/login", json={"email": owner["email"], "password": "wrong"})
    assert bad.status_code == 401
    assert bad.json()["detail"]["error"] == "invalid_auth"


@pytest.mark.asyncio
async def test_missing_token(client):
    res = await client.get("/owner/agents")
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "missing_token"


@pytest.mark.asyncio
async def test_invalid_token(client):
    res = await client.get("/owner/agents", headers=await auth_headers("garbage.token.here"))
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "invalid_token"


@pytest.mark.asyncio
async def test_expired_token(client):
    from app.config import settings

    owner = await make_owner(client)
    expired = jwt.encode(
        {
            "sub": uuid.uuid4().hex,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    res = await client.get("/owner/agents", headers=await auth_headers(expired))
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "token_expired"


@pytest.mark.asyncio
async def test_api_key_auth_missing(client):
    res = await client.post(
        "/agent/request-payout", json={"payee_id": str(uuid.uuid4()), "amount_paise": 100, "mode": "upi"}
    )
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "missing_api_key"


@pytest.mark.asyncio
async def test_api_key_auth_invalid(client):
    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": str(uuid.uuid4()), "amount_paise": 100, "mode": "upi"},
        headers={"X-Api-Key": "af_wrongkey"},
    )
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "invalid_api_key"


@pytest.mark.asyncio
async def test_api_key_stored_hashed(client, db):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    stored = (await db.get(Agent, uuid.UUID(agent["id"]))).api_key_hash
    assert stored == hash_api_key(agent["api_key"])
    assert stored != agent["api_key"]


@pytest.mark.asyncio
async def test_frozen_agent_api_key_rejected(client):
    owner = await make_owner(client)
    agent = await make_agent(client, owner["token"])
    await client.post(
        f"/owner/agents/{agent['id']}/freeze", headers=await auth_headers(owner["token"])
    )
    res = await client.post(
        "/agent/request-payout",
        json={"payee_id": str(uuid.uuid4()), "amount_paise": 100, "mode": "upi"},
        headers={"X-Api-Key": agent["api_key"]},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "agent_frozen"


@pytest.mark.asyncio
async def test_owner_not_found_token(client):
    from app.config import settings

    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    res = await client.get("/owner/agents", headers=await auth_headers(token))
    assert res.status_code == 401
    assert res.json()["detail"]["error"] == "owner_not_found"
