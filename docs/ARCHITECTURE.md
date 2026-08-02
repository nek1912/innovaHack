# Agent Finance Control System — Architecture

## System overview

A control plane for autonomous financial agents. Each agent holds spend limits and is identified by an API key. Payout requests are evaluated against a Rego policy in Open Policy Agent (OPA); allowed requests execute through RazorpayX (Razorpay Payouts); approvals, denials, executions and webhooks are written to an immutable audit log. A nightly-boundary scheduler reconciles payouts that were queued at the provider but never confirmed by webhook.

## Components

```
┌────────────┐   REST /1/agents/*      ┌──────────────────────┐
│ Agent      │ ──────────────────────► │  FastAPI backend      │
│ (automated)│                         │  ───────────────────  │
└────────────┘                         │  auth (JWT / API key) │
                                       │  policy gate → OPA    │
┌────────────┐   REST /owner/*         │  RazorpayX client     │
│ Owner web  │ ──────────────────────► │  webhook receiver     │
│ (frontend) │                         │  scheduler/reconciler │
└────────────┘                         └──┬───────┬───────┬────┘
                                          │       │       │
                                    ┌─────▼──┐ ┌──▼───┐ ┌─▼──────────┐
                                    │ OPA    │ │PostgreSQL │ RazorpayX │
                                    │ :8181  │ │  :5432    │  (API)    │
                                    └────────┘ └────────┘ └───────────┘
```

- **Frontend** — Next.js 16 app router (port 3000, `NEXT_PUBLIC_API_URL` → backend). Owner console: dashboard, agent management, payee management, approvals, audit log, settings.
- **Backend** — FastAPI (port 8000) with async SQLAlchemy (asyncpg), JWT auth for owners, API-key auth for agents, RazorpayX SDK calls, webhook signature verification, APScheduler-based reconciliation, request-ID middleware.
- **OPA** — policy server (port 8181). Policy: `policy/spend.rego`. The backend evaluates every payout request before touching the provider.
- **PostgreSQL** — system of record. Alembic migrations in `backend/alembic/versions/`.

## Backend layout

```
backend/
  app/
    main.py            # app factory, lifespan (scheduler), request-ID middleware
    config.py          # env loading (root .env), Settings model
    database.py        # async engine/session
    auth.py            # owner JWT + agent API-key auth dependencies
    models/            # SQLAlchemy models (owner, agent, payee, payout, audit)
    schemas/           # Pydantic request/response models
    routers/           # owner_admin, agent_actions, webhooks, audit
    services/          # policy_input, opa_client, razorpayx, reconciliation, kill_switch
  alembic/             # migrations
  tests/               # pytest suite
```

## Request flow (payout)

1. Agent calls `POST /1/agents/{id}/payouts` with `X-API-Key` + payout details.
2. Backend validates agent, checks duplicate-window (60s, row-locked), ensures payee has provider IDs (`ensure_payee_provider_ids`).
3. `build_policy_input` computes IST-day spent from `payouts` (status `processed` or `local_error`); OPA evaluates `allow` / `requires_approval` / `deny_reason`.
4. Decision:
   - `allow` → create payout at RazorpayX (mode `test` = sandbox simulation), persist payout `queued`, audit `provider_payout_created`.
   - `requires_approval` → persist `pending`, audit `approval_required`.
   - deny → persist `denied`, audit `policy_denied` with reason.
5. Webhook (payout.processed / failed / reversed) verifies HMAC signature, maps status to DB (`processed`, `failed`), audits `payout_webhook`.
6. Every 10 minutes the scheduler fetches provider status for payouts stuck in `queued` > 15 min (`reconcile_stale_payouts`), updating `processed` or marking `stale`.

## Key design decisions

- **OPA as policy engine** — spend limits, freeze status and approval thresholds are Rego rules with a tested `deny_reason` precedence: `agent_frozen` > `per_tx_cap_exceeded` > `daily_cap_exceeded` > `payee_inactive`.
- **Money as integer paise** everywhere (no floats).
- **Immutable audit log** — every policy decision, approval, execution, webhook and reconciliation writes an `AuditLog` row with request ID and detail JSON.
- **Idempotent provider integration** — payee contact/fund-account IDs stored on the payee row; concurrent adoption guarded by re-check after `db.refresh`.
- **Time zone** — all day-boundary math happens in IST (`policy/spend.rego` is time-zone agnostic; the backend converts).
