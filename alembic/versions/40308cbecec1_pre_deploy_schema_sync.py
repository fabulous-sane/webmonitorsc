"""pre-deploy schema sync

Revision ID: 40308cbecec1
Revises: 2ff6d9fdd337
Create Date: 2026-04-18 21:59:13.116100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '40308cbecec1'
down_revision: Union[str, Sequence[str], None] = '2ff6d9fdd337'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE sites
        ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMP WITH TIME ZONE
    """)

def downgrade() -> None:
    op.execute("""
        ALTER TABLE sites
        DROP COLUMN IF EXISTS last_checked_at
    """)