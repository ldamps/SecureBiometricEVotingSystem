"""add referendum_id to error_report and investigation

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── error_report ──
    op.add_column('error_report', sa.Column('referendum_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_error_report_referendum_id'), 'error_report', ['referendum_id'], unique=False)
    op.create_foreign_key(
        'fk_error_report_referendum_id',
        'error_report',
        'referendum',
        ['referendum_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.alter_column('error_report', 'election_id', nullable=True)
    op.create_check_constraint(
        'ck_error_report_election_xor_referendum',
        'error_report',
        '(election_id IS NOT NULL AND referendum_id IS NULL) OR '
        '(election_id IS NULL AND referendum_id IS NOT NULL)',
    )

    # ── investigation ──
    op.add_column('investigation', sa.Column('referendum_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_investigation_referendum_id'), 'investigation', ['referendum_id'], unique=False)
    op.create_foreign_key(
        'fk_investigation_referendum_id',
        'investigation',
        'referendum',
        ['referendum_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.alter_column('investigation', 'election_id', nullable=True)
    op.create_check_constraint(
        'ck_investigation_election_xor_referendum',
        'investigation',
        '(election_id IS NOT NULL AND referendum_id IS NULL) OR '
        '(election_id IS NULL AND referendum_id IS NOT NULL)',
    )


def downgrade() -> None:
    # ── investigation ──
    op.drop_constraint('ck_investigation_election_xor_referendum', 'investigation', type_='check')
    op.alter_column('investigation', 'election_id', nullable=False)
    op.drop_constraint('fk_investigation_referendum_id', 'investigation', type_='foreignkey')
    op.drop_index(op.f('ix_investigation_referendum_id'), table_name='investigation')
    op.drop_column('investigation', 'referendum_id')

    # ── error_report ──
    op.drop_constraint('ck_error_report_election_xor_referendum', 'error_report', type_='check')
    op.alter_column('error_report', 'election_id', nullable=False)
    op.drop_constraint('fk_error_report_referendum_id', 'error_report', type_='foreignkey')
    op.drop_index(op.f('ix_error_report_referendum_id'), table_name='error_report')
    op.drop_column('error_report', 'referendum_id')
