import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_agent_from_key
from app.db import get_db
from app.deps import log_audit, raise_error, rate_limit_payouts
from app.schemas.payout import PayoutRequest, PayoutResponse
from app.services.opa_client import opa_client
from app.services.policy_input import build_policy_input
from app.services.razorpayx import (
    RazorpayXError,
    _provider_error_status,
    ensure_payee_provider_ids,
    razorpayx_client,
)
from app.models.credit import CreditAccount
from app.models.owner import Payout, Payee, Agent
from app.services.credit_engine import reserve_credit, commit_spend, release_reservation

router = APIRouter(prefix="/agent", tags=["agent"])

DUPLICATE_WINDOW_SECONDS = 60


@router.post("/request-payout", response_model=PayoutResponse)
async def request_payout(
    body: PayoutRequest,
    agent: Agent = Depends(get_agent_from_key),
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_payouts),
):
    request_id = uuid.uuid4()

    # Validate payee exists and belongs to this agent
    payee = await db.get(Payee, body.payee_id)
    if not payee or payee.agent_id != agent.id:
        raise_error(404, "payee_not_found", "Payee not found")

    if not payee.active:
        raise_error(403, "payee_inactive", "Payee is not active")

    # Serialize payout creation per agent: row lock prevents the race where two
    # concurrent identical requests both pass the duplicate check below and
    # both reach the provider (double payment).
    await db.execute(
        select(Agent).where(Agent.id == agent.id).with_for_update()
    )

    # Duplicate request risk: same agent + same payee + same amount within window
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
    dup_result = await db.execute(
        select(func.count(Payout.id)).where(
            Payout.agent_id == agent.id,
            Payout.payee_id == body.payee_id,
            Payout.amount_paise == body.amount_paise,
            Payout.created_at >= cutoff,
        )
    )
    if dup_result.scalar() > 0:
        await log_audit(
            db, request_id, "duplicate_request_risk",
            detail={
                "agent_id": str(agent.id),
                "payee_id": str(body.payee_id),
                "amount_paise": body.amount_paise,
            },
            agent_id=agent.id,
        )
        await db.commit()
        raise_error(409, "duplicate_request_risk", "A similar payout request was recently submitted")

    # Build policy input from DB
    try:
        policy_input = await build_policy_input(
            db, agent.id, body.payee_id, body.amount_paise
        )
    except ValueError as e:
        error_code = str(e)
        error_map = {
            "agent_not_found": (404, "agent_not_found", "Agent not found"),
            "payee_not_found": (404, "payee_not_found", "Payee not found"),
        }
        status, code, msg = error_map.get(error_code, (400, "invalid_request", error_code))
        raise_error(status, code, msg)

    # Call OPA
    try:
        decision = await opa_client.evaluate(policy_input)
    except Exception:
        raise_error(502, "policy_service_unavailable", "Policy evaluation service is unavailable, try again later")
    allow = decision.get("allow", False)
    requires_approval = decision.get("requires_approval", False)
    deny_reason = decision.get("deny_reason")

    if not allow and not requires_approval:
        await log_audit(
            db, request_id, "policy_denied",
            detail={"reason": deny_reason, "amount_paise": body.amount_paise},
            agent_id=agent.id,
        )
        await db.commit()
        # Map OPA deny reasons to structured error codes
        reason = deny_reason or "denied"
        deny_map = {
            "agent_frozen": (403, "agent_frozen", "Agent is frozen"),
            "payee_inactive": (403, "payee_inactive", "Payee is not active"),
            "per_tx_cap_exceeded": (403, "per_tx_cap_exceeded", "Amount exceeds per-transaction cap"),
            "daily_cap_exceeded": (403, "daily_cap_exceeded", "Daily spending cap exceeded"),
            "credit_not_issued": (403, "credit_not_issued", "No credit account exists for this agent"),
            "credit_inactive": (403, "credit_inactive", "Credit account is frozen"),
            "credit_exhausted": (403, "credit_exhausted", "Insufficient available credit"),
        }
        status, code, msg = deny_map.get(reason, (403, "policy_denied", reason))
        raise_error(status, code, msg)

    if requires_approval:
        payout = Payout(
            agent_id=agent.id,
            payee_id=body.payee_id,
            amount_paise=body.amount_paise,
            mode=body.mode,
            purpose=body.purpose,
            policy_decision="approval_required",
            policy_reason="above_approval_threshold",
        )
        db.add(payout)
        await db.flush()
        await log_audit(
            db, request_id, "approval_required",
            detail={"payout_id": str(payout.id), "amount_paise": body.amount_paise},
            agent_id=agent.id,
        )
        await db.commit()
        return PayoutResponse(
            id=payout.id,
            status="pending_approval",
            policy_decision="approval_required",
            policy_reason="above_approval_threshold",
        )

    # allow path — real RazorpayX payout
    payout = Payout(
        agent_id=agent.id,
        payee_id=body.payee_id,
        amount_paise=body.amount_paise,
        mode=body.mode,
        purpose=body.purpose,
        policy_decision="allow",
    )
    db.add(payout)
    await db.flush()

    # Reserve credit before provider call
    credit_result = await db.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent.id)
    )
    credit_account = credit_result.scalar_one_or_none()

    if credit_account:
        await reserve_credit(
            credit_account_id=credit_account.id,
            amount=body.amount_paise,
            session=db,
        )

    try:
        await ensure_payee_provider_ids(db, payee)
        result = await razorpayx_client.create_payout(
            fund_account_id=payee.razorpay_fund_account_id,
            amount_paise=body.amount_paise,
            mode=body.mode,
            purpose=(body.purpose or "payout")[:30],
            idempotency_key=str(payout.id),
            narration=f"AFCS {str(payout.id)[:8]}",
        )
    except RazorpayXError as e:
        # Release credit reservation on provider failure
        if credit_account:
            await release_reservation(
                credit_account_id=credit_account.id,
                amount=body.amount_paise,
                session=db,
            )
        payout.razorpay_status = "local_error"
        await log_audit(
            db, request_id, "provider_failure",
            detail={
                "payout_id": str(payout.id),
                "provider_error_code": e.error_code,
                "provider_status": e.status_code,
                "description": e.description,
            },
            agent_id=agent.id,
        )
        await db.commit()
        status, code, msg = _provider_error_status(e)
        raise_error(status, code, msg)

    # Commit credit spend on provider success
    if credit_account:
        await commit_spend(
            credit_account_id=credit_account.id,
            payout_id=payout.id,
            amount=body.amount_paise,
            session=db,
        )

    payout.razorpay_payout_id = result.get("id")
    payout.razorpay_status = result.get("status", "queued")
    await log_audit(
        db, request_id, "provider_payout_created",
        detail={
            "payout_id": str(payout.id),
            "razorpay_payout_id": result.get("id"),
            "provider_status": result.get("status"),
            "amount_paise": body.amount_paise,
        },
        agent_id=agent.id,
    )
    await db.commit()
    return PayoutResponse(
        id=payout.id,
        status=payout.razorpay_status or "queued",
        policy_decision="allow",
    )
