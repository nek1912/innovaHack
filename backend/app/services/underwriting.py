import uuid

from sqlalchemy.ext.asyncio import AsyncSession


async def calculate_score(
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    session: AsyncSession,
) -> tuple[int, str, int]:
    """Stub underwriting. Returns (score, reason, approved_limit)."""
    return 75, "default stub", 500_000
