"""Tally result - aggregated vote count per candidate per election/constituency."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base


class TallyResult(Base):
    """Aggregated vote count for a candidate in an election/constituency."""

    __tablename__ = "tally_result"

    result_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    election_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election.election_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    constituency_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.constituency_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate.candidate_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tallied_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------
