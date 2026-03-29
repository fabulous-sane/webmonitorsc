"""update check_interval min

Revision ID: 7060f6f68839
Revises: 88dae01565e7
Create Date: 2026-02-23 17:02:15.325091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7060f6f68839'
down_revision: Union[str, Sequence[str], None] = '88dae01565e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_check_constraint(
        "site_check_interval_range",
        "sites",
        "check_interval >= 60 AND check_interval <= 3600",
    )

def downgrade():
    op.drop_constraint(
        "ck_sites_site_check_interval_range",
        "sites",
        type_="check",
    )