"""add constituency_id to referendum

Revision ID: a14770250523
Revises: e31e09f26ef3
Create Date: 2026-04-03 19:27:42.361304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a14770250523'
down_revision: Union[str, None] = 'e31e09f26ef3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'referendum',
        sa.Column('constituency_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f('ix_referendum_constituency_id'),
        'referendum',
        ['constituency_id'],
        unique=False,
    )
    op.create_foreign_key(
        op.f('fk_referendum_constituency_id_constituency'),
        'referendum',
        'constituency',
        ['constituency_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f('fk_referendum_constituency_id_constituency'),
        'referendum',
        type_='foreignkey',
    )
    op.drop_index(op.f('ix_referendum_constituency_id'), table_name='referendum')
    op.drop_column('referendum', 'constituency_id')
