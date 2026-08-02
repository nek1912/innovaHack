import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db import async_session
from app.models.owner import Payout
from app.deps import log_audit
from app.services.razorpayx import RazorpayXError, razorpayx_client

logger = logging.getLogger(__name__)

STALE_THRESHOLD_MINUTES = 10
MAX_RECONCILE_ATTEMPTS = 5

PROVIDER_STATUS_MAP = {
    "queued": "queued",
    "pending": "pending",
    "processing": "processing",
    "processed": "processed",
    "reversed": "reversed",
    "cancelled": "cancelled",
    "failed": "failed",
    "rejected": "rejected",
}


async def reconcile_stale_payouts():
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_THRESHOLD_MINUTES)

    async with async_session() as db:
        result = await db.execute(
            select(Payout).where(
                Payout.razorpay_status.in_(["queued", "processing", "local_error"]),
                Payout.created_at < cutoff,
                Payout.razorpay_payout_id.isnot(None),
                Payout.razorpay_payout_id.notlike("stub_%"),
                Payout.reconcile_attempts < MAX_RECONCILE_ATTEMPTS,
            )
        )
        payouts = result.scalars().all()

        for payout in payouts:
            old_status = payout.razorpay_status
            payout.reconcile_attempts += 1
            try:
                provider = await razorpayx_client.fetch_payout(payout.razorpay_payout_id)
            except RazorpayXError as e:
                if e.status_code == 404:
                    payout.razorpay_status = "stale"
                    payout.updated_at = datetime.now(timezone.utc)
                    await log_audit(
                        db, uuid.uuid4(), "payout_stale",
                        detail={
                            "payout_id": str(payout.id),
                            "old_status": old_status,
                            "razorpay_payout_id": payout.razorpay_payout_id,
                            "reason": "provider_not_found",
                        },
                        agent_id=payout.agent_id,
                    )
                    logger.warning("Marked payout %s as stale (provider 404, was %s)", payout.id, old_status)
                elif payout.reconcile_attempts >= MAX_RECONCILE_ATTEMPTS:
                    payout.razorpay_status = "needs_manual_review"
                    payout.updated_at = datetime.now(timezone.utc)
                    await log_audit(
                        db, uuid.uuid4(), "payout_needs_review",
                        detail={
                            "payout_id": str(payout.id),
                            "old_status": old_status,
                            "attempts": payout.reconcile_attempts,
                            "last_error": e.error_code,
                        },
                        agent_id=payout.agent_id,
                    )
                    logger.warning("Payout %s needs manual review after %d attempts", payout.id, payout.reconcile_attempts)
                else:
                    logger.warning("Provider error for payout %s (%s), skipping stale check", payout.id, e.error_code)
                continue

            provider_status = provider.get("status")
            mapped = PROVIDER_STATUS_MAP.get(provider_status)
            if mapped is None:
                logger.warning("Unknown provider status %r for payout %s", provider_status, payout.id)
                continue

            if mapped == old_status:
                continue

            payout.razorpay_status = mapped
            payout.updated_at = datetime.now(timezone.utc)
            detail = {
                "payout_id": str(payout.id),
                "old_status": old_status,
                "new_status": mapped,
                "razorpay_payout_id": payout.razorpay_payout_id,
            }
            status_details = provider.get("status_details")
            if status_details:
                detail["status_details"] = status_details
            await log_audit(
                db, uuid.uuid4(), "payout_reconciled",
                detail=detail,
                agent_id=payout.agent_id,
            )
            logger.info("Reconciled payout %s: %s -> %s", payout.id, old_status, mapped)

        if payouts:
            await db.commit()
            logger.info("Reconciliation pass done for %d payouts", len(payouts))
