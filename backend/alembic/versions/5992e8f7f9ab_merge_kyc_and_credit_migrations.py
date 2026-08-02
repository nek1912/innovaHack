"""merge kyc and credit migrations

Revision ID: 5992e8f7f9ab
Revises: 005, 1f4b51903943
Create Date: 2026-08-02 22:36:58.824497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5992e8f7f9ab'
down_revision: Union[str, None] = ('005', '1f4b51903943')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
