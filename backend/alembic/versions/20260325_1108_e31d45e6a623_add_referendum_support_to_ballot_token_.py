"""add referendum support to ballot_token voter_ledger tally_result and create referendum_vote table

Revision ID: e31d45e6a623
Revises: 95768b044c89
Create Date: 2026-03-25 11:08:16.700874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e31d45e6a623'
down_revision: Union[str, None] = '95768b044c89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create referendum_vote table ---
    op.create_table('referendum_vote',
        sa.Column('referendum_id', sa.UUID(), nullable=False),
        sa.Column('choice', sa.String(length=3), nullable=False, comment='YES or NO'),
        sa.Column('blind_token_hash', sa.String(length=255), nullable=False),
        sa.Column('receipt_code', sa.String(length=255), nullable=False),
        sa.Column('email_sent', sa.Boolean(), nullable=False),
        sa.Column('cast_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['referendum_id'], ['public.referendum.id'], name=op.f('fk_referendum_vote_referendum_id_referendum'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_referendum_vote')),
        schema='public'
    )
    op.create_index(op.f('ix_public_referendum_vote_blind_token_hash'), 'referendum_vote', ['blind_token_hash'], unique=True, schema='public')
    op.create_index(op.f('ix_public_referendum_vote_choice'), 'referendum_vote', ['choice'], unique=False, schema='public')
    op.create_index(op.f('ix_public_referendum_vote_receipt_code'), 'referendum_vote', ['receipt_code'], unique=True, schema='public')
    op.create_index(op.f('ix_public_referendum_vote_referendum_id'), 'referendum_vote', ['referendum_id'], unique=False, schema='public')

    # --- ballot_token: add referendum_id, make election_id/constituency_id nullable ---
    op.add_column('ballot_token', sa.Column('referendum_id', sa.UUID(), nullable=True))
    op.alter_column('ballot_token', 'election_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('ballot_token', 'constituency_id', existing_type=sa.UUID(), nullable=True)
    op.create_index(op.f('ix_public_ballot_token_referendum_id'), 'ballot_token', ['referendum_id'], unique=False, schema='public')
    op.create_foreign_key(op.f('fk_ballot_token_referendum_id_referendum'), 'ballot_token', 'referendum', ['referendum_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.execute("""
        ALTER TABLE public.ballot_token
        ADD CONSTRAINT ck_ballot_token_election_xor_referendum
        CHECK (
            (election_id IS NOT NULL AND referendum_id IS NULL) OR
            (election_id IS NULL AND referendum_id IS NOT NULL)
        )
    """)

    # --- tally_result: add referendum_id + choice, make election fields nullable ---
    op.add_column('tally_result', sa.Column('referendum_id', sa.UUID(), nullable=True))
    op.add_column('tally_result', sa.Column('choice', sa.String(length=3), nullable=True, comment='YES or NO — only set for referendum tallies'))
    op.alter_column('tally_result', 'election_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('tally_result', 'constituency_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('tally_result', 'candidate_id', existing_type=sa.UUID(), nullable=True)
    op.create_index(op.f('ix_public_tally_result_choice'), 'tally_result', ['choice'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tally_result_referendum_id'), 'tally_result', ['referendum_id'], unique=False, schema='public')
    op.create_foreign_key(op.f('fk_tally_result_referendum_id_referendum'), 'tally_result', 'referendum', ['referendum_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.execute("""
        ALTER TABLE public.tally_result
        ADD CONSTRAINT ck_tally_result_election_xor_referendum
        CHECK (
            (election_id IS NOT NULL AND referendum_id IS NULL) OR
            (election_id IS NULL AND referendum_id IS NOT NULL)
        )
    """)

    # --- voter_ledger: add referendum_id, make election_id nullable ---
    op.add_column('voter_ledger', sa.Column('referendum_id', sa.UUID(), nullable=True))
    op.alter_column('voter_ledger', 'election_id', existing_type=sa.UUID(), nullable=True)
    op.create_index(op.f('ix_public_voter_ledger_referendum_id'), 'voter_ledger', ['referendum_id'], unique=False, schema='public')
    op.create_foreign_key(op.f('fk_voter_ledger_referendum_id_referendum'), 'voter_ledger', 'referendum', ['referendum_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.execute("""
        ALTER TABLE public.voter_ledger
        ADD CONSTRAINT ck_voter_ledger_election_xor_referendum
        CHECK (
            (election_id IS NOT NULL AND referendum_id IS NULL) OR
            (election_id IS NULL AND referendum_id IS NOT NULL)
        )
    """)


def downgrade() -> None:
    # --- voter_ledger ---
    op.execute("ALTER TABLE public.voter_ledger DROP CONSTRAINT IF EXISTS ck_voter_ledger_election_xor_referendum")
    op.drop_constraint(op.f('fk_voter_ledger_referendum_id_referendum'), 'voter_ledger', schema='public', type_='foreignkey')
    op.drop_index(op.f('ix_public_voter_ledger_referendum_id'), table_name='voter_ledger', schema='public')
    op.alter_column('voter_ledger', 'election_id', existing_type=sa.UUID(), nullable=False)
    op.drop_column('voter_ledger', 'referendum_id')

    # --- tally_result ---
    op.execute("ALTER TABLE public.tally_result DROP CONSTRAINT IF EXISTS ck_tally_result_election_xor_referendum")
    op.drop_constraint(op.f('fk_tally_result_referendum_id_referendum'), 'tally_result', schema='public', type_='foreignkey')
    op.drop_index(op.f('ix_public_tally_result_referendum_id'), table_name='tally_result', schema='public')
    op.drop_index(op.f('ix_public_tally_result_choice'), table_name='tally_result', schema='public')
    op.alter_column('tally_result', 'candidate_id', existing_type=sa.UUID(), nullable=False)
    op.alter_column('tally_result', 'constituency_id', existing_type=sa.UUID(), nullable=False)
    op.alter_column('tally_result', 'election_id', existing_type=sa.UUID(), nullable=False)
    op.drop_column('tally_result', 'choice')
    op.drop_column('tally_result', 'referendum_id')

    # --- ballot_token ---
    op.execute("ALTER TABLE public.ballot_token DROP CONSTRAINT IF EXISTS ck_ballot_token_election_xor_referendum")
    op.drop_constraint(op.f('fk_ballot_token_referendum_id_referendum'), 'ballot_token', schema='public', type_='foreignkey')
    op.drop_index(op.f('ix_public_ballot_token_referendum_id'), table_name='ballot_token', schema='public')
    op.alter_column('ballot_token', 'constituency_id', existing_type=sa.UUID(), nullable=False)
    op.alter_column('ballot_token', 'election_id', existing_type=sa.UUID(), nullable=False)
    op.drop_column('ballot_token', 'referendum_id')

    # --- referendum_vote ---
    op.drop_index(op.f('ix_public_referendum_vote_referendum_id'), table_name='referendum_vote', schema='public')
    op.drop_index(op.f('ix_public_referendum_vote_receipt_code'), table_name='referendum_vote', schema='public')
    op.drop_index(op.f('ix_public_referendum_vote_choice'), table_name='referendum_vote', schema='public')
    op.drop_index(op.f('ix_public_referendum_vote_blind_token_hash'), table_name='referendum_vote', schema='public')
    op.drop_table('referendum_vote', schema='public')
