"""Ballot token model - one-time token per ballot (elections and referendums)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin


class BallotToken(Base, UUIDPrimaryKeyMixin):
    """One-time ballot token (blind token hash) for an election or referendum.

    Exactly one of ``election_id`` / ``referendum_id`` must be set.
    ``constituency_id`` is required for election tokens but NULL for referendums.
    """

    __tablename__ = "ballot_token"

    # Election tokens (nullable — NULL when this is a referendum token)
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

    # Referendum tokens (nullable — NULL when this is an election token)
    referendum_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("referendum.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    blind_token_hash: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    issued_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------
    __table_args__ = (
        CheckConstraint(
            "(election_id IS NOT NULL AND referendum_id IS NULL) OR "
            "(election_id IS NULL AND referendum_id IS NOT NULL)",
            name="ck_ballot_token_election_xor_referendum",
        ),
    )
