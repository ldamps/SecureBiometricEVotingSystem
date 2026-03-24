"""create party and referendum tables

Revision ID: 95768b044c89
Revises: f74ac263ec3f
Create Date: 2026-03-24 11:47:51.631038

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95768b044c89'
down_revision: Union[str, None] = 'f74ac263ec3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Party table
    op.create_table(
        'party',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('party_name', sa.String(255), nullable=False, index=True),
        sa.Column('abbreviation', sa.String(255), nullable=True, index=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('party_name', name='uq_party_party_name'),
        schema='public',
    )

    # Referendum table
    op.create_table(
        'referendum',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False, index=True),
        sa.Column('question', sa.Text, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('scope', sa.String(255), nullable=False, index=True),
        sa.Column('status', sa.String(255), nullable=False, server_default=sa.text("'OPEN'"), index=True),
        sa.Column('voting_opens', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('voting_closes', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        schema='public',
    )

    # Convert candidate.party_id from varchar to uuid, then add FK
    op.execute(
        "ALTER TABLE public.candidate "
        "ALTER COLUMN party_id TYPE uuid USING party_id::uuid"
    )
    op.create_foreign_key(
        'fk_candidate_party_id_party',
        'candidate', 'party',
        ['party_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_candidate_party_id_party', 'candidate', schema='public', type_='foreignkey')
    op.drop_table('referendum', schema='public')
    op.drop_table('party', schema='public')
