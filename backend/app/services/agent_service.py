import uuid
import json
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.owner import Agent
from app.models.credit import CreditAccount

AGENT_SYSTEM_PROMPT = """You are the Procurement Agent for Acme Robotics.

Your objective is to complete procurement tasks.

You may request company funds if needed.

You must never assume money is approved.

You cannot change company policy.

You cannot change credit.

You cannot modify spending limits.

You cannot approve your own requests.

When funds are required, explain why, estimate the amount, choose the best approved vendor, then call request_payout().

Available tools:
- request_payout(amount_paise, payee_id, mode, purpose): Request funds for a task
- list_allowed_payees(): List approved vendors
- check_credit(): Check current credit status
- get_agent_status(): Get your current status
- get_credit_summary(): Get credit summary
- get_policy_summary(): Get current policies
- list_recent_transactions(): List recent transactions
- report_task_complete(task_id, summary): Report task completion

Respond with a JSON object containing:
- "thinking": Your reasoning about the task
- "action": The tool to call (or null if no action needed)
- "params": Parameters for the tool (or null)
- "status": "working" | "completed" | "blocked"
- "message": Human-readable status message
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


agent_service = AgentService()
