import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner import Agent
from app.deps import log_audit


async def freeze_agent(db: AsyncSession, agent_id: uuid.UUID, owner_id: uuid.UUID) -> Agent:
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise ValueError("agent_not_found")
    if agent.owner_id != owner_id:
        raise ValueError("agent_not_found")  # do not reveal other owners' agents
    agent.status = "frozen"
    await log_audit(db, uuid.uuid4(), "freeze", agent_id=agent_id, owner_id=owner_id)
    await db.commit()
    return agent


async def unfreeze_agent(db: AsyncSession, agent_id: uuid.UUID, owner_id: uuid.UUID) -> Agent:
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise ValueError("agent_not_found")
    if agent.owner_id != owner_id:
        raise ValueError("agent_not_found")  # do not reveal other owners' agents
    agent.status = "active"
    await log_audit(db, uuid.uuid4(), "unfreeze", agent_id=agent_id, owner_id=owner_id)
    await db.commit()
    return agent
