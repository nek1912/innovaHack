import uuid
import json
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.owner import Agent, Payee, Payout
from app.models.credit import CreditAccount, CreditTransaction
from app.deps import log_audit
from app.services.razorpayx import (
    RazorpayXError,
    ensure_payee_provider_ids,
    razorpayx_client,
)
from app.services.policy_input import build_policy_input
from app.services.opa_client import opa_client
from app.services.credit_engine import reserve_credit, commit_spend, release_reservation

AGENT_SYSTEM_PROMPT = """You are the Procurement Agent for Acme Robotics.

Your objective is to complete procurement tasks.

You may request company funds if needed.

You must never assume money is approved.

You cannot change company policy.

You cannot change credit.

You cannot modify spending limits.

You cannot approve your own requests.

IMPORTANT: 
- Use the EXACT amount specified in the task context. Do NOT estimate your own amount.
- The payee_id is provided in the context. Use it directly.
- Call request_payout() with the task's amount and the provided payee_id.
- Do NOT call list_allowed_payees() first - the payee is already provided.

Respond with ONLY a JSON object:
{
  "thinking": "Brief reasoning",
  "action": "request_payout",
  "params": {
    "payee_id": "use the payee_id from context",
    "amount_paise": use the EXACT amount from task context,
    "mode": "upi",
    "purpose": "task description"
  },
  "status": "working",
  "message": "Requesting funds"
}
"""


class AgentService:
    def __init__(self):
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"

    async def execute_task(
        self,
        agent_id: uuid.UUID,
        task_id: str,
        task_description: str,
        session: AsyncSession,
        payee_id: str | None = None,
        task_amount_paise: int | None = None,
        simulate: bool = False,
    ) -> dict:
        result = await session.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValueError("Agent not found")

        result = await session.execute(
            select(CreditAccount).where(CreditAccount.agent_id == agent_id)
        )
        credit_account = result.scalar_one_or_none()

        context = {
            "task_id": task_id,
            "task_description": task_description,
            "agent_name": agent.name,
            "credit_available": credit_account.available_credit if credit_account else 0,
            "credit_limit": credit_account.credit_limit if credit_account else 0,
            "daily_cap": agent.daily_cap_paise,
            "per_tx_cap": agent.per_tx_cap_paise,
            "payee_id": payee_id,
            "task_amount_paise": task_amount_paise,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.groq_url,
                    headers={
                        "Authorization": f"Bearer {settings.groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                            {"role": "user", "content": f"Task: {task_description}\n\nContext: {json.dumps(context)}"},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1024,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                try:
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0].strip()
                    else:
                        json_str = content.strip()
                    parsed = json.loads(json_str)
                except json.JSONDecodeError:
                    parsed = {
                        "thinking": content,
                        "action": None,
                        "params": None,
                        "status": "completed",
                        "message": "Task analyzed",
                    }

                # Execute payout if LLM requested it
                if parsed.get("action") == "request_payout" and parsed.get("params"):
                    params = parsed["params"]
                    try:
                        payout_result = await execute_payout_direct(
                            db=session,
                            agent=agent,
                            payee_id=params.get("payee_id"),
                            amount_paise=task_amount_paise or params.get("amount_paise", 10000),
                            mode=params.get("mode", "upi"),
                            purpose=params.get("purpose", task_description),
                            task_id=task_id,
                            simulate=simulate,
                        )
                        parsed["payout_result"] = payout_result
                        parsed["message"] = f"Payout created: {payout_result.get('status', 'unknown')}"
                        parsed["status"] = "completed"
                    except Exception as e:
                        error_msg = str(e)
                        if "BAD_REQUEST" in error_msg:
                            friendly_msg = "Payment request was rejected by the provider. Please check payee details."
                        elif "insufficient" in error_msg.lower():
                            friendly_msg = "Insufficient credit available for this transaction."
                        elif "frozen" in error_msg.lower():
                            friendly_msg = "Agent is frozen. Cannot process payments."
                        elif "policy" in error_msg.lower():
                            friendly_msg = "Payment blocked by company policy."
                        else:
                            friendly_msg = "Payment could not be processed. Please try again."
                        parsed["message"] = friendly_msg
                        parsed["status"] = "error"

                return {
                    "task_id": task_id,
                    "thinking": parsed.get("thinking", ""),
                    "action": parsed.get("action"),
                    "params": parsed.get("params"),
                    "status": parsed.get("status", "completed"),
                    "message": parsed.get("message", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as e:
            return {
                "task_id": task_id,
                "thinking": f"Error: {str(e)}",
                "action": None,
                "params": None,
                "status": "error",
                "message": f"Agent error: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


async def execute_payout_direct(
    db: AsyncSession,
    agent: Agent,
    payee_id: str,
    amount_paise: int,
    mode: str,
    purpose: str,
    task_id: str,
    simulate: bool = False,
) -> dict:
    """Create a payout record directly — same path as owner_request_payout so it appears in dashboard/audit.

    simulate=True skips RazorpayX calls and marks payout as "simulated" — for demo/testing only.
    """
    payee_uuid = uuid.UUID(payee_id)
    payee = await db.get(Payee, payee_uuid)
    if not payee or payee.agent_id != agent.id:
        raise ValueError("payee_not_found")
    if not payee.active:
        raise ValueError("payee_inactive")

    request_id = uuid.uuid4()

    # Build policy input and evaluate
    try:
        policy_input = await build_policy_input(db, agent.id, payee_uuid, amount_paise)
    except ValueError as e:
        raise ValueError(str(e))

    try:
        decision = await opa_client.evaluate(policy_input)
    except Exception:
        raise ValueError("policy_service_unavailable")

    allow = decision.get("allow", False)
    requires_approval = decision.get("requires_approval", False)
    deny_reason = decision.get("deny_reason")

    if not allow and not requires_approval:
        await log_audit(
            db, request_id, "policy_denied",
            detail={"reason": deny_reason, "amount_paise": amount_paise},
            agent_id=agent.id,
        )
        raise ValueError(deny_reason or "denied")

    if requires_approval:
        payout = Payout(
            agent_id=agent.id,
            payee_id=payee_uuid,
            amount_paise=amount_paise,
            mode=mode,
            purpose=purpose,
            policy_decision="approval_required",
            policy_reason="above_approval_threshold",
        )
        db.add(payout)
        await db.flush()
        await log_audit(
            db, request_id, "approval_required",
            detail={"payout_id": str(payout.id), "amount_paise": amount_paise},
            agent_id=agent.id,
        )
        await db.commit()
        return {"id": str(payout.id), "status": "pending_approval", "policy_decision": "approval_required"}

    # allow path — create payout
    payout = Payout(
        agent_id=agent.id,
        payee_id=payee_uuid,
        amount_paise=amount_paise,
        mode=mode,
        purpose=purpose,
        policy_decision="allow",
    )
    db.add(payout)
    await db.flush()

    # Reserve credit
    credit_result = await db.execute(
        select(CreditAccount).where(CreditAccount.agent_id == agent.id)
    )
    credit_account = credit_result.scalar_one_or_none()
    if credit_account:
        await reserve_credit(credit_account_id=credit_account.id, amount=amount_paise, session=db)

    if simulate:
        # Skip RazorpayX — mark as simulated, commit spend immediately
        if credit_account:
            await commit_spend(credit_account_id=credit_account.id, payout_id=payout.id, amount=amount_paise, session=db)
        payout.razorpay_status = "simulated"
        await log_audit(
            db, request_id, "payout_simulated",
            detail={"payout_id": str(payout.id), "amount_paise": amount_paise, "task_id": task_id},
            agent_id=agent.id,
        )
        await db.commit()
        return {"id": str(payout.id), "status": "simulated", "policy_decision": "allow"}

    try:
        await ensure_payee_provider_ids(db, payee)
        result = await razorpayx_client.create_payout(
            fund_account_id=payee.razorpay_fund_account_id,
            amount_paise=amount_paise,
            mode=mode,
            purpose=purpose or "payout",
            idempotency_key=str(payout.id),
            narration=f"AFCS {str(payout.id)[:8]}",
        )
    except RazorpayXError as e:
        if credit_account:
            await release_reservation(credit_account_id=credit_account.id, amount=amount_paise, session=db)
        payout.razorpay_status = "local_error"
        await log_audit(
            db, request_id, "provider_failure",
            detail={"payout_id": str(payout.id), "error": str(e)},
            agent_id=agent.id,
        )
        await db.commit()
        raise ValueError(f"provider_error: {e.error_code}")

    if credit_account:
        await commit_spend(credit_account_id=credit_account.id, payout_id=payout.id, amount=amount_paise, session=db)

    payout.razorpay_payout_id = result.get("id")
    payout.razorpay_status = result.get("status", "queued")
    await log_audit(
        db, request_id, "provider_payout_created",
        detail={"payout_id": str(payout.id), "razorpay_payout_id": result.get("id"), "amount_paise": amount_paise},
        agent_id=agent.id,
    )
    await db.commit()
    return {"id": str(payout.id), "status": payout.razorpay_status or "queued", "policy_decision": "allow"}


agent_service = AgentService()
