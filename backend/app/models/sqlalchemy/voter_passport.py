# voter_passport.py - Voter passport model for the e-voting system.

from __future__ import annotations

import uuid
from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedColumn, EncryptedDBField, TimestampMixin, UUIDPrimaryKeyMixin


class VoterPassport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A passport held by a voter.

    Voters may hold multiple passports (dual/multiple nationality).
    At least one passport must support the voter's eligibility claim
    unless the voter has an NI number.

    Encrypted PII fields follow the same pattern as the Voter model:
    JSONB EncryptedDBField columns with companion search-token columns
    for blind-index lookups.
    """

    __tablename__ = "voter_passport"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Encrypted PII fields
    passport_number: Mapped[EncryptedDBField | None] = mapped_column(
        EncryptedColumn, nullable=True
    )
    passport_number_search_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )

    issuing_country: Mapped[EncryptedDBField | None] = mapped_column(
        EncryptedColumn, nullable=True
    )

    expiry_date: Mapped[EncryptedDBField | None] = mapped_column(
        EncryptedColumn, nullable=True
    )

    # Non-encrypted fields
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    voter: Mapped["Voter"] = relationship(
        "Voter",
        back_populates="passports",
    )

    __table_args__ = (
        UniqueConstraint(
            "passport_number_search_token",
            name="uq_voter_passport_passport_number_search_token",
        ),
    )
