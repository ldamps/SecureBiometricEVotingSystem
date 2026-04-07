"""replace referendum constituency_id with many-to-many

Revision ID: 60364610e239
Revises: a14770250523
Create Date: 2026-04-03 19:38:44.431055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '60364610e239'
down_revision: Union[str, None] = 'a14770250523'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the many-to-many junction table
    op.create_table(
        'referendum_constituency',
        sa.Column('referendum_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('referendum.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('constituency_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('constituency.id', ondelete='CASCADE'), primary_key=True),
    )

    # Migrate existing single FK data into the junction table
    op.execute(
        "INSERT INTO referendum_constituency (referendum_id, constituency_id) "
        "SELECT id, constituency_id FROM referendum WHERE constituency_id IS NOT NULL"
    )

    # Drop the old single FK column
    op.drop_constraint('fk_referendum_constituency_id_constituency', 'referendum', type_='foreignkey')
    op.drop_index('ix_referendum_constituency_id', table_name='referendum')
    op.drop_column('referendum', 'constituency_id')


def downgrade() -> None:
    # Re-add the single FK column
    op.add_column(
        'referendum',
        sa.Column('constituency_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_referendum_constituency_id', 'referendum', ['constituency_id'], unique=False)
    op.create_foreign_key(
        'fk_referendum_constituency_id_constituency',
        'referendum', 'constituency',
        ['constituency_id'], ['id'],
        ondelete='SET NULL',
    )

    # Migrate back (pick the first constituency per referendum)
    op.execute(
        "UPDATE referendum SET constituency_id = rc.constituency_id "
        "FROM (SELECT DISTINCT ON (referendum_id) referendum_id, constituency_id "
        "      FROM referendum_constituency) rc "
        "WHERE referendum.id = rc.referendum_id"
    )

    op.drop_table('referendum_constituency')
