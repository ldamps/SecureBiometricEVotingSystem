"""Referendum vote model - a single anonymous cast vote on a referendum (YES/NO)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin


class ReferendumVote(Base, UUIDPrimaryKeyMixin):
    """An anonymous vote cast on a referendum (linked by blind_token_hash)."""

    __tablename__ = "referendum_vote"

    referendum_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("referendum.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    choice: Mapped[str] = mapped_column(
        String(3), nullable=False, index=True,
        comment="YES or NO",
    )
    blind_token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    receipt_code: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cast_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True,
    )

    # Relationships ----------

    # Database constraints + indexes ----------
