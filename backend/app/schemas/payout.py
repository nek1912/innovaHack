import uuid
from pydantic import BaseModel, Field, model_validator


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: dict | None = None


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class PayoutRequest(BaseModel):
    payee_id: uuid.UUID
    amount_paise: int = Field(gt=0)
    mode: str = Field(pattern=r"^(upi|imps|neft|rtgs)$")
    purpose: str | None = None


class PayoutResponse(BaseModel):
    id: uuid.UUID
    status: str
    policy_decision: str
    policy_reason: str | None = None


class OwnerLogin(BaseModel):
    email: str
    password: str


class OwnerToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AgentCreate(BaseModel):
    name: str
    per_tx_cap_paise: int = Field(gt=0)
    daily_cap_paise: int = Field(gt=0)
    approval_threshold_paise: int = Field(ge=0)


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    per_tx_cap_paise: int
    daily_cap_paise: int
    approval_threshold_paise: int
    api_key: str | None = None  # only returned on creation


class AgentList(BaseModel):
    agents: list[AgentResponse]


class PayeeCreate(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    vpa: str | None = None
    bank_account_number: str | None = None
    bank_ifsc: str | None = None

    @model_validator(mode="after")
    def _require_destination(self) -> "PayeeCreate":
        if not self.vpa and not self.bank_account_number:
            raise ValueError("Provide either a VPA (UPI) or a bank account")
        if self.bank_account_number and not self.bank_ifsc:
            raise ValueError("IFSC code is required for bank account transfers")
        if self.bank_ifsc and not _IFSC_RE.match(self.bank_ifsc):
            raise ValueError("Invalid IFSC code format (expected 4 letters + 0 + 6 alphanumeric)")
        return self


_IFSC_RE = __import__("re").compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


class PayeeActiveUpdate(BaseModel):
    active: bool


class PayeeResponse(BaseModel):
    id: uuid.UUID
    label: str
    vpa: str | None
    bank_account_number: str | None
    bank_ifsc: str | None
    active: bool


class AuditEntry(BaseModel):
    id: int
    request_id: uuid.UUID
    agent_id: uuid.UUID | None
    owner_id: uuid.UUID | None
    event_type: str
    detail: dict | None
    created_at: str


class AuditList(BaseModel):
    entries: list[AuditEntry]
    total: int


class PayoutDetail(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    agent_name: str
    payee_id: uuid.UUID
    payee_label: str
    amount_paise: int
    mode: str
    purpose: str | None
    policy_decision: str
    policy_reason: str | None
    razorpay_payout_id: str | None
    razorpay_status: str | None
    created_at: str


class PayoutList(BaseModel):
    payouts: list[PayoutDetail]
    total: int


class PayeeList(BaseModel):
    payees: list[PayeeResponse]


class DashboardStats(BaseModel):
    total_agents: int
    active_agents: int
    frozen_agents: int
    total_payees: int
    today_spend_paise: int
    today_limit_paise: int
    pending_approvals: int
    failed_payouts: int
    policy_violations: int = 0
    payment_success_rate: int = 0  # percent 0-100
    stale_payouts: int = 0
    local_error_payouts: int = 0
    last_reconciled_at: str | None = None
    provider_mode: str = "test"
    provider_configured: bool = False
