"""add election_constituency many-to-many table

Revision ID: f734a4f838cb
Revises: 72e1af3f04a4
Create Date: 2026-04-03 20:55:33.105061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f734a4f838cb'
down_revision: Union[str, None] = '72e1af3f04a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'election_constituency',
        sa.Column('election_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('election.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('constituency_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('constituency.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('election_constituency')
