import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    get_current_owner,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
    create_owner_token,
)
from app.db import get_db
from app.config import settings
from app.models.owner import Agent, Owner, Payee, Payout, AuditLog
from app.schemas.payout import (
    AgentCreate,
    AgentResponse,
    AgentList,
    OwnerLogin,
    OwnerToken,
    PayeeCreate,
    PayeeActiveUpdate,
    PayeeResponse,
    PayeeList,
    PayoutDetail,
    PayoutList,
    PayoutRequest,
    PayoutResponse,
    DashboardStats,
    RegisterRequest,
)
from app.services.kill_switch import freeze_agent, unfreeze_agent
from app.services.razorpayx import (
    RazorpayXError,
    _provider_error_status,
    ensure_payee_provider_ids,
    razorpayx_client,
)
from app.services.policy_input import build_policy_input
from app.services.opa_client import opa_client
from app.deps import raise_error, log_audit, ist_today_bounds

router = APIRouter(prefix="/owner", tags=["owner"])


@router.post("/register", response_model=OwnerToken)
async def register_owner(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Owner).where(Owner.email == body.email))
    if existing.scalar_one_or_none():
        raise_error(409, "email_exists", "An account with this email already exists")
    owner = Owner(name=body.name, email=body.email, password_hash=hash_password(body.password))
    db.add(owner)
    await db.commit()
    await db.refresh(owner)
    return OwnerToken(access_token=create_owner_token(owner.id))


@router.post("/login", response_model=OwnerToken)
async def login_owner(body: OwnerLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Owner).where(Owner.email == body.email))
    owner = result.scalar_one_or_none()
    if not owner or not verify_password(body.password, owner.password_hash):
        raise_error(401, "invalid_auth", "Invalid email or password")
    return OwnerToken(access_token=create_owner_token(owner.id))


@router.post("/agents", response_model=AgentResponse)
async def create_agent(
    body: AgentCreate,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    api_key = generate_api_key()
    agent = Agent(
        owner_id=owner.id,
        name=body.name,
        api_key_hash=hash_api_key(api_key),
        per_tx_cap_paise=body.per_tx_cap_paise,
        daily_cap_paise=body.daily_cap_paise,
        approval_threshold_paise=body.approval_threshold_paise,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        status=agent.status,
        per_tx_cap_paise=agent.per_tx_cap_paise,
        daily_cap_paise=agent.daily_cap_paise,
        approval_threshold_paise=agent.approval_threshold_paise,
        api_key=api_key,
    )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)
    if not agent or agent.owner_id != owner.id:
        raise_error(404, "agent_not_found", "Agent not found")
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        status=agent.status,
        per_tx_cap_paise=agent.per_tx_cap_paise,
        daily_cap_paise=agent.daily_cap_paise,
        approval_threshold_paise=agent.approval_threshold_paise,
    )


@router.get("/agents", response_model=AgentList)
async def list_agents(
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.owner_id == owner.id))
    agents = result.scalars().all()
    return AgentList(
        agents=[
            AgentResponse(
                id=a.id,
                name=a.name,
                status=a.status,
                per_tx_cap_paise=a.per_tx_cap_paise,
                daily_cap_paise=a.daily_cap_paise,
                approval_threshold_paise=a.approval_threshold_paise,
            )
            for a in agents
        ]
    )


@router.post("/agents/{agent_id}/freeze")
async def freeze(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    try:
        agent = await freeze_agent(db, agent_id, owner.id)
    except ValueError:
        raise_error(404, "agent_not_found", "Agent not found")
    return {"status": "frozen", "agent_id": str(agent.id)}


@router.post("/agents/{agent_id}/unfreeze")
async def unfreeze(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    try:
        agent = await unfreeze_agent(db, agent_id, owner.id)
    except ValueError:
        raise_error(404, "agent_not_found", "Agent not found")
    return {"status": "active", "agent_id": str(agent.id)}


@router.post("/agents/{agent_id}/payees", response_model=PayeeResponse)
async def create_payee(
    agent_id: uuid.UUID,
    body: PayeeCreate,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)
    if not agent or agent.owner_id != owner.id:
        raise_error(404, "agent_not_found", "Agent not found")
    payee = Payee(agent_id=agent_id, **body.model_dump())
    db.add(payee)
    await db.commit()
    await db.refresh(payee)
    return PayeeResponse(
        id=payee.id,
        label=payee.label,
        vpa=payee.vpa,
        bank_account_number=payee.bank_account_number,
        bank_ifsc=payee.bank_ifsc,
        active=payee.active,
    )


@router.patch("/agents/{agent_id}/payees/{payee_id}", response_model=PayeeResponse)
async def set_payee_active(
    agent_id: uuid.UUID,
    payee_id: uuid.UUID,
    body: PayeeActiveUpdate,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)
    if not agent or agent.owner_id != owner.id:
        raise_error(404, "agent_not_found", "Agent not found")
    payee = await db.get(Payee, payee_id)
    if not payee or payee.agent_id != agent_id:
        raise_error(404, "payee_not_found", "Payee not found")
    payee.active = body.active
    await log_audit(
        db, uuid.uuid4(), "payee_status_changed",
        detail={"payee_id": str(payee.id), "agent_id": str(agent_id), "active": body.active},
        agent_id=agent_id,
        owner_id=owner.id,
    )
    await db.commit()
    return PayeeResponse(
        id=payee.id,
        label=payee.label,
        vpa=payee.vpa,
        bank_account_number=payee.bank_account_number,
        bank_ifsc=payee.bank_ifsc,
        active=payee.active,
    )


@router.post("/payouts/{payout_id}/approve")
async def approve_payout(
    payout_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    payout = await db.get(Payout, payout_id)
    if not payout or payout.policy_decision != "approval_required":
        raise_error(404, "payout_not_found", "Payout not found or not pending approval")
    agent = await db.get(Agent, payout.agent_id)
    if not agent or agent.owner_id != owner.id:
        raise_error(403, "unauthorized_owner_access", "You do not have access to this payout")

    payee = await db.get(Payee, payout.payee_id)
    if not payee:
        raise_error(404, "payee_not_found", "Payee not found")

    try:
        await ensure_payee_provider_ids(db, payee)
        result = await razorpayx_client.create_payout(
            fund_account_id=payee.razorpay_fund_account_id,
            amount_paise=payout.amount_paise,
            mode=payout.mode,
            purpose=payout.purpose or "payout",
            idempotency_key=str(payout.id),
            narration=f"AFCS {str(payout.id)[:8]}",
        )
    except RazorpayXError as e:
        payout.razorpay_status = "local_error"
        await log_audit(
            db, uuid.uuid4(), "provider_failure",
            detail={
                "payout_id": str(payout.id),
                "provider_error_code": e.error_code,
                "provider_status": e.status_code,
                "description": e.description,
            },
            agent_id=payout.agent_id,
            owner_id=owner.id,
        )
        await db.commit()
        status, code, msg = _provider_error_status(e)
        raise_error(status, code, msg)

    payout.policy_decision = "allow"
    payout.approved_by = owner.id
    payout.razorpay_payout_id = result.get("id")
    payout.razorpay_status = result.get("status", "queued")
    await log_audit(
        db, uuid.uuid4(), "payout_approved",
        detail={
            "payout_id": str(payout.id),
            "amount_paise": payout.amount_paise,
            "razorpay_payout_id": result.get("id"),
            "provider_status": result.get("status"),
        },
        agent_id=payout.agent_id,
        owner_id=owner.id,
    )
    await db.commit()
    return {"status": "approved", "payout_id": str(payout.id)}


@router.post("/payouts/{payout_id}/reject")
async def reject_payout(
    payout_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    payout = await db.get(Payout, payout_id)
    if not payout or payout.policy_decision != "approval_required":
        raise_error(404, "payout_not_found", "Payout not found or not pending approval")
    agent = await db.get(Agent, payout.agent_id)
    if not agent or agent.owner_id != owner.id:
        raise_error(403, "unauthorized_owner_access", "You do not have access to this payout")
    payout.policy_decision = "rejected"
    payout.approved_by = owner.id
    await log_audit(
        db, uuid.uuid4(), "payout_rejected",
        detail={"payout_id": str(payout.id), "amount_paise": payout.amount_paise},
        agent_id=payout.agent_id,
        owner_id=owner.id,
    )
    await db.commit()
    return {"status": "rejected", "payout_id": str(payout.id)}


@router.post("/agents/{agent_id}/payouts", response_model=PayoutResponse)
async def owner_request_payout(
    agent_id: uuid.UUID,
    body: PayoutRequest,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)
    if not agent or agent.owner_id != owner.id:
        raise_error(404, "agent_not_found", "Agent not found")
    if agent.status == "frozen":
        raise_error(403, "agent_frozen", "Agent is frozen")

    payee = await db.get(Payee, body.payee_id)
    if not payee or payee.agent_id != agent_id:
        raise_error(404, "payee_not_found", "Payee not found")
    if not payee.active:
        raise_error(403, "payee_inactive", "Payee is not active")

    request_id = uuid.uuid4()

    try:
        policy_input = await build_policy_input(db, agent_id, body.payee_id, body.amount_paise)
    except ValueError as e:
        error_code = str(e)
        error_map = {
            "agent_not_found": (404, "agent_not_found", "Agent not found"),
            "payee_not_found": (404, "payee_not_found", "Payee not found"),
        }
        status, code, msg = error_map.get(error_code, (400, "invalid_request", error_code))
        raise_error(status, code, msg)

    try:
        decision = await opa_client.evaluate(policy_input)
    except Exception:
        raise_error(502, "policy_service_unavailable", "Policy evaluation service is unavailable")

    allow = decision.get("allow", False)
    requires_approval = decision.get("requires_approval", False)
    deny_reason = decision.get("deny_reason")

    if not allow and not requires_approval:
        await log_audit(db, request_id, "policy_denied", detail={"reason": deny_reason, "amount_paise": body.amount_paise}, agent_id=agent_id, owner_id=owner.id)
        await db.commit()
        reason = deny_reason or "denied"
        deny_map = {
            "agent_frozen": (403, "agent_frozen", "Agent is frozen"),
            "payee_inactive": (403, "payee_inactive", "Payee is not active"),
            "per_tx_cap_exceeded": (403, "per_tx_cap_exceeded", "Amount exceeds per-transaction cap"),
            "daily_cap_exceeded": (403, "daily_cap_exceeded", "Daily spending cap exceeded"),
        }
        status, code, msg = deny_map.get(reason, (403, "policy_denied", reason))
        raise_error(status, code, msg)

    if requires_approval:
        payout = Payout(agent_id=agent_id, payee_id=body.payee_id, amount_paise=body.amount_paise, mode=body.mode, purpose=body.purpose, policy_decision="approval_required", policy_reason="above_approval_threshold")
        db.add(payout)
        await db.flush()
        await log_audit(db, request_id, "approval_required", detail={"payout_id": str(payout.id), "amount_paise": body.amount_paise}, agent_id=agent_id, owner_id=owner.id)
        await db.commit()
        return PayoutResponse(id=payout.id, status="pending_approval", policy_decision="approval_required", policy_reason="above_approval_threshold")

    payout = Payout(agent_id=agent_id, payee_id=body.payee_id, amount_paise=body.amount_paise, mode=body.mode, purpose=body.purpose, policy_decision="allow")
    db.add(payout)
    await db.flush()

    try:
        await ensure_payee_provider_ids(db, payee)
        result = await razorpayx_client.create_payout(
            fund_account_id=payee.razorpay_fund_account_id,
            amount_paise=body.amount_paise,
            mode=body.mode,
            purpose=body.purpose or "payout",
            idempotency_key=str(payout.id),
            narration=f"AFCS {str(payout.id)[:8]}",
        )
    except RazorpayXError as e:
        payout.razorpay_status = "local_error"
        await log_audit(db, request_id, "provider_failure", detail={"payout_id": str(payout.id), "provider_error_code": e.error_code, "provider_status": e.status_code, "description": e.description}, agent_id=agent_id, owner_id=owner.id)
        await db.commit()
        status, code, msg = _provider_error_status(e)
        raise_error(status, code, msg)

    payout.razorpay_payout_id = result.get("id")
    payout.razorpay_status = result.get("status", "queued")
    await log_audit(db, request_id, "provider_payout_created", detail={"payout_id": str(payout.id), "razorpay_payout_id": result.get("id"), "provider_status": result.get("status"), "amount_paise": body.amount_paise}, agent_id=agent_id, owner_id=owner.id)
    await db.commit()
    return PayoutResponse(id=payout.id, status=payout.razorpay_status or "queued", policy_decision="allow")


@router.get("/agents/{agent_id}/payees", response_model=PayeeList)
async def list_agent_payees(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)
    if not agent or agent.owner_id != owner.id:
        raise_error(404, "agent_not_found", "Agent not found")
    result = await db.execute(select(Payee).where(Payee.agent_id == agent_id))
    payees = result.scalars().all()
    return PayeeList(
        payees=[
            PayeeResponse(
                id=p.id,
                label=p.label,
                vpa=p.vpa,
                bank_account_number=p.bank_account_number,
                bank_ifsc=p.bank_ifsc,
                active=p.active,
            )
            for p in payees
        ]
    )


@router.get("/agents/{agent_id}/payouts", response_model=PayoutList)
async def list_agent_payouts(
    agent_id: uuid.UUID,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)
    if not agent or agent.owner_id != owner.id:
        raise_error(404, "agent_not_found", "Agent not found")
    
    query = (
        select(Payout, Payee.label)
        .outerjoin(Payee, Payout.payee_id == Payee.id)
        .where(Payout.agent_id == agent_id)
    )
    count_query = select(func.count(Payout.id)).where(Payout.agent_id == agent_id)
    
    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(Payout.created_at.desc()).offset(offset).limit(limit))
    rows = result.all()
    
    return PayoutList(
        payouts=[
            PayoutDetail(
                id=p.id,
                agent_id=p.agent_id,
                agent_name=agent.name,
                payee_id=p.payee_id,
                payee_label=payee_label or "Deleted",
                amount_paise=p.amount_paise,
                mode=p.mode,
                purpose=p.purpose,
                policy_decision=p.policy_decision,
                policy_reason=p.policy_reason,
                razorpay_payout_id=p.razorpay_payout_id,
                razorpay_status=p.razorpay_status,
                created_at=p.created_at.isoformat(),
            )
            for p, payee_label in rows
        ],
        total=total,
    )


@router.get("/payouts", response_model=PayoutList)
async def list_payouts(
    status: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    # Get all agent IDs for this owner
    agent_result = await db.execute(select(Agent.id).where(Agent.owner_id == owner.id))
    agent_ids = [row[0] for row in agent_result.all()]
    
    if not agent_ids:
        return PayoutList(payouts=[], total=0)
    
    query = (
        select(Payout, Agent.name, Payee.label)
        .join(Agent, Payout.agent_id == Agent.id)
        .outerjoin(Payee, Payout.payee_id == Payee.id)
        .where(Payout.agent_id.in_(agent_ids))
    )
    count_query = select(func.count(Payout.id)).where(Payout.agent_id.in_(agent_ids))
    
    if status:
        if status == "pending":
            query = query.where(Payout.policy_decision == "approval_required")
            count_query = count_query.where(Payout.policy_decision == "approval_required")
        elif status == "failed":
            query = query.where(Payout.razorpay_status == "rejected")
            count_query = count_query.where(Payout.razorpay_status == "rejected")
    
    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(Payout.created_at.desc()).offset(offset).limit(limit))
    rows = result.all()
    
    return PayoutList(
        payouts=[
            PayoutDetail(
                id=p.id,
                agent_id=p.agent_id,
                agent_name=agent_name,
                payee_id=p.payee_id,
                payee_label=payee_label or "Deleted",
                amount_paise=p.amount_paise,
                mode=p.mode,
                purpose=p.purpose,
                policy_decision=p.policy_decision,
                policy_reason=p.policy_reason,
                razorpay_payout_id=p.razorpay_payout_id,
                razorpay_status=p.razorpay_status,
                created_at=p.created_at.isoformat(),
            )
            for p, agent_name, payee_label in rows
        ],
        total=total,
    )


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    agent_ids_result = await db.execute(select(Agent.id).where(Agent.owner_id == owner.id))
    agent_ids = [row[0] for row in agent_ids_result.all()]

    total_agents = len(agent_ids)
    active_agents = 0
    frozen_agents = 0
    payee_count = 0
    today_limit = 0

    if agent_ids:
        # Query 1: agent statuses + payee count + daily cap sum
        agg_result = await db.execute(
            select(
                func.count(Agent.id).filter(Agent.status == "active"),
                func.count(Agent.id).filter(Agent.status == "frozen"),
                func.coalesce(func.sum(Agent.daily_cap_paise), 0),
            ).where(Agent.id.in_(agent_ids))
        )
        active_agents, frozen_agents, today_limit = agg_result.one()

        payee_result = await db.execute(
            select(func.count(Payee.id)).where(Payee.agent_id.in_(agent_ids))
        )
        payee_count = payee_result.scalar()

    today_spend = 0
    pending_approvals = 0
    failed_payouts = 0
    policy_violations = 0
    success_rate = 0
    stale_payouts = 0
    local_error_payouts = 0
    last_reconciled_at = None

    if agent_ids:
        day_start_utc, _ = ist_today_bounds()

        # Query 2: all payout aggregates in one pass
        payout_result = await db.execute(
            select(
                func.coalesce(func.sum(Payout.amount_paise).filter(
                    Payout.policy_decision == "allow",
                    Payout.razorpay_status == "processed",
                    Payout.created_at >= day_start_utc,
                ), 0),
                func.count(Payout.id).filter(Payout.policy_decision == "approval_required"),
                func.count(Payout.id).filter(Payout.razorpay_status.in_(["rejected", "cancelled"])),
                func.count(Payout.id).filter(Payout.razorpay_status == "processed"),
                func.count(Payout.id).filter(Payout.razorpay_status.in_(["failed", "rejected", "cancelled", "reversed"])),
                func.count(Payout.id).filter(Payout.razorpay_status == "stale"),
                func.count(Payout.id).filter(Payout.razorpay_status == "local_error"),
            ).where(Payout.agent_id.in_(agent_ids))
        )
        today_spend, pending_approvals, failed_payouts, processed_count, failed_total, stale_payouts, local_error_payouts = payout_result.one()

        if processed_count + failed_total > 0:
            success_rate = round(processed_count * 100 / (processed_count + failed_total))

        # Query 3: audit aggregates
        audit_result = await db.execute(
            select(
                func.count(AuditLog.id).filter(AuditLog.event_type == "policy_denied"),
                func.max(AuditLog.created_at).filter(AuditLog.event_type.in_(["payout_reconciled", "payout_stale"])),
            ).where(AuditLog.agent_id.in_(agent_ids))
        )
        policy_violations, last_reconciled_at = audit_result.one()
        if last_reconciled_at is not None:
            last_reconciled_at = last_reconciled_at.isoformat()

    return DashboardStats(
        total_agents=total_agents,
        active_agents=active_agents,
        frozen_agents=frozen_agents,
        total_payees=payee_count,
        today_spend_paise=today_spend,
        today_limit_paise=today_limit,
        pending_approvals=pending_approvals,
        failed_payouts=failed_payouts,
        policy_violations=policy_violations,
        payment_success_rate=success_rate,
        stale_payouts=stale_payouts,
        local_error_payouts=local_error_payouts,
        last_reconciled_at=last_reconciled_at,
        provider_mode=settings.razorpay_mode,
        provider_configured=bool(settings.razorpay_key_id and settings.razorpay_key_secret),
    )
