"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum("pending", "test_only", "live", name="kycstatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("active", "frozen", name="agentstatus").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "owners",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("email", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("razorpayx_customer_id", sa.Text),
        sa.Column("kyc_status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("owners.id"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("api_key_hash", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="active"),
        sa.Column("per_tx_cap_paise", sa.BigInteger, nullable=False),
        sa.Column("daily_cap_paise", sa.BigInteger, nullable=False),
        sa.Column("approval_threshold_paise", sa.BigInteger, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "payees",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("vpa", sa.Text),
        sa.Column("bank_account_number", sa.Text),
        sa.Column("bank_ifsc", sa.Text),
        sa.Column("razorpay_fund_account_id", sa.Text),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "payouts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("payee_id", UUID(as_uuid=True), sa.ForeignKey("payees.id"), nullable=False),
        sa.Column("amount_paise", sa.BigInteger, nullable=False),
        sa.Column("mode", sa.Text, nullable=False),
        sa.Column("purpose", sa.Text),
        sa.Column("policy_decision", sa.Text, nullable=False),
        sa.Column("policy_reason", sa.Text),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("owners.id")),
        sa.Column("razorpay_payout_id", sa.Text),
        sa.Column("razorpay_status", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("request_id", UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id")),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("owners.id")),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("detail", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("payouts")
    op.drop_table("payees")
    op.drop_table("agents")
    op.drop_table("owners")
    sa.Enum(name="agentstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="kycstatus").drop(op.get_bind(), checkfirst=True)
