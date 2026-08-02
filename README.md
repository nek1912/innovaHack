# Autonomous Agent Credit Platform

Mission-control dashboard for supervising autonomous AI agents that handle real money via RazorpayX. Owners set limits and policies, agents request payouts, OPA gates every transaction, and every action is audited.

**Credit-for-autonomous-agents control system** with underwriting, credit issuance, constrained spending, repayment tracking, risk scoring, and autonomous agent demo.

---

## Problem Statement

Autonomous AI agents increasingly need to move money — paying vendors, settling invoices, disbursing funds. But giving an agent unchecked access to a payment provider is a liability. This system solves that by:

1. **Issuing credit** after underwriting
2. **Enforcing credit limits** via OPA policy
3. **Reserving credit** before payout execution
4. **Tracking repayment** with mandate-ready schema
5. **Scoring risk** and freezing on default

---

## Features

### Credit System

- Credit accounts with limit/available/used/reserved
- Append-only credit transaction ledger
- Underwriting engine (explainable scoring)
- Credit reservation before payout
- Credit release on provider failure
- Credit commit on success
- Repayment schedule (mandate-ready schema)
- Simulated manual repayment
- Risk scoring per agent
- Default handling with agent freeze
- OPA credit checks (7 deny reasons)

### Autonomous Agent Demo

- Groq LLM integration for autonomous decisions
- Constrained system prompt (agent cannot approve/modify policies)
- 5 demo tasks covering all scenarios
- Timeline UI showing agent reasoning
- PS evaluation mapping

### Finance Control

- Owner authentication (JWT)
- Agent API key authentication
- Payee management
- OPA policy enforcement
- Approval workflow
- Kill switch (freeze/unfreeze)
- RazorpayX test integration
- Webhook signature verification
- Reconciliation
- Rate limiting
- Audit logging

---

## Architecture

```
Owner (Sarah)
    ↓
Creates Agent (Procurement Agent)
    ↓
Issues Credit (₹10,000)
    ↓
Starts Agent Demo
    ↓
Agent (Groq LLM)
    ↓
Reasons about task
    ↓
Calls request_payout()
    ↓
Backend authenticates
    ↓
OPA evaluates (credit + caps)
    ↓
Credit reserved
    ↓
RazorpayX Test Mode
    ↓
Webhook received
    ↓
Credit committed
    ↓
Audit logged
    ↓
Timeline updated
```

### Request Flow

1. Owner creates agent and issues credit
2. Agent requests payout (API key auth)
3. Backend builds policy input with credit data
4. OPA evaluates: allow / requires_approval / deny
5. Allow → reserve credit → RazorpayX executes → commit credit
6. Approval required → pending payout, owner approves
7. Deny → request blocked, reason logged
8. Provider failure → release credit reservation
9. Webhook confirms result
10. Reconciliation verifies stuck payouts
11. Every transition written to audit log

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4 |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Database | PostgreSQL 16 (asyncpg) |
| Policy Engine | Open Policy Agent (OPA), Rego |
| Payments | RazorpayX API (UPI, IMPS, NEFT, RTGS) |
| AI Agent | Groq LLM (llama-3.3-70b-versatile) |
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
│   │   ├── models/
│   │   │   ├── owner.py         # Owner, Agent, Payee, Payout, AuditLog
│   │   │   └── credit.py        # CreditAccount, CreditTransaction, CreditDecision, RepaymentSchedule
│   │   ├── routers/
│   │   │   ├── owner_admin.py   # Owner endpoints
│   │   │   ├── agent_payouts.py # Agent payout request
│   │   │   ├── credit.py        # Credit issue, repay, history
│   │   │   ├── credit_admin.py  # Credit freeze/unfreeze, dashboard
│   │   │   ├── agent_demo.py    # Autonomous agent demo
│   │   │   ├── audit.py         # Audit log viewer
│   │   │   └── webhooks.py      # RazorpayX webhook
│   │   └── services/
│   │       ├── razorpayx.py     # RazorpayX client
│   │       ├── opa_client.py    # OPA HTTP client
│   │       ├── policy_input.py  # Builds OPA input with credit
│   │       ├── credit_engine.py # Credit issue/reserve/commit/release
│   │       ├── underwriting.py  # Credit scoring
│   │       ├── repayment.py     # Repayment schedule + scheduler
│   │       ├── risk.py          # Risk scoring
│   │       ├── agent_service.py # Groq LLM integration
│   │       ├── agent_tools.py   # Safe tool wrappers
│   │       ├── demo_tasks.py    # Demo task catalog
│   │       ├── reconciliation.py# Background reconciliation
│   │       └── kill_switch.py   # Freeze/unfreeze
│   ├── tests/                   # 120+ automated tests
│   └── alembic/                 # 5 applied migrations
├── frontend/
│   ├── app/
│   │   ├── dashboard/           # Main dashboard
│   │   ├── credit/              # Credit dashboard
│   │   │   ├── [agentId]/       # Credit account detail
│   │   │   │   ├── underwriting/
│   │   │   │   └── repayments/
│   │   │   └── risk/            # Risk dashboard
│   │   ├── agent-demo/          # Autonomous agent demo
│   │   ├── agents/              # Agent management
│   │   ├── audit/               # Audit log viewer
│   │   └── settings/            # System settings
│   ├── components/
│   │   ├── AgentTimeline.tsx    # Agent activity timeline
│   │   ├── CreditCard.tsx       # Credit balance display
│   │   ├── CreditTimeline.tsx   # Transaction history
│   │   ├── RepaymentTable.tsx   # Repayment list
│   │   ├── RiskGauge.tsx        # Risk score visualization
│   │   └── UnderwritingFactors.tsx
│   └── lib/api.ts              # Typed API client
├── policy/
│   ├── spend.rego               # OPA policy with credit checks
│   └── spend_test.rego          # 35 OPA tests
└── docs/                        # Architecture, API, security docs
```

---

## Security Features

- **JWT Authentication** — Owner tokens with 24h expiry
- **API Key Auth** — SHA-256 hashed, never returned after creation
- **Owner Isolation** — Every endpoint verifies ownership, cross-owner returns 404
- **Kill Switch** — Freeze agent → blocked at auth and policy layers
- **Rate Limiting** — 20 requests/60s per API key on payout endpoint
- **Duplicate Detection** — 60s window for identical requests
- **Row Locking** — `SELECT FOR UPDATE` serializes concurrent requests
- **Webhook Verification** — HMAC-SHA256 with constant-time comparison
- **Structured Errors** — Provider errors sanitized, no secrets leaked
- **Audit Trail** — Every financial transition recorded
- **OPA Policy Enforcement** — All decisions gated through policy engine
- **Credit Guards** — No spending without credit, reservation before payout

---

## OPA Policy Deny Reasons

| Reason | Description |
|--------|-------------|
| `agent_frozen` | Agent is frozen |
| `credit_not_issued` | No credit account exists |
| `credit_inactive` | Credit account is frozen |
| `per_tx_cap_exceeded` | Amount exceeds per-transaction cap |
| `daily_cap_exceeded` | Daily spending cap exceeded |
| `payee_inactive` | Payee is not active |
| `credit_exhausted` | Insufficient available credit |

---

## Testing

| Category | Count |
|----------|-------|
| Backend pytest tests | 120+ |
| OPA policy tests | 35 |
| **Total** | **155+** |

**Test categories:**
- Credit engine (issue, reserve, commit, release, concurrent)
- Credit policy (no credit, exhausted, inactive, allow, precedence)
- Repayment (create, manual pay, scheduler, default)
- Credit flow (full, provider failure, default)
- Authentication (register, login, JWT, API keys)
- Payout workflows (allow/deny/approval paths)
- Webhooks (signature, idempotency)
- Security (IDOR, token tampering, frozen agents)
- Race conditions (concurrent payouts)

**Run tests:**
```bash
# Backend
cd backend
python -m pytest tests/ -v

# OPA policies
cd policy
.\tools\opa.exe test . -v
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `OPA_URL` | OPA server URL | `http://localhost:8181` |
| `RAZORPAY_MODE` | `test` or `live` | `test` |
| `RAZORPAY_KEY_ID` | Razorpay API key ID | (required) |
| `RAZORPAY_KEY_SECRET` | Razorpay API key secret | (required) |
| `RAZORPAY_WEBHOOK_SECRET` | Webhook signature secret | (required) |
| `JWT_SECRET` | JWT signing secret | `dev-secret-change-in-production` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `GROQ_API_KEY` | Groq LLM API key | (required for agent demo) |

---

## API Endpoints

### Owner Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/owner/register` | Register owner |
| `POST` | `/owner/login` | Login, get JWT |
| `POST` | `/owner/agents` | Create agent |
| `POST` | `/owner/agents/{id}/freeze` | Freeze agent |
| `POST` | `/owner/agents/{id}/payees` | Add payee |
| `POST` | `/owner/payouts/{id}/approve` | Approve payout |
| `POST` | `/owner/payouts/{id}/reject` | Reject payout |

### Credit Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/credit/issue` | Issue credit to agent |
| `POST` | `/credit/repay` | Process manual repayment |
| `GET` | `/credit/account/{agent_id}` | Get credit account |
| `GET` | `/credit/history/{agent_id}` | Get transaction history |
| `GET` | `/credit/score/{agent_id}` | Get credit score |
| `GET` | `/credit/repayments/{agent_id}` | Get repayment schedule |
| `POST` | `/credit/create-repayment` | Create repayment schedule |
| `POST` | `/owner/credit/freeze/{agent_id}` | Freeze credit |
| `POST` | `/owner/credit/unfreeze/{agent_id}` | Unfreeze credit |
| `GET` | `/owner/credit/dashboard` | Credit dashboard summary |
| `GET` | `/owner/credit/risk` | Risk summary |

### Agent Demo Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/agent-demo/tasks` | List demo tasks |
| `POST` | `/agent-demo/execute` | Execute demo task |
| `GET` | `/agent-demo/tools/payees/{id}` | List payees |
| `GET` | `/agent-demo/tools/credit/{id}` | Check credit |
| `GET` | `/agent-demo/tools/status/{id}` | Get agent status |

### Agent Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/agent/request-payout` | Request payout |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/audit` | Filterable audit log |
| `POST` | `/webhooks/razorpay` | RazorpayX webhook |
| `GET` | `/health` | Health check |

---

## Demo Scenarios

| Scenario | Expected Result | PS Criterion |
|----------|----------------|--------------|
| Buy GPU Compute (₹1200) | Approved | Trust Design |
| Purchase Dataset (₹3500) | Approval Required | Repayment/Credit |
| Purchase Hardware (Unknown) | Rejected | Risk Containment |
| API Subscription (₹600) | Approved | Technical Soundness |
| Emergency Compute (₹15000) | Credit Exhausted | Risk Containment |

---

## Deployment

### Render

1. Connect GitHub repository
2. Set environment variables
3. Clear build cache on first deploy
4. Deploy

### Docker

```bash
docker build -t agent-finance .
docker run -p 8000:8000 agent-finance
```

---

## Current Limitations

- RazorpayX test mode only — no live payments
- Repayment is simulated (owner-initiated)
- No real NACH/e-mandate collection
- Single-process rate limiting (in-memory)
- No frontend automated tests

---

## Production Readiness

Although this is a demo:

- All backend APIs are production-quality
- All security checks are enabled
- Audit logging is complete
- RazorpayX Test Mode only
- Schema is mandate-ready for future automated collection
- Repayment execution is simulated (documented limitation)

---

## License

MIT
