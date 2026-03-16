"""Add any remaining voter columns from current model if missing.

Revision ID: 20250316_006
Revises: 20250316_005
Create Date: 2025-03-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "20250316_006"
down_revision: Union[str, None] = "20250316_005"
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
    table = "voter"

    # Add any column from current Voter model if missing (id, national_insurance_number, etc. assumed from 001)
    columns_to_add = [
        ("first_name", sa.Column("first_name", sa.LargeBinary(), nullable=True)),
        ("surname", sa.Column("surname", sa.LargeBinary(), nullable=True)),
        ("date_of_birth", sa.Column("date_of_birth", sa.LargeBinary(), nullable=True)),
        ("email", sa.Column("email", sa.LargeBinary(), nullable=True)),
        ("voter_reference", sa.Column("voter_reference", sa.String(255), nullable=True, index=True)),
        ("constituency_id", sa.Column("constituency_id", PG_UUID(as_uuid=True), nullable=True, index=True)),
        ("registration_status", sa.Column("registration_status", sa.String(255), nullable=True, index=True)),
        ("failed_auth_attempts", sa.Column("failed_auth_attempts", sa.SmallInteger(), nullable=True)),
        ("locked_until", sa.Column("locked_until", sa.TIMESTAMP(timezone=True), nullable=True)),
        ("registered_at", sa.Column("registered_at", sa.TIMESTAMP(timezone=True), nullable=True)),
        ("renew_by", sa.Column("renew_by", sa.TIMESTAMP(timezone=True), nullable=True)),
        ("created_at", sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True)),
        ("updated_at", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True)),
    ]

    for col_name, col_obj in columns_to_add:
        if not _table_has_column(conn, table, col_name):
            op.add_column(table, col_obj)


def downgrade() -> None:
    # No-op: we don't drop columns that might have been created by 001 or other migrations
    pass
