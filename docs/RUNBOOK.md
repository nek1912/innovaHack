# Runbook

## Services and ports

| Service | Port | Logs / notes |
|---|---|---|
| Frontend (Next.js) | 3000 | `npm run dev` in `frontend/` |
| Backend (FastAPI) | 8000 | structured request logs with `request_id` |
| OPA | 8181 | `opa run --server --watch` in repo root (`policy/` served) |
| PostgreSQL | 5432 | dev role: `agentfinance` / db `agentfinance` |

Windows convenience: `start_all.ps1`, `stop_all.ps1`.

## Day-to-day

- **Start everything**: `.\start_all.ps1`
- **Stop everything**: `.\stop_all.ps1`
- **Backend tests**: `cd backend; .venv\Scripts\python -m pytest tests -q`
- **Policy tests**: `tools\opa.exe test policy` (30 tests)
- **Migrations**: `cd backend; .venv\Scripts\python -m alembic upgrade head` (also `alembic check` after model edits)
- **Frontend checks**: `cd frontend; npx tsc --noEmit; npx eslint app lib components`

## Statuses you will see

- `queued` — provider accepted the payout; webhook may still arrive
- `processed` / `failed` / `reversed` — confirmed by webhook or reconciliation
- `stale` — provider no longer reports the payout after 15+ min in `queued`; **investigate manually** (was money moved?)
- `local_error` — provider call failed (timeout/network); **retry manually** via the approval/payout flow or refund checks
- `pending` — above approval threshold, waiting for owner
- `denied` — policy denial (reason in audit: `agent_frozen`, `per_tx_cap_exceeded`, `daily_cap_exceeded`, `payee_inactive`)

## Troubleshooting

### Payout stuck in `queued` > 15 min
Reconciliation runs every 10 min (APScheduler inside the backend process; restarts with it). Check:
1. `SELECT razorpay_status, razorpay_payout_id, created_at FROM payouts WHERE razorpay_status='queued' ORDER BY created_at DESC;`
2. Query the provider for that payout ID. If processed but DB stale → manually set `razorpay_status='processed'` and add an audit row.
3. If the provider never knew about it → it will flip to `stale`; do NOT blindly re-pay (double-payment risk). Confirm the money trail first.

### Webhook events not arriving
- Signature failures log `invalid_signature` — check `RAZORPAY_WEBHOOK_SECRET` matches the dashboard.
- The webhook URL must be reachable from the internet (tunnel in dev).

### OPA down / policy changed
- Backend responds `503`-class provider errors on evaluate failures — statuses stay `queued`/`pending`; nothing is paid out silently.
- After editing `policy/spend.rego`, OPA with `--watch` reloads automatically; else restart it.
- **Running an OPA instance without `--watch` serves a stale policy** — verify with `curl http://localhost:8181/v1/data/agent/spend` before trusting decisions.

### Agent payouts rejected unexpectedly
1. Check agent status (`frozen`?).
2. Check payee `active` flag.
3. Read the `policy_denied` audit entry — `detail.reason` names the violated rule.

### Reconciliation scheduler not running
It lives in the backend process (lifespan). If the backend runs without the lifespan (e.g., some test harnesses), no reconciliation happens. Restart the backend.

## Recovery drills

- **Wrong amount paid**: RazorpayX dashboard reversal → webhook flips status; audit both sides.
- **DB restored from backup**: re-apply `alembic upgrade head`; stale provider state is repaired by the next reconciliation run.
- **API key leaked**: delete/recreate the agent (key shown once at creation; hash stored), audit event on rotation.
