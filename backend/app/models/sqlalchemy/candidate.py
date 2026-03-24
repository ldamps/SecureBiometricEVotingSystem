"""Candidate model - candidate in an election/constituency."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.sqlalchemy.party import Party
    from app.models.sqlalchemy.election import Election

class Candidate(Base, UUIDPrimaryKeyMixin):
    """Candidate standing in an election for a constituency."""

    __tablename__ = "candidate"

    election_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    constituency_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    party_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("party.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships ----------

    party: Mapped["Party"] = relationship(
        "Party",
        back_populates="candidates",
    )

    election: Mapped["Election"] = relationship(
        "Election",
        back_populates="candidates",
    )

    # Database constraints + indexes ----------
    __table_args__ = (
        UniqueConstraint(
            "election_id",
            "constituency_id",
            "party_id",
            name="uq_candidate_election_constituency_party",
        ),

    )
