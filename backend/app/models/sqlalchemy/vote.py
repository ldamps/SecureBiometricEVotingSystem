"""Vote model - a single cast vote.

Supports multiple electoral systems:
- FPTP / AMS constituency: single candidate_id, no preference_rank.
- AMS regional list: party_id set, candidate_id NULL.
- STV / Alternative Vote: multiple rows per ballot sharing the same
  blind_token_hash prefix, each with a different preference_rank.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedColumn, EncryptedDBField, UUIDPrimaryKeyMixin


class Vote(Base, UUIDPrimaryKeyMixin):
    """A vote cast in an election (linked by blind_token_hash)."""

    __tablename__ = "vote"

    election_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    constituency_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    party_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("party.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Set for AMS regional-list votes.",
    )
    preference_rank: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Preference rank (1 = first choice). Set for STV and AV votes.",
    )
    blind_token_hash: Mapped[EncryptedDBField] = mapped_column(EncryptedColumn, nullable=False)
    blind_token_hash_search_token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    receipt_code: Mapped[EncryptedDBField] = mapped_column(EncryptedColumn, nullable=False)
    receipt_code_search_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cast_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------