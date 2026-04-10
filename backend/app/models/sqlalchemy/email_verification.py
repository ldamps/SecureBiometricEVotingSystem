"""Email verification code model.

Stores single-use 6-digit codes sent to a voter's registered email
address.  Used as an alternative verification method when biometric
verification is unavailable (e.g. lost or replaced phone).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin


class EmailVerificationCode(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Single-use 6-digit code for email-based voter verification."""

    __tablename__ = "email_verification_code"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(6), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    used_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
