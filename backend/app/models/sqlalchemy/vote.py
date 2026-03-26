"""Vote model - a single cast vote."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin


class Vote(Base, UUIDPrimaryKeyMixin):
    """A vote cast in an election for a candidate (linked by blind_token_hash)."""

    __tablename__ = "vote"

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
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blind_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    receipt_code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cast_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------