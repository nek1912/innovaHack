import uuid
import hashlib
import hmac
import logging

from fastapi import APIRouter, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import async_session
from app.models.owner import Payout
from app.deps import log_audit, raise_error

router = APIRouter(tags=["webhooks"])

logger = logging.getLogger(__name__)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    if not settings.razorpay_webhook_secret:
        return True  # skip in dev if no secret configured
    expected = hmac.new(
        settings.razorpay_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not verify_webhook_signature(body, signature):
        raise_error(401, "invalid_webhook_signature", "Webhook signature verification failed")

    try:
        payload = await request.json()
    except Exception:
        raise_error(400, "invalid_payload", "Webhook body is not valid JSON")
    event = payload.get("event", "")
    entity = payload.get("payload", {}).get("payout", {}).get("entity", {})
    razorpay_payout_id = entity.get("id")

    if not razorpay_payout_id:
        return {"status": "ignored"}

    async with async_session() as db:
        result = await db.execute(
            select(Payout)
            .where(Payout.razorpay_payout_id == razorpay_payout_id)
            .with_for_update()
        )
        payout = result.scalar_one_or_none()
        if not payout:
            await log_audit(
                db, uuid.uuid4(), "webhook_unknown_payout",
                detail={"razorpay_payout_id": razorpay_payout_id, "event": event},
            )
            await db.commit()
            return {"status": "unknown_payout"}

        status_map = {
            "payout.processed": "processed",
            "payout.reversed": "reversed",
            "payout.rejected": "rejected",
            "payout.failed": "failed",
            "payout.cancelled": "cancelled",
            "payout.queued": "queued",
            "payout.pending": "pending",
        }
        new_status = status_map.get(event)
        if not new_status:
            return {"status": "ignored_event"}

        # Idempotency: skip if status already matches
        if payout.razorpay_status == new_status:
            return {"status": "already_processed"}

        old_status = payout.razorpay_status
        payout.razorpay_status = new_status
        detail = {
            "event": event,
            "razorpay_payout_id": razorpay_payout_id,
            "old_status": old_status,
            "new_status": new_status,
        }
        # carry provider status_details into audit when present
        status_details = entity.get("status_details")
        if status_details:
            detail["status_details"] = status_details
        await log_audit(
            db, uuid.uuid4(), "payout_webhook",
            detail=detail,
            agent_id=payout.agent_id,
        )
        await db.commit()

    return {"status": "ok"}
