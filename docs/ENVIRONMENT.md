# Environment Configuration

The repo root `.env` is the single source of truth. The backend loads it explicitly from the repo root (not the working directory), so `uvicorn` can be started from any folder. The frontend only consumes `NEXT_PUBLIC_API_URL` (inlined at build time).

## Variables

| Variable | Required | Dev default | Notes |
|---|---|---|---|
| `DATABASE_URL` | yes | `postgresql+asyncpg://agentfinance:changeme@localhost:5432/agentfinance` | asyncpg driver |
| `JWT_SECRET` | yes | `dev-secret-...` | ≥ 32 bytes; production must differ from the dev default (backend warns/logs if default in prod mode) |
| `RAZORPAY_MODE` | yes | `test` | `test` = sandbox simulation |
| `RAZORPAY_KEY_ID` | yes | `rzp_test_*` | test keys in dev |
| `RAZORPAY_KEY_SECRET` | yes | (test secret) | |
| `RAZORPAY_WEBHOOK_SECRET` | yes | `dev-local-webhook-secret` | must match RazorpayX dashboard |
| `RAZORPAY_DEBIT_IDENTIFIER` | no | *(empty)* | the debit (source) account number for payouts. **Dashboard-provisioned** — it is the test/live account number shown in the RazorpayX dashboard; it cannot be created or discovered via the API. Without it, payout creation is rejected by the provider with `400 "The requested URL was not found on the server."` (surfaced as 502 `provider_failure`). Required even in test mode for payouts to complete. |
| `OPA_URL` | no | `http://localhost:8181` | |
| `NEXT_PUBLIC_API_URL` | no | `http://localhost:8000` | frontend only; baked into the build |

Extra keys in `.env` (e.g. `POSTGRES_PASSWORD`, `NEXT_PUBLIC_*`) are ignored by the backend (`extra="ignore"`), so the root `.env` can be shared with `docker-compose`-style tooling.

## `.env.example`

Mirrors the above with placeholder values; commit-safe. Never commit `.env` itself.

## Frontend

`NEXT_PUBLIC_API_URL` is read at build time — after changing it, rebuild (`npm run build`) or run `npm run dev` fresh.

## Tests

`tests/conftest.py` sets its own env (test DB `agentfinance_test`, test JWT/keys) before importing the app. Running the suite does not touch your dev data.
