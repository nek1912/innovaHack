# Known Limitations

Deliberate, documented scope boundaries. Do not treat as bugs unless a listed workaround is required.

1. **Frontend unit tests** — none. Deferred because Phase 5 forbids introducing new test frameworks. `tsc` + `eslint` are clean; backend and policy carry the automated coverage.

2. **Live RazorpayX end-to-end** — never exercised against real money. Test-mode sandbox only. `RAZORPAY_DEBIT_IDENTIFIER` is empty in dev, so payout creation is rejected by the provider (400 → surfaced as 502 `provider_failure`). The debit account number is dashboard-provisioned and cannot be created via API — it must be copied from the RazorpayX dashboard into `.env` even for test-mode payouts to complete. Contact/fund-account creation and policy evaluation are verified working against the live test API.

3. **Rate limiting** — none beyond the 60s duplicate window. Add per-key rate limiting before exposing agent endpoints publicly.

4. **Reconciliation is in-process** — the 10-minute scheduler runs inside the backend lifespan. Restarting the backend restarts the timer; multiple backend replicas would double-run it (idempotent per payout, but wasteful). Use a separate worker/Celery beat if scaling.

5. **OPA transport plain HTTP** — dev default. Use private networking/TLS between backend and OPA in production.

6. **Frontend auth token in `localStorage`** — acceptable for an internal console; HttpOnly cookies are the hardened alternative.

7. **Audit immutability is by convention** — no DB trigger blocks manual updates/deletes. Cryptographic chain-of-custody is out of scope.

8. **JWT is HS256 shared-secret** — single-key simplicity; RS256/ES256 with per-service keys for multi-service deployments.

9. **Password policy** — length 8-128 only; no complexity or breach-list checks.

10. **No soft-delete / archival** — audit rows grow unboundedly; plan retention/archival before long production runs (indexes exist on the hot query paths).

11. **Provider error taxonomy** — `local_error`/`stale` statuses require human verification before re-payment; no automatic retry exists by design (double-payment risk).

12. **OPA server must run with `--watch`** (or be restarted) after policy edits — a stale policy will keep serving old decisions.

13. **`daily_cap_paise` is a per-agent cap** — the dashboard's "Today's Limit" is the sum of per-agent daily caps, not an owner-level budget. An owner-level aggregate cap is not implemented.
