"""remove old check_interval constraint

Revision ID: 4bb13db1e997
Revises: 7060f6f68839
Create Date: 2026-02-23 17:25:20.217186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bb13db1e997'
down_revision: Union[str, Sequence[str], None] = '7060f6f68839'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_constraint(
        "ck_site_check_interval_range",
        "sites",
        type_="check",
    )

def downgrade():
    op.create_check_constraint(
        "ck_site_check_interval_range",
        "sites",
        "check_interval >= 60 AND check_interval <= 3600",
    )
