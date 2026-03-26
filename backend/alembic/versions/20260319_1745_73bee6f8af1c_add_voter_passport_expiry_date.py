"""add_voter_passport_expiry_date and address encryption migration

Revision ID: 73bee6f8af1c
Revises: 20250318_010
Create Date: 2026-03-19 17:45:07.270556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '73bee6f8af1c'
down_revision: Union[str, None] = '20250318_010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- Voter: add passport_expiry_date encrypted column --
    op.add_column('voter', sa.Column('passport_expiry_date', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # -- Address: migrate encrypted columns from BYTEA to JSONB --
    op.alter_column('address', 'address_line1',
               existing_type=postgresql.BYTEA(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               postgresql_using='NULL')
    op.alter_column('address', 'address_line2',
               existing_type=postgresql.BYTEA(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               postgresql_using='NULL')
    op.alter_column('address', 'town',
               existing_type=postgresql.BYTEA(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               postgresql_using='NULL')
    op.alter_column('address', 'postcode',
               existing_type=postgresql.BYTEA(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               postgresql_using='NULL')
    op.alter_column('address', 'county',
               existing_type=postgresql.BYTEA(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               postgresql_using='NULL')
    op.alter_column('address', 'country',
               existing_type=postgresql.BYTEA(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               postgresql_using='NULL')

    # -- Address: add postcode_search_token --
    op.add_column('address', sa.Column('postcode_search_token', sa.String(length=64), nullable=True))
    op.create_index('ix_address_postcode_search_token', 'address', ['postcode_search_token'], unique=False)


def downgrade() -> None:
    # -- Address: drop postcode_search_token --
    op.drop_index('ix_address_postcode_search_token', table_name='address')
    op.drop_column('address', 'postcode_search_token')

    # -- Address: revert JSONB back to BYTEA --
    for col in ('country', 'county', 'postcode', 'town', 'address_line2', 'address_line1'):
        op.alter_column('address', col,
                   existing_type=postgresql.JSONB(astext_type=sa.Text()),
                   type_=postgresql.BYTEA(),
                   existing_nullable=True,
                   postgresql_using='NULL')

    # -- Voter: drop passport_expiry_date --
    op.drop_column('voter', 'passport_expiry_date')
