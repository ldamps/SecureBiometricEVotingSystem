"""Election model - a single election event."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


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

    # Database constraints + indexes ----------
