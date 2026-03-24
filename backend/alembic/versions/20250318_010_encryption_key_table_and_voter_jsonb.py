"""Create encryption_key table and migrate voter encrypted columns to JSONB.

Revision ID: 20250318_010
Revises: 20250316_009
Create Date: 2025-03-18

What this migration does
------------------------
1.  Creates the ``encryption_key`` table (stores KMS-wrapped DEKs).
2a. Converts the six voter columns that were BYTEA (EncryptedBytes) to JSONB.
2b. Converts four voter columns that were VARCHAR (national_insurance_number,
    passport_number, passport_country, voter_reference) to JSONB.
3.  Drops the old plain-text unique constraints on national_insurance_number,
    passport_number, and voter_reference.
4.  Adds search-token columns for the searchable encrypted fields and places
    unique/regular indexes on them.

Data note
---------
Existing plain-text / raw-bytes values in those columns cannot be
automatically migrated to the new EncryptedDBField JSONB format — they
were never properly encrypted.  This migration sets them to NULL.
In production you would run a re-encryption backfill script before
applying step 2.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

revision: str = "20250318_010"
down_revision: Union[str, None] = "20250316_009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Columns changing from BYTEA → JSONB (were EncryptedBytes)
_BYTEA_TO_JSONB = [
    "first_name",
    "surname",
    "previous_first_name",
    "previous_surname",
    "date_of_birth",
    "email",
]

# Columns changing from VARCHAR → JSONB (were plain String)
_VARCHAR_TO_JSONB = [
    "national_insurance_number",
    "passport_number",
    "passport_country",
    "voter_reference",
]

# Search-token columns to add: (column_name, unique)
_SEARCH_TOKEN_COLUMNS = [
    ("national_insurance_number_search_token", True),
    ("passport_number_search_token", True),
    ("email_search_token", False),
    ("voter_reference_search_token", True),
]

# Old constraints to drop before altering columns
_OLD_UNIQUE_CONSTRAINTS = [
    ("voter", "uq_voter_national_insurance_number_unique"),
    ("voter", "uq_voter_voter_reference_unique"),
    # passport_number had inline unique=True — drop by index name
]
_OLD_INDEXES = [
    "ix_voter_national_insurance_number",
    "ix_voter_passport_number",
    "ix_voter_voter_reference",
]


def _column_type(conn, table: str, column: str) -> str | None:
    result = conn.execute(
        sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
        ),
        {"t": table, "c": column},
    )
    row = result.fetchone()
    return row[0].lower() if row else None


def _constraint_exists(conn, constraint: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.table_constraints "
            "WHERE constraint_schema='public' AND constraint_name=:n"
        ),
        {"n": constraint},
    )
    return result.fetchone() is not None


def _index_exists(conn, index: str) -> bool:
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname=:n"),
        {"n": index},
    )
    return result.fetchone() is not None


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def _drop_not_null_if_needed(conn, table: str, column: str) -> None:
    """Allow clearing/converting columns that were NOT NULL (e.g. national_insurance_number)."""
    result = conn.execute(
        sa.text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
        ),
        {"t": table, "c": column},
    )
    row = result.fetchone()
    if row and (row[0] or "").upper() == "NO":
        conn.execute(
            sa.text(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" DROP NOT NULL')
        )


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Create encryption_key table
    # ------------------------------------------------------------------
    op.create_table(
        "encryption_key",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("encrypted_dek", sa.LargeBinary(), nullable=False),
        sa.Column("kms_key_id", sa.String(512), nullable=False),
        sa.Column("kms_key_region", sa.String(64), nullable=False, server_default="us-east-1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.UniqueConstraint(
            "org_id", "purpose", "version",
            name="uq_encryption_key_org_purpose_version",
        ),
        schema="public",
    )
    op.create_index("ix_encryption_key_org_id", "encryption_key", ["org_id"], schema="public")

    # ------------------------------------------------------------------
    # 2a. Drop old plain-text unique constraints + indexes on voter
    # ------------------------------------------------------------------
    for _, constraint_name in _OLD_UNIQUE_CONSTRAINTS:
        if _constraint_exists(conn, constraint_name):
            op.drop_constraint(constraint_name, "voter", type_="unique")

    for idx in _OLD_INDEXES:
        if _index_exists(conn, idx):
            op.drop_index(idx, table_name="voter")

    # passport_number also had a unique constraint created inline; drop it by name
    if _constraint_exists(conn, "uq_voter_passport_number"):
        op.drop_constraint("uq_voter_passport_number", "voter", type_="unique")

    # ------------------------------------------------------------------
    # 2b. BYTEA columns → JSONB
    # ------------------------------------------------------------------
    for col in _BYTEA_TO_JSONB:
        if _column_type(conn, "voter", col) == "bytea":
            _drop_not_null_if_needed(conn, "voter", col)
            conn.execute(
                sa.text(f'ALTER TABLE voter ALTER COLUMN "{col}" TYPE jsonb USING NULL')
            )

    # ------------------------------------------------------------------
    # 2c. VARCHAR columns → JSONB
    # ------------------------------------------------------------------
    for col in _VARCHAR_TO_JSONB:
        col_type = _column_type(conn, "voter", col)
        if col_type and col_type.startswith("character varying"):
            _drop_not_null_if_needed(conn, "voter", col)
            conn.execute(
                sa.text(f'ALTER TABLE voter ALTER COLUMN "{col}" TYPE jsonb USING NULL')
            )

    # ------------------------------------------------------------------
    # 3. Add search-token columns and their indexes
    # ------------------------------------------------------------------
    for token_col, is_unique in _SEARCH_TOKEN_COLUMNS:
        if not _column_exists(conn, "voter", token_col):
            op.add_column(
                "voter",
                sa.Column(token_col, sa.String(64), nullable=True),
            )
        index_name = f"ix_voter_{token_col}"
        if not _index_exists(conn, index_name):
            op.create_index(index_name, "voter", [token_col], unique=is_unique)


def downgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 3. Drop search-token columns and indexes
    # ------------------------------------------------------------------
    for token_col, _ in _SEARCH_TOKEN_COLUMNS:
        index_name = f"ix_voter_{token_col}"
        if _index_exists(conn, index_name):
            op.drop_index(index_name, table_name="voter")
        if _column_exists(conn, "voter", token_col):
            op.drop_column("voter", token_col)

    # ------------------------------------------------------------------
    # 2c. JSONB → VARCHAR  (data loss: values reset to NULL)
    # ------------------------------------------------------------------
    for col in _VARCHAR_TO_JSONB:
        if _column_type(conn, "voter", col) == "jsonb":
            conn.execute(sa.text(f"UPDATE voter SET {col} = NULL"))
            conn.execute(
                sa.text(
                    f"ALTER TABLE voter ALTER COLUMN {col} "
                    f"TYPE varchar(255) USING NULL"
                )
            )

    # ------------------------------------------------------------------
    # 2b. JSONB → BYTEA  (data loss: values reset to NULL)
    # ------------------------------------------------------------------
    for col in _BYTEA_TO_JSONB:
        if _column_type(conn, "voter", col) == "jsonb":
            conn.execute(sa.text(f"UPDATE voter SET {col} = NULL"))
            conn.execute(
                sa.text(
                    f"ALTER TABLE voter ALTER COLUMN {col} TYPE bytea USING NULL"
                )
            )

    # ------------------------------------------------------------------
    # 2a. Re-add old constraints
    # ------------------------------------------------------------------
    if _column_exists(conn, "voter", "national_insurance_number"):
        op.create_unique_constraint(
            "uq_voter_national_insurance_number_unique", "voter", ["national_insurance_number"]
        )
        op.create_index(
            "ix_voter_national_insurance_number", "voter", ["national_insurance_number"]
        )
    if _column_exists(conn, "voter", "voter_reference"):
        op.create_unique_constraint(
            "uq_voter_voter_reference_unique", "voter", ["voter_reference"]
        )
        op.create_index("ix_voter_voter_reference", "voter", ["voter_reference"])

    # ------------------------------------------------------------------
    # 1. Drop encryption_key table
    # ------------------------------------------------------------------
    op.drop_index("ix_encryption_key_org_id", table_name="encryption_key", schema="public")
    op.drop_table("encryption_key", schema="public")
