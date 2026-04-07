"""Seat allocation - per-election seat records supporting all UK electoral systems.

- FPTP / AV: one row per constituency (allocation_type = CONSTITUENCY).
- AMS: constituency rows (CONSTITUENCY) + regional top-up rows (REGIONAL_TOPUP).
- STV: one row per winning candidate in a multi-seat constituency (CONSTITUENCY).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin


class AllocationType(str, enum.Enum):
    """How this seat was allocated."""
    CONSTITUENCY = "CONSTITUENCY"
    REGIONAL_TOPUP = "REGIONAL_TOPUP"


class SeatAllocation(Base, UUIDPrimaryKeyMixin):
    """A single seat awarded in an election.

    Each row represents one seat. For FPTP/AV there is one row per
    constituency; for STV there may be several rows per constituency
    (one per elected candidate); for AMS there are constituency rows
    plus regional top-up rows.
    """

    __tablename__ = "seat_allocation"

    election_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    constituency_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="NULL for AMS regional top-up seats.",
    )
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="The winning candidate for this seat.",
    )
    party_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("party.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="The party awarded this seat.",
    )
    allocation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        default=AllocationType.CONSTITUENCY.value,
        comment="CONSTITUENCY or REGIONAL_TOPUP (AMS).",
    )
    seats_won: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of seats (usually 1; >1 for aggregated regional top-ups).",
    )
    vote_share_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    majority: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Winning margin in votes (FPTP/AV only).",
    )
    counts_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election_official.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------