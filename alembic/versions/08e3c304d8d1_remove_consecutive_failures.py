"""remove consecutive_failures

Revision ID: 08e3c304d8d1
Revises: 591781f14c5c
Create Date: 2026-04-12 02:33:04.318294

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08e3c304d8d1'
down_revision: Union[str, Sequence[str], None] = '591781f14c5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
