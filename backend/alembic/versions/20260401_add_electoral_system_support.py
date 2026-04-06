"""Add electoral system support across vote, tally_result, and seat_allocation tables.

vote table:
- preference_rank (integer, nullable) — rank for STV / AV ballots.
- party_id (uuid FK -> party, nullable) — for AMS regional-list votes.
- candidate_id made nullable — AMS regional-list votes have no candidate.
- constituency_id made nullable.
- blind_token_hash unique constraint dropped — ranked ballots share a base token.

tally_result table:
- party_id (uuid FK -> party, nullable) — for AMS regional-list tallies.

seat_allocation table:
- candidate_id (uuid FK -> candidate, nullable) — winning candidate for this seat.
- party_id (uuid FK -> party, nullable) — party awarded this seat.
- allocation_type (string, NOT NULL, default CONSTITUENCY) — CONSTITUENCY or REGIONAL_TOPUP.
- seats_won (integer, NOT NULL, default 1) — number of seats (>1 for aggregated top-ups).
- constituency_id made nullable — NULL for AMS regional top-up seats.

Revision ID: b8d2e4f59c60
Revises: a7c1e2f38b49
Create Date: 2026-04-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b8d2e4f59c60"
down_revision: Union[str, None] = "20250330_006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- vote table changes --

    op.add_column(
        "vote",
        sa.Column(
            "preference_rank",
            sa.Integer(),
            nullable=True,
            comment="Preference rank (1 = first choice). Set for STV and AV votes.",
        ),
    )

    op.add_column(
        "vote",
        sa.Column(
            "party_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("party.id", ondelete="CASCADE"),
            nullable=True,
            comment="Set for AMS regional-list votes.",
        ),
    )
    op.create_index("ix_vote_party_id", "vote", ["party_id"])

    op.alter_column("vote", "candidate_id", existing_type=postgresql.UUID(), nullable=True)
    op.alter_column("vote", "constituency_id", existing_type=postgresql.UUID(), nullable=True)
    op.drop_index("ix_public_vote_blind_token_hash", table_name="vote")
    op.create_index("ix_vote_blind_token_hash", "vote", ["blind_token_hash"], unique=False)

    # -- tally_result table changes --

    op.add_column(
        "tally_result",
        sa.Column(
            "party_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("party.id", ondelete="CASCADE"),
            nullable=True,
            comment="Set for AMS regional-list tallies.",
        ),
    )
    op.create_index("ix_tally_result_party_id", "tally_result", ["party_id"])

    # -- seat_allocation table changes --

    op.add_column(
        "seat_allocation",
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate.id", ondelete="SET NULL"),
            nullable=True,
            comment="The winning candidate for this seat.",
        ),
    )
    op.create_index("ix_seat_allocation_candidate_id", "seat_allocation", ["candidate_id"])

    op.add_column(
        "seat_allocation",
        sa.Column(
            "party_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("party.id", ondelete="SET NULL"),
            nullable=True,
            comment="The party awarded this seat.",
        ),
    )
    op.create_index("ix_seat_allocation_party_id", "seat_allocation", ["party_id"])

    op.add_column(
        "seat_allocation",
        sa.Column(
            "allocation_type",
            sa.String(50),
            nullable=False,
            server_default="CONSTITUENCY",
            comment="CONSTITUENCY or REGIONAL_TOPUP (AMS).",
        ),
    )
    op.create_index("ix_seat_allocation_allocation_type", "seat_allocation", ["allocation_type"])

    op.add_column(
        "seat_allocation",
        sa.Column(
            "seats_won",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Number of seats (usually 1; >1 for aggregated regional top-ups).",
        ),
    )

    # Make constituency_id nullable (NULL for AMS regional top-up seats)
    op.alter_column(
        "seat_allocation", "constituency_id",
        existing_type=postgresql.UUID(), nullable=True,
    )


def downgrade() -> None:
    # -- seat_allocation --
    op.alter_column(
        "seat_allocation", "constituency_id",
        existing_type=postgresql.UUID(), nullable=False,
    )
    op.drop_column("seat_allocation", "seats_won")
    op.drop_index("ix_seat_allocation_allocation_type", table_name="seat_allocation")
    op.drop_column("seat_allocation", "allocation_type")
    op.drop_index("ix_seat_allocation_party_id", table_name="seat_allocation")
    op.drop_column("seat_allocation", "party_id")
    op.drop_index("ix_seat_allocation_candidate_id", table_name="seat_allocation")
    op.drop_column("seat_allocation", "candidate_id")

    # -- tally_result --
    op.drop_index("ix_tally_result_party_id", table_name="tally_result")
    op.drop_column("tally_result", "party_id")

    # -- vote --
    op.drop_index("ix_vote_blind_token_hash", table_name="vote")
    op.create_index("ix_public_vote_blind_token_hash", "vote", ["blind_token_hash"], unique=True)
    op.alter_column("vote", "constituency_id", existing_type=postgresql.UUID(), nullable=False)
    op.alter_column("vote", "candidate_id", existing_type=postgresql.UUID(), nullable=False)
    op.drop_index("ix_vote_party_id", table_name="vote")
    op.drop_column("vote", "party_id")
    op.drop_column("vote", "preference_rank")
