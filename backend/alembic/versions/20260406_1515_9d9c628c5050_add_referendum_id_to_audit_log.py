"""add referendum_id to audit_log

Revision ID: 9d9c628c5050
Revises: f734a4f838cb
Create Date: 2026-04-06 15:15:21.465393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d9c628c5050'
down_revision: Union[str, None] = 'f734a4f838cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audit_log', sa.Column('referendum_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_audit_log_referendum_id'), 'audit_log', ['referendum_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_log_referendum_id'), table_name='audit_log')
    op.drop_column('audit_log', 'referendum_id')
