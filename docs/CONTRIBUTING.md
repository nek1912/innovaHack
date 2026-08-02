# Contributing

## Ground rules

- **Money is integer paise** — never floats, never rounding.
- **Every decision is audited** — new flows must write an `AuditLog` row with `request_id` and a JSON `detail`.
- **Policy stays in OPA** — spend rules live in `policy/spend.rego`, not in Python. Changing behavior means changing Rego and its tests.
- **External calls fail loud** — provider errors map to typed `RazorpayXError`s; never swallow a provider failure into a `queued` success.
- **No new frameworks without asking** — the codebase deliberately uses FastAPI + SQLAlchemy + pytest + Next.js + lucide-react. Match the stack.
- **`ponytail:` comments** mark deliberate simplifications and their upgrade path. Respect them; expand only with justification.

## Workflow

1. Change code, keeping the existing module layout (`routers/`, `services/`, `models/`, `schemas/`).
2. For model changes: `cd backend; .venv\Scripts\python -m alembic revision --autogenerate -m "<msg>"` then review the generated migration (it can create indexes/migrations it shouldn't).
3. Add a test for the behavior:
   - backend: `tests/test_*.py` (pytest, stubbed OPA/RazorpayX)
   - policy: a rule in `policy/spend_test.rego`
4. Run the gates (see TESTING.md): pytest suite, `tools\opa.exe test policy`, `npx tsc --noEmit`, `npx eslint`, `alembic check`.
5. Update `docs/` if behavior, endpoints, or env vars changed.

## Layout cheat sheet

| Change touches | Files |
|---|---|
| HTTP endpoint | `backend/app/routers/*`, `backend/app/schemas/*` |
| Provider call | `backend/app/services/razorpayx.py` |
| Policy decision | `policy/spend.rego` + `policy/spend_test.rego` |
| Spend accounting | `backend/app/services/policy_input.py` |
| Webhooks | `backend/app/routers/webhooks.py` |
| Frontend page | `frontend/app/**/page.tsx` + `frontend/lib/api.ts` |
| DB schema | `backend/app/models/*` + `backend/alembic/versions/*` |

## Commit hygiene

The repository has no commits yet at the end of Phase 5 — an initial commit covering the final state is expected. Never commit `.env` or real secrets.
