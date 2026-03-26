"""Add passport_number and passport_country to voter if missing.

Revision ID: 20250316_003
Revises: 20250316_002
Create Date: 2025-03-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250316_003"
down_revision: Union[str, None] = "20250316_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_has_column(conn, table: str, column: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_has_column(conn, "voter", "passport_number"):
        op.add_column(
            "voter",
            sa.Column("passport_number", sa.String(255), nullable=True, index=True),
        )
    if not _table_has_column(conn, "voter", "passport_country"):
        op.add_column(
            "voter",
            sa.Column("passport_country", sa.String(255), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("voter", "passport_country")
    op.drop_column("voter", "passport_number")
