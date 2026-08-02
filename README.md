# Agent Finance Control System

Mission-control dashboard for supervising autonomous AI agents that handle real money via RazorpayX. Owners set limits and policies, agents request payouts, OPA gates every transaction, and every action is audited.

---

## Problem Statement

Autonomous AI agents increasingly need to move money — paying vendors, settling invoices, disbursing funds. But giving an agent unchecked access to a payment provider is a liability. This system solves that by placing a policy engine (OPA) between every payout request and execution, with owner approval thresholds, per-transaction and daily spending caps, a kill switch, and a full audit trail.

---

## Features

### Implemented

- Owner authentication (register/login, JWT)
- Agent management (create, freeze/unfreeze, API key generation)
- Payee management (add, activate/deactivate, VPA or bank account)
- OPA policy enforcement (per-tx cap, daily cap, approval threshold, frozen agent, inactive payee)
- Approval workflow (pending payouts require owner approve/reject)
- Kill switch (freeze agent → all requests blocked immediately)
- Audit logging (every financial transition recorded with request ID and actor)
- RazorpayX test integration (contacts, fund accounts, payouts)
- Webhook signature verification (HMAC-SHA256, idempotent processing)
- Reconciliation (background job, provider truth, retry cap, stale marking)
- Rate limiting (20 requests/60s per API key on payout endpoint)
- Dashboard with live polling (30s auto-refresh)
- Payout request form (owner-initiated via frontend)
- Toast notification system
- Error boundary with retry
- Health check (DB + OPA dependency checks)
- CORS from environment variable
- 102 automated tests + 30 OPA policy tests

### Not Yet Implemented

- Credit ledger and credit accounts
- Repayment engine
- Underwriting and risk scoring
- Production RazorpayX mode
- Frontend automated tests
- Multi-currency support
- Agent-to-agent transfers

---

## Architecture

```
Owner → Frontend (Next.js 16) → FastAPI Backend → OPA Policy Engine → RazorpayX (Test)
                                    ↓
                               PostgreSQL
                                    ↓
                              Audit Dashboard
```

**Request flow:**

1. Owner creates agent and payees via frontend
2. Agent requests payout (API key auth)
3. Backend builds policy input from live DB state
4. OPA evaluates: allow / requires_approval / deny
5. Allow → RazorpayX executes payout
6. Approval required → pending payout, owner approves from dashboard
7. Deny → request blocked, reason logged
8. RazorpayX webhook confirms result
9. Reconciliation verifies stuck payouts every 10 minutes
10. Every transition written to audit log

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4 |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Database | PostgreSQL 16 (asyncpg) |
| Policy Engine | Open Policy Agent (OPA), Rego |
| Payments | RazorpayX API (UPI, IMPS, NEFT, RTGS) |
| Auth | JWT (HS256), bcrypt passwords, SHA-256 API keys |

---

## Project Structure

```
agent-finance/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, health
│   │   ├── config.py            # Pydantic settings
│   │   ├── auth.py              # JWT + API key auth
│   │   ├── deps.py              # Audit, rate limit, IST helpers
│   │   ├── models/owner.py      # Owner, Agent, Payee, Payout, AuditLog
│   │   ├── schemas/payout.py    # Request/response models
│   │   ├── routers/
│   │   │   ├── owner_admin.py   # 15 owner endpoints
│   │   │   ├── agent_payouts.py # Agent payout request
│   │   │   ├── audit.py         # Audit log viewer
│   │   │   └── webhooks.py      # RazorpayX webhook
│   │   └── services/
│   │       ├── razorpayx.py     # RazorpayX client
│   │       ├── opa_client.py    # OPA HTTP client
│   │       ├── policy_input.py  # Builds OPA input
│   │       ├── reconciliation.py# Background reconciliation
│   │       └── kill_switch.py   # Freeze/unfreeze
│   ├── tests/                   # 102 automated tests
│   └── alembic/                 # 4 applied migrations
├── frontend/
│   ├── app/                     # Next.js pages
│   ├── components/              # UI components
│   └── lib/api.ts              # Typed API client
├── policy/
│   ├── spend.rego               # OPA policy
│   └── spend_test.rego          # 30 OPA tests
└── docs/                        # Architecture, API, security docs
```

---

## Security Features

- **JWT Authentication** — Owner tokens with 24h expiry
- **API Key Auth** — SHA-256 hashed, never returned after creation
- **Owner Isolation** — Every endpoint verifies `agent.owner_id == owner.id`, cross-owner access returns 404
- **Kill Switch** — Freeze agent → blocked at auth and policy layers
- **Rate Limiting** — 20 requests/60s per API key on payout endpoint
- **Duplicate Detection** — 60s window for identical agent+payee+amount requests
- **Row Locking** — `SELECT FOR UPDATE` serializes concurrent payout requests per agent
- **Webhook Verification** — HMAC-SHA256 signature with constant-time comparison
- **Structured Errors** — Provider errors sanitized, no API keys leaked
- **Audit Trail** — Every financial transition recorded with request ID and actor
- **OPA Policy Enforcement** — All payout decisions gated through policy engine

---

## Testing

| Category | Count |
|----------|-------|
| Backend pytest tests | 102 |
| OPA policy tests | 30 |
| **Total** | **132** |

**Test categories:**
- Authentication (registration, login, JWT, API keys, frozen agents)
- Agent workflows (CRUD, IDOR guards, freeze/unfreeze)
- Payout workflows (allow/deny/approval paths, provider failures, stats)
- Policy input (daily spend aggregation, IST boundaries)
- Webhooks (signature, idempotency, unknown payouts, malformed payloads)
- Security (cross-owner IDOR, token tampering, frozen agents, provider error leaks)
- RazorpayX (mode mapping, error mapping, provider-ID races)
- Reconciliation (provider truth, stale marking, 5xx skip)
- Race conditions (concurrent payouts, double approve, webhook timing)
- Environment failures (OPA down, missing env, audit coverage)
- Schema contracts (backend response fields match frontend TypeScript types)

**Run tests:**
```bash
# Backend
cd backend
.\.venv\Scripts\activate
python -m pytest tests/ -v

# OPA policies
cd policy
.\tools\opa.exe test . -v
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://agentfinance:changeme@localhost:5432/agentfinance` |
| `OPA_URL` | OPA server URL | `http://localhost:8181` |
| `RAZORPAY_MODE` | `test` or `live` | `test` |
| `RAZORPAY_KEY_ID` | Razorpay API key ID | (required) |
| `RAZORPAY_KEY_SECRET` | Razorpay API key secret | (required) |
| `RAZORPAY_WEBHOOK_SECRET` | Webhook signature secret | (required for webhooks) |
| `RAZORPAY_DEBIT_IDENTIFIER` | RazorpayX payout source account | (required for payouts) |
| `JWT_SECRET` | JWT signing secret | `dev-secret-change-in-production` |
| `JWT_EXPIRE_MINUTES` | Token expiry | `1440` (24h) |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend | `http://localhost:8000` |

---

## Local Development

**Prerequisites:** Python 3.11+, Node.js 18+, PostgreSQL 16, OPA binary

```bash
# 1. Clone and setup
git clone https://github.com/nek1912/innovaHack.git
cd innovaHack

# 2. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
alembic upgrade head

# 3. Start services (from project root)
.\start_all.ps1    # Starts OPA, backend, frontend, tunnel
```

**Or manually:**
```bash
# Terminal 1 — OPA
.\tools\opa.exe run --server --addr :8181

# Terminal 2 — Backend
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 3 — Frontend
cd frontend
npm install
npm run dev
```

**Stop all:**
```bash
.\stop_all.ps1
```

---

## API Documentation

Swagger UI available at: `http://localhost:8000/docs`

ReDoc available at: `http://localhost:8000/redoc`

**Key endpoints:**

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/owner/register` | None | Register owner account |
| `POST` | `/owner/login` | None | Login, get JWT |
| `POST` | `/owner/agents` | JWT | Create agent, get API key |
| `POST` | `/owner/agents/{id}/freeze` | JWT | Freeze agent (kill switch) |
| `POST` | `/owner/agents/{id}/payees` | JWT | Add payee |
| `POST` | `/owner/agents/{id}/payouts` | JWT | Request payout (owner) |
| `POST` | `/owner/payouts/{id}/approve` | JWT | Approve pending payout |
| `POST` | `/owner/payouts/{id}/reject` | JWT | Reject pending payout |
| `POST` | `/agent/request-payout` | API Key | Request payout (agent) |
| `GET` | `/audit` | JWT | Filterable audit log |
| `POST` | `/webhooks/razorpay` | HMAC | RazorpayX webhook |
| `GET` | `/health` | None | Health check (DB + OPA) |

---

## Current Limitations

- RazorpayX test mode only — no live payments
- Credit engine stubs exist but not integrated
- No repayment or collection workflow
- No underwriting or risk scoring
- No frontend automated tests
- No multi-currency support
- Single-process rate limiting (in-memory, not Redis)

---

## Future Roadmap

- Credit ledger with reserve/commit/release flow
- Repayment engine with NACH collection
- Risk scoring and underwriting
- Agent-to-agent transfers
- Multi-owner support with team roles
- Production RazorpayX integration
- Frontend E2E tests
- Redis-backed rate limiting

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## License

MIT
