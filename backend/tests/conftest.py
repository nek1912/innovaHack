"""Shared fixtures for the backend test suite.

Tests run against a dedicated Postgres database (agentfinance_test) with the
RazorpayX and OPA clients mocked — deterministic, no external services needed.

Environment is configured BEFORE any app import so the settings singleton
picks up test values.
"""

import os

os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://agentfinance:changeme@localhost:5432/agentfinance_test"
)
os.environ["JWT_SECRET"] = "test-secret-not-for-production-1234567890"
os.environ["RAZORPAY_MODE"] = "test"
os.environ["RAZORPAY_KEY_ID"] = "key_test"
os.environ["RAZORPAY_KEY_SECRET"] = "secret_test"
os.environ["RAZORPAY_WEBHOOK_SECRET"] = "whsec_test"
os.environ["RAZORPAY_DEBIT_IDENTIFIER"] = "acc_test"

import uuid  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

import asyncpg  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import Base, async_session, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.owner import Agent, Owner, Payee, Payout  # noqa: E402
from app.services.razorpayx import RazorpayXError  # noqa: E402

TEST_DB = "postgresql://agentfinance:changeme@localhost:5432/agentfinance_test"
ADMIN_DB = "postgresql://agentfinance:changeme@localhost:5432/postgres"


async def _ensure_test_db() -> None:
    try:
        conn = await asyncpg.connect(ADMIN_DB)
    except asyncpg.InvalidCatalogNameError:
        conn = await asyncpg.connect(TEST_DB)
    try:
        exists = await conn.fetchval(
            "select 1 from pg_database where datname = $1", "agentfinance_test"
        )
        if not exists:
            await conn.execute("CREATE DATABASE agentfinance_test")
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _database():
    await _ensure_test_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables(_database):
    async with engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE payouts, payees, agents, owners, audit_log RESTART IDENTITY CASCADE")
        )
    yield


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db():
    async with async_session() as session:
        yield session


class OPAStub:
    decision = {"allow": True, "requires_approval": False, "deny_reason": None}
    calls: list[dict] = []

    async def evaluate(self, input_data: dict) -> dict:
        self.calls.append(input_data)
        return dict(self.decision)


@pytest.fixture(autouse=True)
def mock_opa(monkeypatch):
    stub = OPAStub()
    stub.calls = []
    monkeypatch.setattr("app.services.opa_client.opa_client.evaluate", stub.evaluate)
    return stub


class RazorpayXStub:
    contact_id = "cnt_test"
    fund_account_id = "fa_test"
    payout = {"id": "pay_test", "status": "queued"}
    fetched = {"id": "pay_test", "status": "processed"}
    errors: dict[str, Exception] = {}
    calls: list[tuple] = []

    async def create_contact(self, name: str, contact_type: str = "customer") -> dict:
        self.calls.append(("create_contact", name))
        if "create_contact" in self.errors:
            raise self.errors["create_contact"]
        return {"id": self.contact_id, "name": name}

    async def create_fund_account(self, contact_id, account_type, **kwargs) -> dict:
        self.calls.append(("create_fund_account", contact_id, account_type))
        if "create_fund_account" in self.errors:
            raise self.errors["create_fund_account"]
        return {"id": self.fund_account_id, "account_type": account_type}

    async def create_payout(self, **kwargs) -> dict:
        self.calls.append(("create_payout", kwargs))
        if "create_payout" in self.errors:
            raise self.errors["create_payout"]
        return dict(self.payout)

    async def fetch_payout(self, payout_id: str) -> dict:
        self.calls.append(("fetch_payout", payout_id))
        if "fetch_payout" in self.errors:
            raise self.errors["fetch_payout"]
        return dict(self.fetched)


@pytest.fixture(autouse=True)
def mock_razorpayx(monkeypatch):
    stub = RazorpayXStub()
    stub.calls = []
    stub.errors = {}
    monkeypatch.setattr("app.services.razorpayx.razorpayx_client.create_contact", stub.create_contact)
    monkeypatch.setattr("app.services.razorpayx.razorpayx_client.create_fund_account", stub.create_fund_account)
    monkeypatch.setattr("app.services.razorpayx.razorpayx_client.create_payout", stub.create_payout)
    monkeypatch.setattr("app.services.razorpayx.razorpayx_client.fetch_payout", stub.fetch_payout)
    return stub


async def make_owner(client: httpx.AsyncClient, email: str | None = None) -> dict:
    """Register an owner via the API, return {token, email}."""
    email = email or f"owner-{uuid.uuid4()}@test.dev"
    res = await client.post(
        "/owner/register",
        json={"name": "Test Owner", "email": email, "password": "password123"},
    )
    assert res.status_code == 200, res.text
    return {"token": res.json()["access_token"], "email": email}


async def make_agent(client: httpx.AsyncClient, token: str, **caps) -> dict:
    body = {
        "name": f"agent-{uuid.uuid4().hex[:6]}",
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "approval_threshold_paise": 75000,
        **caps,
    }
    res = await client.post(
        "/owner/agents", json=body, headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200, res.text
    return res.json()


async def make_payee(client: httpx.AsyncClient, token: str, agent_id: str, **kw) -> dict:
    body = {"label": f"payee-{uuid.uuid4().hex[:6]}", "vpa": "payee@upi", **kw}
    res = await client.post(
        f"/owner/agents/{agent_id}/payees",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, res.text
    return res.json()


async def seed_payout(db, agent: Agent, payee: Payee, **kw) -> Payout:
    payout = Payout(
        agent_id=agent.id,
        payee_id=payee.id,
        amount_paise=kw.pop("amount_paise", 50000),
        mode=kw.pop("mode", "upi"),
        purpose=kw.pop("purpose", "test"),
        policy_decision=kw.pop("policy_decision", "allow"),
        razorpay_status=kw.pop("razorpay_status", None),
        razorpay_payout_id=kw.pop("razorpay_payout_id", None),
        created_at=kw.pop("created_at", datetime.now(timezone.utc)),
    )
    db.add(payout)
    await db.commit()
    return payout


async def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
