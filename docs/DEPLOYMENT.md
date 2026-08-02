# Deployment

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- OPA binary (see `tools/` — the repo ships `opa.exe` for Windows; on other platforms download from openpolicyagent.org and put it on `PATH`, or set `OPA_URL` to a remote server)

## 1. Environment

Copy `.env.example` to `.env` at the repo root (shared by backend and frontend tooling) and set:

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` |
| `JWT_SECRET` | ≥ 32 random bytes, base64/hex — **never** the dev default |
| `RAZORPAY_MODE` | `test` (sandbox, no real money) or `live` |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | RazorpayX API keys |
| `RAZORPAY_WEBHOOK_SECRET` | webhook signing secret |
| `RAZORPAY_DEBIT_IDENTIFIER` | live-only: the debit fund account for payouts |
| `OPA_URL` | `http://localhost:8181` |
| `NEXT_PUBLIC_API_URL` | frontend → backend base URL |

## 2. Database

```bash
cd backend
.venv\Scripts\python -m pip install -r requirements.txt   # or sync uv.lock
.venv\Scripts\python -m alembic upgrade head
```

## 3. OPA

```bash
opa run --server --watch --set "decision_logs.console=true" policy/
```

`--watch` reloads `spend.rego`/`spend_test.rego` on change. Verify:

```bash
opa test policy/          # 30 tests
curl http://localhost:8181/v1/data/agent/spend -d '{"input": {...}}'
```

## 4. Backend

```bash
cd backend
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 5. Frontend

```bash
cd frontend
npm install
npm run build && npm start   # or npm run dev
```

## 6. Webhook

In the RazorpayX dashboard, point payout webhooks at `https://<host>/webhooks/razorpay` with the signing secret. For local dev, expose the backend via a tunnel (the repo root has `tunnel_output.txt` from previous dev tunnel use).

## Windows one-shot

`start_all.ps1` launches OPA (with `--watch`), backend, and frontend. `stop_all.ps1` stops them.

## Production checklist

- [ ] `JWT_SECRET` replaced with strong random value
- [ ] `RAZORPAY_MODE=live` and `RAZORPAY_DEBIT_IDENTIFIER` set
- [ ] Webhook secret set and dashboard webhook registered over HTTPS
- [ ] Backend/OPA traffic on a private network (or mTLS)
- [ ] `alembic upgrade head` applied; `alembic check` clean
- [ ] Frontend built (not `dev`) and served over HTTPS
