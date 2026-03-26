"""Tally result - aggregated vote counts for elections and referendums."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin


class TallyResult(Base, UUIDPrimaryKeyMixin):
    """Aggregated vote count for a candidate in an election/constituency,
    or for a choice (YES/NO) in a referendum.

    Exactly one of ``election_id`` / ``referendum_id`` must be set.
    - Election tallies: ``election_id``, ``constituency_id``, ``candidate_id`` are set; ``choice`` is NULL.
    - Referendum tallies: ``referendum_id`` and ``choice`` are set; ``election_id``, ``constituency_id``, ``candidate_id`` are NULL.
    """

    __tablename__ = "tally_result"

    # Election tally fields (nullable — NULL for referendum tallies)
    election_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    constituency_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Referendum tally fields (nullable — NULL for election tallies)
    referendum_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("referendum.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    choice: Mapped[str | None] = mapped_column(
        String(3), nullable=True, index=True,
        comment="YES or NO — only set for referendum tallies",
    )

    vote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tallied_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------
    __table_args__ = (
        CheckConstraint(
            "(election_id IS NOT NULL AND referendum_id IS NULL) OR "
            "(election_id IS NULL AND referendum_id IS NOT NULL)",
            name="ck_tally_result_election_xor_referendum",
        ),
    )
