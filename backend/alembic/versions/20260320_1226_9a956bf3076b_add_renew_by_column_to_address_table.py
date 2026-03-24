"""add renew_by column to address table

Revision ID: 9a956bf3076b
Revises: 20260319_012
Create Date: 2026-03-20 12:26:30.031956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9a956bf3076b'
down_revision: Union[str, None] = '20260319_012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('address', sa.Column('renew_by', sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('address', 'renew_by')
