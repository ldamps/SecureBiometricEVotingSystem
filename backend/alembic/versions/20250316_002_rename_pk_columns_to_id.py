"""Rename primary key columns to id (for UUIDPrimaryKeyMixin).

Revision ID: 20250316_002
Revises: 20250225_001
Create Date: 2025-03-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250316_002"
down_revision: Union[str, None] = "20250225_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, old_pk_column)
PK_RENAMES = [
    ("address", "address_id"),
    ("audit_log", "audit_id"),
    ("ballot_token", "token_id"),
    ("biometric_template", "biometric_id"),
    ("candidate", "candidate_id"),
    ("constituency", "constituency_id"),
    ("election", "election_id"),
    ("election_official", "official_id"),
    ("error_report", "error_id"),
    ("investigation", "investigation_id"),
    ("seat_allocation", "allocation_id"),
    ("tally_result", "result_id"),
    ("voter", "voter_id"),
    ("voter_ledger", "ledger_id"),
    ("vote", "vote_id"),
]

# (from_table, fk_column, to_table) - FKs that reference a table's PK we are renaming
FKS_TO_RECREATE = [
    ("address", "voter_id", "voter"),
    ("ballot_token", "election_id", "election"),
    ("ballot_token", "constituency_id", "constituency"),
    ("biometric_template", "voter_id", "voter"),
    ("candidate", "election_id", "election"),
    ("candidate", "constituency_id", "constituency"),
    ("election", "created_by", "election_official"),
    ("election_official", "constituency_id", "constituency"),
    ("election_official", "created_by", "election_official"),
    ("error_report", "election_id", "election"),
    ("error_report", "reported_by", "election_official"),
    ("investigation", "error_id", "error_report"),
    ("investigation", "election_id", "election"),
    ("investigation", "raised_by", "election_official"),
    ("investigation", "assigned_to", "election_official"),
    ("investigation", "resolved_by", "election_official"),
    ("seat_allocation", "election_id", "election"),
    ("seat_allocation", "constituency_id", "constituency"),
    ("seat_allocation", "verified_by", "election_official"),
    ("tally_result", "election_id", "election"),
    ("tally_result", "constituency_id", "constituency"),
    ("tally_result", "candidate_id", "candidate"),
    ("voter", "constituency_id", "constituency"),
    ("voter_ledger", "voter_id", "voter"),
    ("voter_ledger", "election_id", "election"),
    ("vote", "election_id", "election"),
    ("vote", "constituency_id", "constituency"),
    ("vote", "candidate_id", "candidate"),
]


def _fk_name(table: str, column: str, referred_table: str) -> str:
    return f"fk_{table}_{column}_{referred_table}"


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

    # Drop FKs that reference tables whose PK we are renaming (only if constraint exists)
    for from_table, fk_column, to_table in FKS_TO_RECREATE:
        constraint_name = _fk_name(from_table, fk_column, to_table)
        try:
            op.drop_constraint(constraint_name, from_table, type_="foreignkey")
        except Exception:
            pass  # constraint may already be gone or name may differ

    # Rename PK columns to id only when the old column still exists (existing DBs)
    for table, old_pk in PK_RENAMES:
        if _table_has_column(conn, table, old_pk):
            op.alter_column(
                table,
                old_pk,
                new_column_name="id",
                existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                existing_nullable=False,
            )

    # Recreate FKs pointing to id (only if not already present)
    for from_table, fk_column, to_table in FKS_TO_RECREATE:
        constraint_name = _fk_name(from_table, fk_column, to_table)
        try:
            op.create_foreign_key(
                constraint_name,
                from_table,
                to_table,
                [fk_column],
                ["id"],
            )
        except Exception:
            pass  # may already exist


def downgrade() -> None:
    # Drop FKs
    for from_table, fk_column, to_table in FKS_TO_RECREATE:
        constraint_name = _fk_name(from_table, fk_column, to_table)
        op.drop_constraint(constraint_name, from_table, type_="foreignkey")

    # Rename id back to original PK names
    for table, old_pk in PK_RENAMES:
        op.alter_column(
            table,
            "id",
            new_column_name=old_pk,
            existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
            existing_nullable=False,
        )

    # Recreate FKs pointing to old column names
    for from_table, fk_column, to_table in FKS_TO_RECREATE:
        constraint_name = _fk_name(from_table, fk_column, to_table)
        to_column = {"voter": "voter_id", "election": "election_id", "constituency": "constituency_id", "election_official": "official_id", "error_report": "error_id", "candidate": "candidate_id"}[to_table]
        op.create_foreign_key(
            constraint_name,
            from_table,
            to_table,
            [fk_column],
            [to_column],
        )
