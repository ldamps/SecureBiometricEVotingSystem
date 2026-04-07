"""encrypt_sensitive_columns_and_remove_ip_address

Revision ID: 4f249d6a53c3
Revises: b8d2e4f59c60
Create Date: 2026-04-02 10:24:05.073436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4f249d6a53c3'
down_revision: Union[str, None] = 'b8d2e4f59c60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def _convert_column(table: str, column: str, old_type, *, nullable: bool):
    """Convert a column to JSONB (EncryptedColumn), clearing existing plaintext data."""
    if not nullable:
        op.alter_column(table, column, existing_type=old_type, nullable=True)
    op.alter_column(
        table, column,
        type_=JSONB,
        existing_type=old_type,
        existing_nullable=True,
        postgresql_using='NULL',
    )
    if not nullable:
        # Backfill existing NULLs so NOT NULL can be re-applied
        op.execute(sa.text(f"UPDATE {table} SET {column} = '{{}}'::jsonb WHERE {column} IS NULL"))
        op.alter_column(table, column, existing_type=JSONB, nullable=False)


def upgrade() -> None:
    # -- biometric_template: template_data LargeBinary -> JSONB --
    _convert_column('biometric_template', 'template_data', sa.LargeBinary(), nullable=True)

    # -- vote: blind_token_hash & receipt_code VARCHAR -> JSONB --
    op.add_column('vote', sa.Column('blind_token_hash_search_token', sa.String(64), nullable=True))
    op.add_column('vote', sa.Column('receipt_code_search_token', sa.String(64), nullable=True))

    op.drop_index('ix_vote_blind_token_hash', table_name='vote')
    op.drop_index('ix_public_vote_receipt_code', table_name='vote')

    _convert_column('vote', 'blind_token_hash', sa.String(255), nullable=False)
    _convert_column('vote', 'receipt_code', sa.String(255), nullable=False)

    op.create_index('ix_public_vote_blind_token_hash_search_token', 'vote', ['blind_token_hash_search_token'], unique=False)
    op.create_index('ix_public_vote_receipt_code_search_token', 'vote', ['receipt_code_search_token'], unique=True)

    # -- referendum_vote: blind_token_hash & receipt_code VARCHAR -> JSONB --
    op.add_column('referendum_vote', sa.Column('blind_token_hash_search_token', sa.String(64), nullable=True))
    op.add_column('referendum_vote', sa.Column('receipt_code_search_token', sa.String(64), nullable=True))

    op.drop_index('ix_public_referendum_vote_blind_token_hash', table_name='referendum_vote')
    op.drop_index('ix_public_referendum_vote_receipt_code', table_name='referendum_vote')

    _convert_column('referendum_vote', 'blind_token_hash', sa.String(255), nullable=False)
    _convert_column('referendum_vote', 'receipt_code', sa.String(255), nullable=False)

    op.create_index('ix_public_referendum_vote_blind_token_hash_search_token', 'referendum_vote', ['blind_token_hash_search_token'], unique=True)
    op.create_index('ix_public_referendum_vote_receipt_code_search_token', 'referendum_vote', ['receipt_code_search_token'], unique=True)

    # -- voter: nationality_category & immigration_status VARCHAR -> JSONB --
    op.drop_index('ix_public_voter_nationality_category', table_name='voter')

    _convert_column('voter', 'nationality_category', sa.String(50), nullable=False)
    _convert_column('voter', 'immigration_status', sa.String(50), nullable=True)

    # -- audit_log: remove ip_address column entirely --
    op.drop_column('audit_log', 'ip_address')

    # -- investigation: description & notes TEXT -> JSONB --
    _convert_column('investigation', 'description', sa.Text(), nullable=True)
    _convert_column('investigation', 'notes', sa.Text(), nullable=True)

    # -- error_report: description TEXT -> JSONB --
    _convert_column('error_report', 'description', sa.Text(), nullable=True)


def downgrade() -> None:
    # -- error_report --
    op.alter_column('error_report', 'description', type_=sa.Text(), existing_type=JSONB, existing_nullable=True)

    # -- investigation --
    op.alter_column('investigation', 'notes', type_=sa.Text(), existing_type=JSONB, existing_nullable=True)
    op.alter_column('investigation', 'description', type_=sa.Text(), existing_type=JSONB, existing_nullable=True)

    # -- audit_log --
    op.add_column('audit_log', sa.Column('ip_address', sa.String(45), nullable=True))

    # -- voter --
    op.alter_column('voter', 'immigration_status', type_=sa.String(50), existing_type=JSONB, existing_nullable=True)
    op.alter_column('voter', 'nationality_category', type_=sa.String(50), existing_type=JSONB, existing_nullable=False)
    op.create_index('ix_public_voter_nationality_category', 'voter', ['nationality_category'], unique=False)

    # -- referendum_vote --
    op.drop_index('ix_public_referendum_vote_receipt_code_search_token', table_name='referendum_vote')
    op.drop_index('ix_public_referendum_vote_blind_token_hash_search_token', table_name='referendum_vote')
    op.alter_column('referendum_vote', 'receipt_code', type_=sa.String(255), existing_type=JSONB, existing_nullable=False)
    op.create_index('ix_public_referendum_vote_receipt_code', 'referendum_vote', ['receipt_code'], unique=True)
    op.alter_column('referendum_vote', 'blind_token_hash', type_=sa.String(255), existing_type=JSONB, existing_nullable=False)
    op.create_index('ix_public_referendum_vote_blind_token_hash', 'referendum_vote', ['blind_token_hash'], unique=True)
    op.drop_column('referendum_vote', 'receipt_code_search_token')
    op.drop_column('referendum_vote', 'blind_token_hash_search_token')

    # -- vote --
    op.drop_index('ix_public_vote_receipt_code_search_token', table_name='vote')
    op.drop_index('ix_public_vote_blind_token_hash_search_token', table_name='vote')
    op.alter_column('vote', 'receipt_code', type_=sa.String(255), existing_type=JSONB, existing_nullable=False)
    op.create_index('ix_public_vote_receipt_code', 'vote', ['receipt_code'], unique=True)
    op.alter_column('vote', 'blind_token_hash', type_=sa.String(255), existing_type=JSONB, existing_nullable=False)
    op.create_index('ix_vote_blind_token_hash', 'vote', ['blind_token_hash'], unique=False)
    op.drop_column('vote', 'receipt_code_search_token')
    op.drop_column('vote', 'blind_token_hash_search_token')

    # -- biometric_template --
    op.alter_column('biometric_template', 'template_data', type_=sa.LargeBinary(), existing_type=JSONB, existing_nullable=True)
