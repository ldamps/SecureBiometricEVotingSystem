"""add email_verification_code table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'email_verification_code',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('voter_id', PG_UUID(as_uuid=True), sa.ForeignKey('voter.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.timezone('utc', sa.func.now())),
        schema='public',
    )
    op.create_index('ix_email_verification_code_voter_id', 'email_verification_code', ['voter_id'])


def downgrade() -> None:
    op.drop_index('ix_email_verification_code_voter_id', table_name='email_verification_code')
    op.drop_table('email_verification_code')
