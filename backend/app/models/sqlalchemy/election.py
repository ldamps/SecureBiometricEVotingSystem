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
    from app.models.sqlalchemy.candidate import Candidate


class ElectionType(str, enum.Enum):
    """UK election types — each maps to a specific electoral system."""

    # FPTP elections
    GENERAL = "GENERAL"
    LOCAL_ENGLAND_WALES = "LOCAL_ENGLAND_WALES"
    MAYORS = "MAYORS"
    POLICE_AND_CRIME_COMMISSIONER = "POLICE_AND_CRIME_COMMISSIONER"
    SCOTTISH_NATIONAL_PARK = "SCOTTISH_NATIONAL_PARK"

    # AMS elections
    SCOTTISH_PARLIAMENT = "SCOTTISH_PARLIAMENT"
    LONDON_ASSEMBLY = "LONDON_ASSEMBLY"

    # STV elections
    NORTHERN_IRELAND_ASSEMBLY = "NORTHERN_IRELAND_ASSEMBLY"
    LOCAL_NORTHERN_IRELAND_SCOTLAND = "LOCAL_NORTHERN_IRELAND_SCOTLAND"

    # Alternative Vote elections
    HOUSE_OF_LORDS_HEREDITARY = "HOUSE_OF_LORDS_HEREDITARY"
    SCOTTISH_CROFTING_COMMISSION = "SCOTTISH_CROFTING_COMMISSION"


class AllocationMethod(str, enum.Enum):
    """Electoral systems used in UK elections."""
    FPTP = "FPTP"
    AMS = "AMS"
    STV = "STV"
    ALTERNATIVE_VOTE = "ALTERNATIVE_VOTE"


# Deterministic mapping: election type -> allocation method.
ELECTION_TYPE_ALLOCATION_MAP: dict[ElectionType, AllocationMethod] = {
    # First Past The Post
    ElectionType.GENERAL: AllocationMethod.FPTP,
    ElectionType.LOCAL_ENGLAND_WALES: AllocationMethod.FPTP,
    ElectionType.MAYORS: AllocationMethod.FPTP,
    ElectionType.POLICE_AND_CRIME_COMMISSIONER: AllocationMethod.FPTP,
    ElectionType.SCOTTISH_NATIONAL_PARK: AllocationMethod.FPTP,
    # Additional Member System
    ElectionType.SCOTTISH_PARLIAMENT: AllocationMethod.AMS,
    ElectionType.LONDON_ASSEMBLY: AllocationMethod.AMS,
    # Single Transferable Vote
    ElectionType.NORTHERN_IRELAND_ASSEMBLY: AllocationMethod.STV,
    ElectionType.LOCAL_NORTHERN_IRELAND_SCOTLAND: AllocationMethod.STV,
    # Alternative Vote
    ElectionType.HOUSE_OF_LORDS_HEREDITARY: AllocationMethod.ALTERNATIVE_VOTE,
    ElectionType.SCOTTISH_CROFTING_COMMISSION: AllocationMethod.ALTERNATIVE_VOTE,
}

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

    candidates: Mapped[list["Candidate"]] = relationship(
        "Candidate",
        back_populates="election",
    )

    # Database constraints + indexes ----------
