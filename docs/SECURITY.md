# Security

## Verified posture (as of the Phase 5 audit)

### Fixed in this phase

- **IDOR — agent freeze/unfreeze** (`kill_switch.py`): the endpoint previously resolved the agent by ID without checking ownership. An owner could freeze another owner's agent. Now raises `agent_not_found` (identical to a missing agent — no existence oracle) when `agent.owner_id != owner.id`.
- **IDOR — audit log scoping** (`routers/audit.py`): the audit query was not owner-scoped; any owner could read any agent's audit trail. Now restricted to the owner's agents (plus global events), and an `agent_id` filter for a non-owned agent returns 404.
- **Registration input validation**: `/owner/register` previously took query parameters with no validation. Now `RegisterRequest` (name 1-200, email regex, password 8-128) via JSON body.
- **Payee input validation** (`schemas/payout.py`): `PayeeCreate` requires exactly one of VPA or bank account; `PayeeActiveUpdate` bounds `active` to a bool.
- **Payee activation state** is now an explicit owner-controlled flag (`PATCH .../payees/{id}`) with audit; an inactive payee is denied by policy.

### Already present and re-verified

- **Secrets**: passwords hashed (bcrypt-style), agent API keys stored as hash, JWT secret must not be the dev default (backend refuses to start in production mode with default), test-mode RazorpayX keys are not usable for live payouts.
- **Webhook signatures**: HMAC-SHA256 over the raw request body with `RAZORPAY_WEBHOOK_SECRET`; unknown events ignored; malformed payloads rejected.
- **Policy evaluation**: every payout is gated by OPA — freeze, per-tx cap, daily cap (IST), approval threshold, payee-active — before any provider call.
- **Idempotency**: 60-second duplicate window with a per-agent row lock (`SELECT ... FOR UPDATE`) against double-payment races.
- **Request IDs**: every request gets a UUID logged and echoed as `X-Request-Id`; audit entries carry it for correlation.
- **Immutable audit trail**: `AuditLog` rows are append-only by design; every decision/execution/webhook is recorded.

## Known limitations

- **Provider credentials**: test-mode RazorpayX keys (`rzp_test_*`) authorize sandbox payouts only. Live payouts additionally require `RAZORPAY_DEBIT_IDENTIFIER` (debit-fund account) to be set — until then provider payouts will 4xx.
- **Rate limiting**: none beyond the duplicate window — API keys can be used for moderate load; add per-key rate limiting before exposing publicly.
- **Frontend auth**: token stored in `localStorage` (XSS risk surface). Acceptable for this internal console; move to HttpOnly cookies for stronger protection.
- **OPA transport**: plain HTTP in dev (http://localhost:8181); use TLS/network isolation between backend and OPA in production.
- **JWT**: HS256 with a single shared secret; use RS256/ES256 with per-service keys for a multi-service deployment.
- **Audit immutability**: enforced by design (append-only writes), not by DB constraints — no trigger blocks manual `UPDATE`. Cryptographic chain-of-custody is out of scope.
- **Password policy**: length 8-128 only; no complexity/breach-list checks.

## Reporting

Report suspected vulnerabilities to the project owner with reproduction steps. Do not test against production RazorpayX.
