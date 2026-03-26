"""Add previous_first_name and previous_surname to voter if missing.

Revision ID: 20250316_004
Revises: 20250316_003
Create Date: 2025-03-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250316_004"
down_revision: Union[str, None] = "20250316_003"
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
    # EncryptedBytes -> LargeBinary -> BYTEA in PostgreSQL
    if not _table_has_column(conn, "voter", "previous_first_name"):
        op.add_column(
            "voter",
            sa.Column("previous_first_name", sa.LargeBinary(), nullable=True),
        )
    if not _table_has_column(conn, "voter", "previous_surname"):
        op.add_column(
            "voter",
            sa.Column("previous_surname", sa.LargeBinary(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("voter", "previous_surname")
    op.drop_column("voter", "previous_first_name")
