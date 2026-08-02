import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.owner import AuditLog

IST = timezone(timedelta(hours=5, minutes=30))


def ist_today_bounds() -> tuple[datetime, datetime]:
    """Return (start_utc, end_utc) for today's IST calendar day."""
    now_ist = datetime.now(IST)
    day_start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    return day_start_ist.astimezone(timezone.utc), (day_start_ist + timedelta(days=1)).astimezone(timezone.utc)


def raise_error(status_code: int, error: str, message: str, detail: dict | None = None) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"error": error, "message": message, "detail": detail},
    )


async def log_audit(
    db: AsyncSession,
    request_id: uuid.UUID,
    event_type: str,
    detail: dict | None = None,
    agent_id: uuid.UUID | None = None,
    owner_id: uuid.UUID | None = None,
) -> None:
    entry = AuditLog(
        request_id=request_id,
        agent_id=agent_id,
        owner_id=owner_id,
        event_type=event_type,
        detail=detail,
    )
    db.add(entry)
    await db.flush()


# ponytail: in-memory rate limiter — per-API-key, sliding window.
# Good enough for single-process. Needs Redis if scaling to multiple workers.
_RATE_LIMIT_MAX = 20  # requests per window
_RATE_LIMIT_WINDOW = 60  # seconds
_rate_buckets: dict[str, list[float]] = defaultdict(list)


async def rate_limit_payouts(request: Request):
    """FastAPI dependency: rate-limit POST /agent/request-payout per API key."""
    api_key = request.headers.get("x-api-key", "")
    if not api_key:
        return  # auth middleware handles missing keys
    now = time.time()
    bucket = _rate_buckets[api_key]
    # prune old entries
    cutoff = now - _RATE_LIMIT_WINDOW
    bucket[:] = [t for t in bucket if t > cutoff]
    if len(bucket) >= _RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limited", "message": "Too many requests, try again later"},
        )
    bucket.append(now)
