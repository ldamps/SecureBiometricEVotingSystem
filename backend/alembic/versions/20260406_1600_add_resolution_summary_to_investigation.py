"""add resolution_summary to investigation

Revision ID: a1b2c3d4e5f6
Revises: 9d9c628c5050
Create Date: 2026-04-06 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9d9c628c5050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'investigation',
        sa.Column('resolution_summary', JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('investigation', 'resolution_summary')
