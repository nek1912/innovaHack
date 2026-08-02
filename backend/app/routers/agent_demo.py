import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.auth import get_current_owner
from app.models.owner import Owner, Agent
from app.services.agent_service import agent_service
from app.services.agent_tools import (
    list_allowed_payees,
    check_credit,
    get_agent_status,
    list_recent_transactions,
)
from app.services.demo_tasks import get_task, list_tasks

router = APIRouter(prefix="/agent-demo", tags=["agent-demo"])


class ExecuteTaskRequest(BaseModel):
    agent_id: uuid.UUID
    task_id: str


@router.get("/tasks")
async def get_demo_tasks():
    return {"tasks": list_tasks()}


@router.get("/tasks/{task_id}")
async def get_demo_task(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/execute")
async def execute_task(
    request: ExecuteTaskRequest,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.id == request.agent_id, Agent.owner_id == owner.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    task = get_task(request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the first active payee for this agent
    payees = await list_allowed_payees(request.agent_id, db)
    payee_id = payees[0]["id"] if payees else None

    return await agent_service.execute_task(
        agent_id=request.agent_id,
        task_id=task["id"],
        task_description=task["description"],
        payee_id=payee_id,
        session=db,
    )


@router.get("/tools/payees/{agent_id}")
async def agent_list_payees(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.owner_id == owner.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"payees": await list_allowed_payees(agent_id, db)}


@router.get("/tools/credit/{agent_id}")
async def agent_check_credit(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.owner_id == owner.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")
    return await check_credit(agent_id, db)


@router.get("/tools/status/{agent_id}")
async def agent_get_status(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.owner_id == owner.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")
    return await get_agent_status(agent_id, db)


@router.get("/tools/transactions/{agent_id}")
async def agent_list_transactions(
    agent_id: uuid.UUID,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.owner_id == owner.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"transactions": await list_recent_transactions(agent_id, db)}
