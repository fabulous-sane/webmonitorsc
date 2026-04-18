"""add ssl monitoring

Revision ID: 2ff6d9fdd337
Revises: 08e3c304d8d1
Create Date: 2026-04-12 18:09:16.735085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ff6d9fdd337'
down_revision: Union[str, Sequence[str], None] = '08e3c304d8d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
