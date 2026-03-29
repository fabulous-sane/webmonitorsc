"""add check constraint to sites.check_interval

Revision ID: 88dae01565e7
Revises: 2a1b46c32627
Create Date: 2026-02-23 14:52:20.669745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88dae01565e7'
down_revision: Union[str, Sequence[str], None] = '2a1b46c32627'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_check_constraint(
        "ck_site_check_interval_range",
        "sites",
        "check_interval >= 30 AND check_interval <= 3600",
    )

def downgrade():
    op.drop_constraint(
        "ck_site_check_interval_range",
        "sites",
        type_="check",
    )