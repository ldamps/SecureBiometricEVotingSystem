"""encrypt ballot_token blind_token_hash column with JSONB and add search token

Revision ID: a7c1e2f38b49
Revises: 4ad342d56387
Create Date: 2026-03-28 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a7c1e2f38b49'
down_revision: Union[str, None] = '4ad342d56387'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop the old unique index and constraint on blind_token_hash (UUID column)
    op.drop_index(
        'ix_public_ballot_token_blind_token_hash',
        table_name='ballot_token',
        schema='public',
    )

    # 2. Change blind_token_hash from UUID to JSONB (encrypted EncryptedDBField)
    op.alter_column(
        'ballot_token',
        'blind_token_hash',
        existing_type=sa.UUID(),
        type_=JSONB,
        existing_nullable=False,
        postgresql_using='NULL',
        schema='public',
    )

    # 3. Add the HMAC search token column
    op.add_column(
        'ballot_token',
        sa.Column('blind_token_hash_search_token', sa.String(64), nullable=True),
        schema='public',
    )

    # 4. Create unique index on the search token
    op.create_index(
        'ix_public_ballot_token_blind_token_hash_search_token',
        'ballot_token',
        ['blind_token_hash_search_token'],
        unique=True,
        schema='public',
    )

    # 5. Add unique constraint on search token
    op.create_unique_constraint(
        'uq_ballot_token_blind_token_hash_search_token',
        'ballot_token',
        ['blind_token_hash_search_token'],
        schema='public',
    )


def downgrade() -> None:
    # Remove the unique constraint and index on search token
    op.drop_constraint(
        'uq_ballot_token_blind_token_hash_search_token',
        'ballot_token',
        schema='public',
        type_='unique',
    )
    op.drop_index(
        'ix_public_ballot_token_blind_token_hash_search_token',
        table_name='ballot_token',
        schema='public',
    )

    # Drop the search token column
    op.drop_column('ballot_token', 'blind_token_hash_search_token', schema='public')

    # Revert blind_token_hash back to UUID
    op.alter_column(
        'ballot_token',
        'blind_token_hash',
        existing_type=JSONB,
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using='NULL',
        schema='public',
    )

    # Recreate the original unique index
    op.create_index(
        'ix_public_ballot_token_blind_token_hash',
        'ballot_token',
        ['blind_token_hash'],
        unique=True,
        schema='public',
    )
