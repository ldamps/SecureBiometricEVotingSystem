"""rename candidate party column to party_id

Revision ID: f74ac263ec3f
Revises: 20260321_past
Create Date: 2026-03-24 11:11:06.416254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f74ac263ec3f'
down_revision: Union[str, None] = '20260321_past'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('candidate', 'party', new_column_name='party_id', schema='public')


def downgrade() -> None:
    op.alter_column('candidate', 'party_id', new_column_name='party', schema='public')
