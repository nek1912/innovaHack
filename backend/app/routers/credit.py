import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.auth import get_current_owner
from app.models.owner import Owner
from app.models.credit import CreditAccount, CreditDecision, RepaymentSchedule, CreditTransaction
from app.services.credit_engine import issue_credit
from app.services.repayment import process_manual_repayment, create_repayment_schedule

router = APIRouter(prefix="/credit", tags=["credit"])


class CreditIssueRequest(BaseModel):
    agent_id: uuid.UUID


class CreditRepayRequest(BaseModel):
    repayment_id: uuid.UUID


class RepaymentCreateRequest(BaseModel):
    agent_id: uuid.UUID
    amount: int
    days_until_due: int = 30


@router.post("/issue")
async def issue_credit_endpoint(
    request: CreditIssueRequest,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Issue credit to an agent after underwriting."""
    try:
        credit_account = await issue_credit(
            owner_id=owner.id,
            agent_id=request.agent_id,
            session=db,
        )
        await db.commit()
        return {
            "id": str(credit_account.id),
            "agent_id": str(credit_account.agent_id),
            "credit_limit": credit_account.credit_limit,
            "available_credit": credit_account.available_credit,
            "status": credit_account.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/repay")
async def repay_credit_endpoint(
    request: CreditRepayRequest,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Process a manual repayment (simulated)."""
    try:
        repayment = await process_manual_repayment(
            repayment_id=request.repayment_id,
            session=db,
        )
        await db.commit()
        return {
            "id": str(repayment.id),
            "status": repayment.status,
            "paid_amount": repayment.paid_amount,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/account/{agent_id}")
async def get_credit_account(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get credit account for an agent."""
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise HTTPException(status_code=404, detail="Credit account not found")

    return {
        "id": str(credit_account.id),
        "agent_id": str(credit_account.agent_id),
        "credit_limit": credit_account.credit_limit,
        "available_credit": credit_account.available_credit,
        "used_credit": credit_account.used_credit,
        "reserved_credit": credit_account.reserved_credit,
        "status": credit_account.status,
    }


@router.get("/history/{agent_id}")
async def get_credit_history(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get credit transaction history for an agent."""
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise HTTPException(status_code=404, detail="Credit account not found")

    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.credit_account_id == credit_account.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()

    return {
        "transactions": [
            {
                "id": str(tx.id),
                "type": tx.type,
                "amount": tx.amount,
                "balance_after": tx.balance_after,
                "reason": tx.reason,
                "created_at": tx.created_at.isoformat(),
            }
            for tx in transactions
        ],
        "total": len(transactions),
    }


@router.get("/score/{agent_id}")
async def get_credit_score(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get latest credit score/decision for an agent."""
    result = await db.execute(
        select(CreditDecision)
        .where(CreditDecision.agent_id == agent_id)
        .order_by(CreditDecision.created_at.desc())
        .limit(1)
    )
    decision = result.scalar_one_or_none()

    if not decision:
        raise HTTPException(status_code=404, detail="No credit decision found")

    return {
        "id": str(decision.id),
        "decision": decision.decision,
        "score": decision.score,
        "reason": decision.reason,
        "approved_limit": decision.approved_limit,
        "model_version": decision.model_version,
        "created_at": decision.created_at.isoformat(),
    }


@router.get("/repayments/{agent_id}")
async def get_repayments(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get repayment schedule for an agent."""
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent_id)
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise HTTPException(status_code=404, detail="Credit account not found")

    result = await db.execute(
        select(RepaymentSchedule)
        .where(RepaymentSchedule.credit_account_id == credit_account.id)
        .order_by(RepaymentSchedule.due_date.desc())
    )
    repayments = result.scalars().all()

    return {
        "repayments": [
            {
                "id": str(r.id),
                "due_date": r.due_date.isoformat(),
                "amount": r.amount,
                "status": r.status,
                "paid_amount": r.paid_amount,
                "repayment_method": r.repayment_method,
            }
            for r in repayments
        ],
        "total": len(repayments),
    }


@router.post("/create-repayment")
async def create_repayment_endpoint(
    request: RepaymentCreateRequest,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Create a new repayment schedule entry."""
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.agent_id == request.agent_id)
    )
    credit_account = result.scalar_one_or_none()

    if not credit_account:
        raise HTTPException(status_code=404, detail="Credit account not found")

    due_date = date.today() + timedelta(days=request.days_until_due)

    repayment = await create_repayment_schedule(
        credit_account_id=credit_account.id,
        amount=request.amount,
        due_date=due_date,
        session=db,
    )
    await db.commit()

    return {
        "id": str(repayment.id),
        "due_date": repayment.due_date.isoformat(),
        "amount": repayment.amount,
        "status": repayment.status,
    }
