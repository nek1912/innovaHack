import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    razorpayx_customer_id: Mapped[str | None] = mapped_column(Text)
    kyc_status: Mapped[str] = mapped_column(Text, nullable=False, default="test_only")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    agents: Mapped[list["Agent"]] = relationship(back_populates="owner")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("owners.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    per_tx_cap_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    daily_cap_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    approval_threshold_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    owner: Mapped["Owner"] = relationship(back_populates="agents")
    payees: Mapped[list["Payee"]] = relationship(back_populates="agent")
    payouts: Mapped[list["Payout"]] = relationship(back_populates="agent")
    credit_account: Mapped["CreditAccount"] = relationship(back_populates="agent", uselist=False)

    __table_args__ = (Index("ix_agents_owner_id", "owner_id"),)


class Payee(Base):
    __tablename__ = "payees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    vpa: Mapped[str | None] = mapped_column(Text)
    bank_account_number: Mapped[str | None] = mapped_column(Text)
    bank_ifsc: Mapped[str | None] = mapped_column(Text)
    razorpay_contact_id: Mapped[str | None] = mapped_column(Text)
    razorpay_fund_account_id: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    agent: Mapped["Agent"] = relationship(back_populates="payees")

    __table_args__ = (Index("ix_payees_agent_id", "agent_id"),)


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    payee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payees.id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text)
    policy_decision: Mapped[str] = mapped_column(Text, nullable=False)
    policy_reason: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("owners.id"))
    razorpay_payout_id: Mapped[str | None] = mapped_column(Text)
    razorpay_status: Mapped[str | None] = mapped_column(Text)
    reconcile_attempts: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    agent: Mapped["Agent"] = relationship(back_populates="payouts")
    payee: Mapped["Payee"] = relationship()

    __table_args__ = (
        Index("ix_payouts_razorpay_payout_id", "razorpay_payout_id"),
        Index("ix_payouts_agent_created", "agent_id", "created_at"),
        Index("ix_payouts_status", "razorpay_status"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("owners.id"))
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_audit_agent_created", "agent_id", "created_at"),
        Index("ix_audit_event_type", "event_type"),
    )
