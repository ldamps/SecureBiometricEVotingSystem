"""Rename address_type_enum value LOCAL_PAST to PAST.

Revision ID: 20260321_past
Revises: 20260321_overseas
Create Date: 2026-03-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260321_past"
down_revision: Union[str, None] = "20260321_overseas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE address_type_enum RENAME VALUE 'LOCAL_PAST' TO 'PAST'")


def downgrade() -> None:
    op.execute("ALTER TYPE address_type_enum RENAME VALUE 'PAST' TO 'LOCAL_PAST'")
