"""drop_legacy_biometric_template_table

Revision ID: 0737a00cd68b
Revises: 4f249d6a53c3
Create Date: 2026-04-02 11:32:58.943817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0737a00cd68b'
down_revision: Union[str, None] = '4f249d6a53c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_public_biometric_template_modality', table_name='biometric_template')
    op.drop_index('ix_public_biometric_template_status', table_name='biometric_template')
    op.drop_index('ix_public_biometric_template_voter_id', table_name='biometric_template')
    op.drop_table('biometric_template')


def downgrade() -> None:
    op.create_table(
        'biometric_template',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('voter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('voter.id', ondelete='CASCADE'), nullable=False),
        sa.Column('modality', sa.String(255), nullable=False),
        sa.Column('template_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('template_dimension', sa.SmallInteger, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('status', sa.String(255), nullable=False),
        sa.Column('encoded_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        schema='public',
    )
    op.create_index('ix_public_biometric_template_voter_id', 'biometric_template', ['voter_id'])
    op.create_index('ix_public_biometric_template_status', 'biometric_template', ['status'])
    op.create_index('ix_public_biometric_template_modality', 'biometric_template', ['modality'])
