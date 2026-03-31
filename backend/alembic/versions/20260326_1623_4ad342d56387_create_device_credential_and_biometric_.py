"""create device_credential and biometric_challenge tables

Revision ID: 4ad342d56387
Revises: e31d45e6a623
Create Date: 2026-03-26 16:23:11.609868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ad342d56387'
down_revision: Union[str, None] = 'e31d45e6a623'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('biometric_challenge',
        sa.Column('voter_id', sa.UUID(), nullable=False),
        sa.Column('challenge', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(['voter_id'], ['public.voter.id'], name=op.f('fk_biometric_challenge_voter_id_voter'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_biometric_challenge')),
        sa.UniqueConstraint('challenge', name=op.f('uq_biometric_challenge_challenge')),
        schema='public'
    )
    op.create_index(op.f('ix_public_biometric_challenge_voter_id'), 'biometric_challenge', ['voter_id'], unique=False, schema='public')

    op.create_table('device_credential',
        sa.Column('voter_id', sa.UUID(), nullable=False),
        sa.Column('modalities', sa.String(length=255), nullable=False),
        sa.Column('public_key_pem', sa.Text(), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('attestation', sa.Text(), nullable=True),
        sa.Column('device_label', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.ForeignKeyConstraint(['voter_id'], ['public.voter.id'], name=op.f('fk_device_credential_voter_id_voter'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_device_credential')),
        schema='public'
    )
    op.create_index(op.f('ix_public_device_credential_device_id'), 'device_credential', ['device_id'], unique=False, schema='public')
    op.create_index(op.f('ix_public_device_credential_voter_id'), 'device_credential', ['voter_id'], unique=False, schema='public')


def downgrade() -> None:
    op.drop_index(op.f('ix_public_device_credential_voter_id'), table_name='device_credential', schema='public')
    op.drop_index(op.f('ix_public_device_credential_device_id'), table_name='device_credential', schema='public')
    op.drop_table('device_credential', schema='public')
    op.drop_index(op.f('ix_public_biometric_challenge_voter_id'), table_name='biometric_challenge', schema='public')
    op.drop_table('biometric_challenge', schema='public')
