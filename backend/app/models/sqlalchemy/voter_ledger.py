"""Voter ledger - records that a voter participated in an election or referendum."""

from __future__ import annotations

import uuid
from datetime import datetime

from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.sqlalchemy.voter import Voter
    from app.models.sqlalchemy.election import Election
    from app.models.sqlalchemy.referendum import Referendum


class VoterLedger(Base, UUIDPrimaryKeyMixin):
    """Records that a voter has participated in a given election or referendum.

    Exactly one of ``election_id`` / ``referendum_id`` must be set.
    """

    __tablename__ = "voter_ledger"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    election_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    referendum_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("referendum.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    voted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------
    voter: Mapped["Voter"] = relationship(
        "Voter",
        back_populates="voter_ledger",
        lazy="select",
    )

    election: Mapped["Election | None"] = relationship(
        "Election",
        back_populates="voter_ledger",
        lazy="select",
    )

    referendum: Mapped["Referendum | None"] = relationship(
        "Referendum",
        back_populates="voter_ledger",
        lazy="select",
    )

    # Database constraints + indexes ----------
    __table_args__ = (
        CheckConstraint(
            "(election_id IS NOT NULL AND referendum_id IS NULL) OR "
            "(election_id IS NULL AND referendum_id IS NOT NULL)",
            name="ck_voter_ledger_election_xor_referendum",
        ),
    )