"""add_encrypted_key_bundle_to_device_credential

Revision ID: b53e10be5b35
Revises: 0737a00cd68b
Create Date: 2026-04-03 12:00:18.257009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b53e10be5b35'
down_revision: Union[str, None] = '0737a00cd68b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('device_credential', sa.Column('encrypted_key_bundle', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('device_credential', 'encrypted_key_bundle')
