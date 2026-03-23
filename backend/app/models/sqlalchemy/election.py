"""Election model - a single election event."""

from __future__ import annotations

import uuid
from datetime import datetime
import enum
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base.sqlalchemy_base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.sqlalchemy.voter_ledger import VoterLedger
    from app.models.sqlalchemy.election_official import ElectionOfficial


class ElectionType(str, enum.Enum):
    """
    Election type.
    ** GENERAL ** - General election.
    ** REFERENDUM ** - Referendum.
    ** LOCAL ** - Local election.
    """
    ELECTION = "ELECTION"
    REFERENDUM = "REFERENDUM"

class ElectionScope(str, enum.Enum):
    """
    Election scope.
    ** NATIONAL ** - National scope (entire country).
    ** REGIONAL ** - Regional scope (specific region).
    ** LOCAL ** - Local scope (specific constituency/ward).
    """
    NATIONAL = "NATIONAL"
    REGIONAL = "REGIONAL"
    LOCAL = "LOCAL"

class ElectionStatus(str, enum.Enum):
    """
    Election status.
    ** OPEN ** - Election is open for voting.
    ** CLOSED ** - Election is closed for voting
    """
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Election(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Election with opening/closing times and status."""

    __tablename__ = "election"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    election_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    allocation_method: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    voting_opens: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    voting_closes: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election_official.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships ----------

    voter_ledger: Mapped[list["VoterLedger"]] = relationship(
        "VoterLedger",
        back_populates="election",
    )

    creator: Mapped["ElectionOfficial | None"] = relationship(
        "ElectionOfficial",
        foreign_keys=[created_by],
    )

    # Database constraints + indexes ----------
