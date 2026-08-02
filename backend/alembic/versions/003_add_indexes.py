"""indexes for hot query paths

Revision ID: 003
Revises: 002
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # webhook + reconciliation lookups by provider payout id
    op.create_index("ix_payouts_razorpay_payout_id", "payouts", ["razorpay_payout_id"])
    # per-agent payout listing + policy daily-spend queries
    op.create_index("ix_payouts_agent_created", "payouts", ["agent_id", "created_at"])
    # status-based queries (stats, stale reconciliation, failed lists)
    op.create_index("ix_payouts_status", "payouts", ["razorpay_status"])
    # agent-owned payee lookups
    op.create_index("ix_payees_agent_id", "payees", ["agent_id"])
    # owner scoping of agents
    op.create_index("ix_agents_owner_id", "agents", ["owner_id"])
    # audit filtering by agent + time (dashboard, audit page)
    op.create_index("ix_audit_agent_created", "audit_log", ["agent_id", "created_at"])
    op.create_index("ix_audit_event_type", "audit_log", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_audit_event_type", table_name="audit_log")
    op.drop_index("ix_audit_agent_created", table_name="audit_log")
    op.drop_index("ix_agents_owner_id", table_name="agents")
    op.drop_index("ix_payees_agent_id", table_name="payees")
    op.drop_index("ix_payouts_status", table_name="payouts")
    op.drop_index("ix_payouts_agent_created", table_name="payouts")
    op.drop_index("ix_payouts_razorpay_payout_id", table_name="payouts")
