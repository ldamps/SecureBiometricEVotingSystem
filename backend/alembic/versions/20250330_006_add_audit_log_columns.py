"""Add new columns to audit_log table for actor/resource tracking.

Revision ID: 20250330_006
Revises: a7c1e2f38b49
Create Date: 2025-03-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "20250330_006"
down_revision: Union[str, None] = "a7c1e2f38b49"
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

    new_columns = [
        ("action", sa.Column("action", sa.String(50), nullable=False, server_default="CREATE")),
        ("actor_id", sa.Column("actor_id", PG_UUID(as_uuid=True), nullable=True)),
        ("actor_type", sa.Column("actor_type", sa.String(50), nullable=True)),
        ("resource_type", sa.Column("resource_type", sa.String(100), nullable=True)),
        ("resource_id", sa.Column("resource_id", PG_UUID(as_uuid=True), nullable=True)),
        ("election_id", sa.Column("election_id", PG_UUID(as_uuid=True), nullable=True)),
        ("ip_address", sa.Column("ip_address", sa.String(45), nullable=True)),
    ]

    for col_name, col_def in new_columns:
        if not _table_has_column(conn, "audit_log", col_name):
            op.add_column("audit_log", col_def)

    # Change event_metadata from LargeBinary (EncryptedBytes) to JSONB
    # The original model used EncryptedBytes; the new model uses JSONB.
    op.alter_column(
        "audit_log",
        "event_metadata",
        type_=sa.dialects.postgresql.JSONB,
        existing_type=sa.LargeBinary,
        existing_nullable=True,
        postgresql_using="event_metadata::text::jsonb",
    )

    # Add indexes for the new columns
    op.create_index("ix_audit_log_action", "audit_log", ["action"], if_not_exists=True)
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"], if_not_exists=True)
    op.create_index("ix_audit_log_actor_type", "audit_log", ["actor_type"], if_not_exists=True)
    op.create_index("ix_audit_log_resource_type", "audit_log", ["resource_type"], if_not_exists=True)
    op.create_index("ix_audit_log_resource_id", "audit_log", ["resource_id"], if_not_exists=True)
    op.create_index("ix_audit_log_election_id", "audit_log", ["election_id"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_audit_log_election_id", table_name="audit_log")
    op.drop_index("ix_audit_log_resource_id", table_name="audit_log")
    op.drop_index("ix_audit_log_resource_type", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_type", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_id", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")

    op.alter_column(
        "audit_log",
        "event_metadata",
        type_=sa.LargeBinary,
        existing_type=sa.dialects.postgresql.JSONB,
        existing_nullable=True,
    )

    op.drop_column("audit_log", "ip_address")
    op.drop_column("audit_log", "election_id")
    op.drop_column("audit_log", "resource_id")
    op.drop_column("audit_log", "resource_type")
    op.drop_column("audit_log", "actor_type")
    op.drop_column("audit_log", "actor_id")
    op.drop_column("audit_log", "action")
