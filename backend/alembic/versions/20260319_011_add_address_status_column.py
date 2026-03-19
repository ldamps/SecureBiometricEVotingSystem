"""Add address_status column to address table.

Revision ID: 20260319_011
Revises: 73bee6f8af1c
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260319_011"
down_revision: Union[str, None] = "73bee6f8af1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    address_status_enum = sa.Enum("PENDING", "ACTIVE", "REJECTED", name="address_status_enum")
    address_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "address",
        sa.Column(
            "address_status",
            sa.Enum("PENDING", "ACTIVE", "REJECTED", name="address_status_enum"),
            nullable=False,
            server_default="PENDING",
        ),
    )
    op.create_index("ix_address_address_status", "address", ["address_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_address_address_status", table_name="address")
    op.drop_column("address", "address_status")
    sa.Enum(name="address_status_enum").drop(op.get_bind(), checkfirst=True)
