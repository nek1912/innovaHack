import uuid
from datetime import datetime, date, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Date, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class CreditAccount(Base):
    __tablename__ = "credit_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("owners.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, unique=True)
    credit_limit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    available_credit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    used_credit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    reserved_credit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="INR")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner: Mapped["Owner"] = relationship()
    agent: Mapped["Agent"] = relationship()
    transactions: Mapped[list["CreditTransaction"]] = relationship(back_populates="credit_account")
    repayments: Mapped[list["RepaymentSchedule"]] = relationship(back_populates="credit_account")

    __table_args__ = (
        Index("ix_credit_accounts_owner_id", "owner_id"),
        Index("ix_credit_accounts_agent_id", "agent_id"),
    )


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("credit_accounts.id"), nullable=False)
    payout_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payouts.id"))
    type: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    credit_account: Mapped["CreditAccount"] = relationship(back_populates="transactions")

    __table_args__ = (
        Index("ix_credit_transactions_account_id", "credit_account_id"),
        Index("ix_credit_transactions_type", "type"),
        Index("ix_credit_transactions_created", "created_at"),
    )


class CreditDecision(Base):
    __tablename__ = "credit_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_limit: Mapped[int | None] = mapped_column(BigInteger)
    model_version: Mapped[str] = mapped_column(Text, nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_credit_decisions_agent_id", "agent_id"),
    )


class RepaymentSchedule(Base):
    __tablename__ = "repayment_schedule"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("credit_accounts.id"), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    paid_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    repayment_method: Mapped[str] = mapped_column(Text, nullable=False, default="manual")
    provider_transaction_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    credit_account: Mapped["CreditAccount"] = relationship(back_populates="repayments")

    __table_args__ = (
        Index("ix_repayment_schedule_account_id", "credit_account_id"),
        Index("ix_repayment_schedule_due_date", "due_date"),
        Index("ix_repayment_schedule_status", "status"),
    )
