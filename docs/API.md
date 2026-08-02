# API Reference

Base URL: `http://localhost:8000` (configure via `NEXT_PUBLIC_API_URL` for the frontend).

All endpoints return JSON. Errors follow `{"error": "<machine_code>", "message": "<human message>", "detail": {...}}`.

## Authentication

| Scheme | Where | How |
|---|---|---|
| Owner | `/owner/*`, `/audit` | `Authorization: Bearer <jwt>` (from `/owner/login`) |
| Agent | `/1/agents/{id}/*` | `X-API-Key: <agent api key>` (shown once at agent creation) |
| Webhook | `/webhooks/razorpay` | HMAC-SHA256 signature in `X-Razorpay-Signature` over the raw body, verified with `RAZORPAY_WEBHOOK_SECRET` |

## Owner endpoints

### Auth
- `POST /owner/register` — body `{"name", "email", "password"}` (name 1-200, email format, password 8-128). Returns `{access_token, token_type}`.
- `POST /owner/login` — body `{"email", "password"}`. Returns `{access_token, token_type}`.

### Agents
- `GET /owner/agents` — list, includes `api_key` only for a newly created agent.
- `POST /owner/agents` — body `{"name", "per_tx_cap_paise", "daily_cap_paise", "approval_threshold_paise"}`. Returns agent with `api_key` (shown once).
- `GET /owner/agents/{agent_id}` — detail.
- `POST /owner/agents/{agent_id}/freeze` / `/unfreeze` — toggles status; `404 agent_not_found` if not owned.
- `GET /owner/agents/{agent_id}/payees` — list payees.
- `POST /owner/agents/{agent_id}/payees` — body `{"label", "vpa"? | "bank_account_number"+ "bank_ifsc"?}` (exactly one of vpa / bank account required).
- `PATCH /owner/agents/{agent_id}/payees/{payee_id}` — body `{"active": bool}`. Audits `payee_status_changed`.
- `GET /owner/agents/{agent_id}/payouts?limit&offset` — payout history for the agent.
- `GET /owner/agents/{agent_id}/audit?limit&offset&event_type&from&to` — audit scoped to the agent.

### Approvals
- `GET /owner/payouts?status&limit&offset` — list; `status=pending` for the approval queue.
- `POST /owner/payouts/{payout_id}/approve` — executes a `pending` payout at the provider.
- `POST /owner/payouts/{payout_id}/reject` — marks `rejected`.

### Dashboard
- `GET /owner/stats` — counts (agents, payees, today's spend vs. aggregate daily limit), `pending_approvals`, `failed_payouts`, `policy_violations`, `payment_success_rate` (0-100 or null), `stale_payouts`, `local_error_payouts`, `last_reconciled_at`, `provider_mode`, `provider_configured`.

## Agent endpoints

- `POST /1/agents/{agent_id}/payouts` — headers `X-API-Key`, `Idempotency-Key`; body `{"amount_paise", "mode" ("upi"|"card"|"bank_account"), "purpose"?, "payee_id"}`. Returns:
  - `allow` → `{"status": "queued", "policy_decision": "allowed", ...}` with `razorpay_payout_id`
  - `requires_approval` → `{"status": "pending", "policy_decision": "requires_approval", ...}`
  - deny → `422` with `{"error": "policy_denied", "message": ..., "detail": {"reason": "<deny_reason>"}}`
  - duplicate within 60s (same amount+payee) → `409 duplicate_request_risk`
- `GET /1/agents/{agent_id}/payouts/{payout_id}` — status lookup.

## Webhook

- `POST /webhooks/razorpay` — RazorpayX payout events (`payout.processed`, `payout.failed`, `payout.reversed`). Malformed JSON → `400 invalid_payload`; bad signature → `401 invalid_signature`; unknown event → `200 {"status": "ignored_event"}`.

## Status values

`Payout.razorpay_status`: `queued` (provider accepted), `processed`, `failed`, `reversed`, `stale` (provider no longer reports it; manual intervention), `local_error` (no provider call happened; manual action required), `pending`/`rejected` (approval flow), `denied` (policy).
