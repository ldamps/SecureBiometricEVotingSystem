"""Election official model - staff who manage elections."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedBytes, TimestampMixin, UUIDPrimaryKeyMixin


class ElectionOfficial(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Election official (admin/staff) with role and constituency."""

    __tablename__ = "election_official"

    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    last_name: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    email_hash: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    constituency_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_reset_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election_official.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    
    # Relationships ----------

    # Database constraints + indexes ----------
