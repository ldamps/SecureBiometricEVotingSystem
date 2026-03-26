"""Drop voter columns: civil_servant, armed_forces, council_employee (no references wanted).

Revision ID: 20250316_007
Revises: 20250316_006
Create Date: 2025-03-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250316_007"
down_revision: Union[str, None] = "20250316_006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Columns to remove from voter (no civil servant / armed forces / council employee tracking)
COLUMNS_TO_DROP = ("civil_servant", "armed_forces", "council_employee")


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
    for col in COLUMNS_TO_DROP:
        if _table_has_column(conn, "voter", col):
            op.drop_column("voter", col)


def downgrade() -> None:
    # Re-adding would require type/default; leave as no-op (columns remain dropped)
    pass
