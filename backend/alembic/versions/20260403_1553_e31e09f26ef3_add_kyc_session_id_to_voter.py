"""add_kyc_session_id_to_voter

Revision ID: e31e09f26ef3
Revises: b53e10be5b35
Create Date: 2026-04-03 15:53:07.479154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e31e09f26ef3'
down_revision: Union[str, None] = 'b53e10be5b35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('voter', sa.Column('kyc_session_id', sa.String(length=255), nullable=True))
    op.create_index('ix_voter_kyc_session_id', 'voter', ['kyc_session_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_voter_kyc_session_id', table_name='voter')
    op.drop_column('voter', 'kyc_session_id')
