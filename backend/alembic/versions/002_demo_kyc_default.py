"""set demo kyc default

Revision ID: 002
Revises: 001
Create Date: 2026-08-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE owners SET kyc_status = 'test_only' WHERE kyc_status = 'pending'")
    op.alter_column("owners", "kyc_status", server_default="test_only")


def downgrade() -> None:
    op.alter_column("owners", "kyc_status", server_default="pending")
    op.execute("UPDATE owners SET kyc_status = 'pending' WHERE kyc_status = 'test_only'")
