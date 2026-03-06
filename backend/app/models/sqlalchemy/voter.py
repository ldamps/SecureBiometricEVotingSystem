"""Voter model - registered voter."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedBytes, TimestampMixin


class Voter(Base, TimestampMixin):
    """Registered voter with encrypted PII and constituency."""

    __tablename__ = "voter"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    national_insurance_number: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    first_name: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    surname: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    previous_first_name: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    maiden_name: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    date_of_birth: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    email: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)  # UK in ER
    civil_servant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    council_employee: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    armed_forces_member: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voter_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    constituency_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.constituency_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    registration_status: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    failed_auth_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    registered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------
