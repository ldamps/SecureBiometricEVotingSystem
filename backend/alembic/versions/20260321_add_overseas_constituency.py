"""Add Overseas constituency for voters registered at an overseas address.

Revision ID: 20260321_overseas
Revises: 20260321_seed
Create Date: 2026-03-21

"""
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "20260321_overseas"
down_revision: Union[str, None] = "20260321_seed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO constituency (id, name, country, county, region, is_active)
            VALUES (:id, 'Overseas', 'Overseas', NULL, NULL, true)
            ON CONFLICT (name) DO NOTHING
        """),
        {"id": str(uuid4())},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM constituency WHERE name = 'Overseas'"))
