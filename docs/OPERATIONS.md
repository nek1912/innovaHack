# Operations — Maintenance Guide

Companion to RUNBOOK.md for ongoing operation of the Agent Finance Control System.

## Backup / restore

- Daily `pg_dump` of the database is the minimum. Restore procedure: restore dump, then `alembic upgrade head` (migrations are the single source of schema truth).
- After a restore, payouts that were mid-flight at provider level self-heal on the next 10-minute reconciliation run (provider status wins where the DB is stale).

## Monitoring

- **Request logs**: backend emits structured logs with `request_id`; search by `request_id` to correlate a payout to its audit rows.
- **Watch counters**: `failed_payouts` (dashboard), `stale_payouts` (provider lost sight of a payout — manual money-trace needed), `local_error_payouts` (provider call failed — manual retry decision needed), `policy_violations`.
- **Scheduler health**: the reconciliation job runs in-process; if the backend restarts, the timer restarts with it. There is no external cron dependency.

## Capacity notes

- Indexes from migration 003 cover the hot queries: payouts by provider id, agent+created, status; payees by agent; agents by owner; audit by agent+created and event type.
- `AuditLog` grows unboundedly; plan retention/archival before long production runs.

## Change procedure

1. Edit policy → `tools\opa.exe test policy` (30 tests) → OPA `--watch` reloads; otherwise restart OPA.
2. Edit backend → run `pytest tests -q` (66 tests) → restart backend.
3. Edit models → `alembic revision --autogenerate` → review → `alembic upgrade head` → `alembic check`.
4. Edit frontend → `npx tsc --noEmit` + `npx eslint` → rebuild.

## Known operational gotchas

- OPA started without `--watch` serves a **stale policy** — verify loaded policy before trusting decisions.
- `RAZORPAY_DEBIT_IDENTIFIER` empty ⇒ live payouts fail at provider level (`local_error`); set it before going live.
- Webhook URL must be internet-reachable and the secret must match the RazorpayX dashboard, or events silently die with `invalid_signature`.
- Do not manually re-pay a `stale` payout without tracing the money first — double-payment risk is the system's hardest operational failure mode.
