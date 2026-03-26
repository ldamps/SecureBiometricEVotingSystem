"""Seed a default constituency so voter registration with example UUID works.

Revision ID: 20250316_009
Revises: 20250316_008
Create Date: 2025-03-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250316_009"
down_revision: Union[str, None] = "20250316_008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CONSTITUENCY_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    conn = op.get_bind()
    # Insert default constituency only if it doesn't exist (e.g. for Postman/example payloads)
    r = conn.execute(
        sa.text("SELECT 1 FROM constituency WHERE id = :id"),
        {"id": DEFAULT_CONSTITUENCY_ID},
    )
    if r.scalar() is None:
        conn.execute(
            sa.text("""
                INSERT INTO constituency (id, name, country, county, is_active)
                VALUES (:id, 'Default', 'UK', NULL, true)
            """),
            {"id": DEFAULT_CONSTITUENCY_ID},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM constituency WHERE id = :id"), {"id": DEFAULT_CONSTITUENCY_ID})
