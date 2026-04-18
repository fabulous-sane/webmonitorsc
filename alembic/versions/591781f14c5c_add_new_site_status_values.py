"""add new site_status values

Revision ID: 591781f14c5c
Revises: 4bb13db1e997
Create Date: 2026-04-11 19:00:34.928373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '591781f14c5c'
down_revision: Union[str, Sequence[str], None] = '4bb13db1e997'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE site_status ADD VALUE IF NOT EXISTS 'TIMEOUT'")
    op.execute("ALTER TYPE site_status ADD VALUE IF NOT EXISTS 'ERROR'")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
