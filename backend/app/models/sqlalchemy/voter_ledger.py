"""Voter ledger - records that a voter participated in an election."""

from __future__ import annotations

import uuid
from datetime import datetime

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.sqlalchemy.voter import Voter
    from app.models.sqlalchemy.election import Election


class VoterLedger(Base, UUIDPrimaryKeyMixin):
    """Records that a voter has voted in a given election (one row per voter per election)."""

    __tablename__ = "voter_ledger"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    election_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    voted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------
    voter: Mapped["Voter"] = relationship(
        "Voter",
        back_populates="voter_ledger",
        lazy="select",
    )

    election: Mapped["Election"] = relationship(
        "Election",
        back_populates="voter_ledger",
        lazy="select",
    )

    # Database constraints + indexes ----------