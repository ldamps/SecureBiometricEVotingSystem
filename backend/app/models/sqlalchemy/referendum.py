"""Referendum model - a standalone yes/no question posed to voters."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.sqlalchemy.voter_ledger import VoterLedger
    from app.models.sqlalchemy.constituency import Constituency


class ReferendumStatus(str, enum.Enum):
    """Persisted referendum lifecycle status (stored as string in DB)."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


# Many-to-many association table: referendum <-> constituency
referendum_constituency = Table(
    "referendum_constituency",
    Base.metadata,
    Column(
        "referendum_id",
        PG_UUID(as_uuid=True),
        ForeignKey("referendum.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "constituency_id",
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Referendum(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A standalone yes/no referendum question presented to voters."""

    __tablename__ = "referendum"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False, default="OPEN", index=True)
    voting_opens: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    voting_closes: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships ----------
    constituencies: Mapped[list["Constituency"]] = relationship(
        "Constituency",
        secondary=referendum_constituency,
    )
    voter_ledger: Mapped[list["VoterLedger"]] = relationship(
        "VoterLedger",
        back_populates="referendum",
    )
