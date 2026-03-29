"""remove revoked_tokens table

Revision ID: dad5dcbfa69a
Revises: 603fa27d571b
Create Date: 2026-02-19 11:59:01.311626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dad5dcbfa69a'
down_revision: Union[str, Sequence[str], None] = '603fa27d571b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_table("revoked_tokens")


def downgrade():
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(), primary_key=True),
    )
