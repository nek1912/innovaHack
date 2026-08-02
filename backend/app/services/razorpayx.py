import logging
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.owner import Payee

# ponytail: thin RazorpayX client via httpx — no SDK abstraction, direct API calls
# Stops on unclear contracts instead of guessing. No retry beyond idempotency.

RAZORPAY_BASE = "https://api.razorpay.com/v1"

# shared connection pool — created once, reused across requests
_client = httpx.AsyncClient()

# Our internal mode → RazorpayX API mode (case-sensitive per Razorpay docs)
MODE_MAP = {
    "upi": "UPI",
    "imps": "IMPS",
    "neft": "NEFT",
    "rtgs": "RTGS",
}


class RazorpayXError(Exception):
    """Non-2xx response from RazorpayX API."""

    def __init__(self, status_code: int, error_code: str, description: str, raw: dict | None = None):
        self.status_code = status_code
        self.error_code = error_code
        self.description = description
        self.raw = raw or {}
        super().__init__(f"RazorpayX {status_code}: {error_code} — {description}")


class RazorpayXClient:
    def __init__(self):
        self.key_id = settings.razorpay_key_id
        self.key_secret = settings.razorpay_key_secret

    def _headers(self, idempotency_key: str | None = None) -> dict:
        h = {"Content-Type": "application/json"}
        if idempotency_key:
            h["X-Payout-Idempotency"] = idempotency_key
        return h

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        idempotency_key: str | None = None,
        timeout: float = 10.0,
    ) -> dict:
        url = f"{RAZORPAY_BASE}{path}"
        try:
            resp = await _client.request(
                method,
                url,
                json=json,
                headers=self._headers(idempotency_key),
                auth=(self.key_id, self.key_secret),
                timeout=timeout,
            )
        except httpx.TimeoutException:
            # network-level timeout — typed so every caller handles it uniformly
            raise RazorpayXError(504, "provider_timeout", "Payment provider timed out")
        except httpx.HTTPError as e:
            raise RazorpayXError(502, "provider_network_error", f"Payment provider request failed: {e.__class__.__name__}")
        if resp.status_code >= 400:
            body = {}
            if resp.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = resp.json()
                except ValueError:
                    body = {}
            error = body.get("error", {})
            raise RazorpayXError(
                status_code=resp.status_code,
                error_code=error.get("code", "unknown"),
                description=error.get("description", resp.text[:500]),
                raw=body,
            )
        try:
            return resp.json()
        except ValueError:
            return {}

    async def create_contact(self, name: str, contact_type: str = "customer") -> dict:
        """Create a RazorpayX contact. Returns full contact object.
        Live API accepts type in (customer, employee, self_employed, support, sales) —
        'other' is rejected with 400 Invalid type."""
        return await self._request("POST", "/contacts", json={
            "name": name,
            "type": contact_type,
        })

    async def create_fund_account(
        self,
        contact_id: str,
        account_type: str,
        **kwargs: Any,
    ) -> dict:
        """Create a fund account. account_type: 'bank_account' or 'vpa'.
        For bank_account: bank_account_number, ifsc required.
        For vpa: vpa required.
        """
        payload: dict[str, Any] = {
            "contact_id": contact_id,
            "account_type": account_type,
        }
        if account_type == "bank_account":
            payload["bank_account"] = {
                "name": kwargs.get("name", ""),
                "ifsc": kwargs["ifsc"],
                "account_number": kwargs["account_number"],
            }
        elif account_type == "vpa":
            payload["vpa"] = {"address": kwargs["vpa"]}
        else:
            raise ValueError(f"Unsupported fund account type: {account_type}")
        return await self._request("POST", "/fund_accounts", json=payload)

    async def create_payout(
        self,
        fund_account_id: str,
        amount_paise: int,
        mode: str,  # lowercase: upi, imps, neft, rtgs
        purpose: str,
        idempotency_key: str,
        narration: str = "",
        queue_if_low_balance: bool = True,
    ) -> dict:
        """Create a payout. Idempotency key is mandatory per Razorpay docs."""
        api_mode = MODE_MAP.get(mode)
        if not api_mode:
            raise ValueError(f"Unsupported payout mode: {mode}")

        payload: dict[str, Any] = {
            "account_number": settings.razorpay_debit_identifier,
            "fund_account_id": fund_account_id,
            "amount": amount_paise,
            "currency": "INR",
            "mode": api_mode,
            "purpose": purpose or "payout",
            "queue_if_low_balance": queue_if_low_balance,
        }
        if narration:
            payload["narration"] = narration[:30]  # Razorpay max 30 chars

        return await self._request(
            "POST",
            "/payouts",
            json=payload,
            idempotency_key=idempotency_key,
            timeout=15.0,
        )

    async def fetch_payout(self, payout_id: str) -> dict:
        """Fetch current payout state from provider."""
        return await self._request("GET", f"/payouts/{payout_id}")


razorpayx_client = RazorpayXClient()


def _provider_error_status(e: RazorpayXError) -> tuple[int, str, str]:
    """Map a RazorpayX error to (http_status, error_code, message)."""
    if e.status_code >= 500:
        return 502, "provider_failure", "Payment provider is unavailable, please retry later"
    # 4xx: bad request, invalid payload, bad fund account — our fault
    return 422, "provider_rejected", f"Payment provider rejected the request: {e.description}"


async def ensure_payee_provider_ids(db: AsyncSession, payee: Payee) -> None:
    """Create RazorpayX contact + fund account for a payee if missing.

    Race-safe: re-check after each create — another concurrent request may have
    already populated the field, in which case we adopt its IDs and skip ours.

    Raises RazorpayXError on provider failure — callers own the audit/commit.
    """
    if not payee.razorpay_contact_id:
        contact = await razorpayx_client.create_contact(payee.label)
        await db.refresh(payee)
        if not payee.razorpay_contact_id:
            payee.razorpay_contact_id = contact["id"]
            await db.flush()

    if not payee.razorpay_fund_account_id:
        account_type = "vpa" if payee.vpa else "bank_account"
        kwargs = {}
        if account_type == "vpa":
            kwargs["vpa"] = payee.vpa
        else:
            kwargs = {"name": payee.label, "ifsc": payee.bank_ifsc, "account_number": payee.bank_account_number}
        fund = await razorpayx_client.create_fund_account(payee.razorpay_contact_id, account_type, **kwargs)
        await db.refresh(payee)
        if not payee.razorpay_fund_account_id:
            payee.razorpay_fund_account_id = fund["id"]
            await db.flush()
