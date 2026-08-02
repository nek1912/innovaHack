# Testing

## Backend (pytest) — 66 tests

```bash
cd backend
.venv\Scripts\python -m pytest tests -q
```

- **DB**: tests run against a real PostgreSQL database `agentfinance_test` (created automatically — the role needs `CREATEDB`). Schema is recreated per session; tables truncated per test.
- **External services are stubbed**: OPA (`OPAStub` fixture) and RazorpayX (`RazorpayXStub` fixture) are monkeypatched into the app's singletons, so tests are deterministic and offline. Provider error scenarios are driven by a stub `errors` dict.
- **Loop scope**: configured `session` for fixtures and tests (shared async engine); see `pyproject.toml`.
- Coverage: auth (register/login/key auth, validation), agent workflows (freeze IDOR, payee creation, toggle), payout workflows (allow/approval/deny paths, duplicate window, provider reuse), webhooks (signature, mapping, unknown events, malformed payload), reconciliation (provider truth, 404→stale, 5xx→skip), policy input (IST day boundary, spent computation), RazorpayX client (mode validation, concurrent payee adoption, typed timeouts).

## Policy (OPA) — 30 tests

```bash
tools\opa.exe test policy
```

Boundary cases: exact caps (per-tx, daily) and ±1 paise, approval threshold strictly-greater semantics, freeze overriding everything, `deny_reason` precedence (`agent_frozen` > `per_tx_cap_exceeded` > `daily_cap_exceeded` > `payee_inactive`), approval-vs-deny precedence.

## Frontend

- `npx tsc --noEmit` and `npx eslint app lib components` are clean.
- **No frontend unit tests** — deferred by project decision (no new test frameworks allowed in Phase 5). Manual QA path: login → create agent → create payee → exercise dashboard, approvals, payee toggle, audit filters.

## Full validation (Phase 5 gate)

```bash
cd backend; .venv\Scripts\python -m py_compile <changed files>
cd backend; .venv\Scripts\python -m pytest tests -q
tools\opa.exe test policy
cd frontend; npx tsc --noEmit; npx eslint app lib components; npm run build
cd backend; .venv\Scripts\python -m alembic check
```
