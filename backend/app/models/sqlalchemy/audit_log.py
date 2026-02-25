"""Audit log model - immutable event log."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base.sqlalchemy_base import Base, EncryptedBytes


class AuditLog(Base):
    """Immutable audit log entry for security-relevant events."""

    __tablename__ = "audit_log"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column(EncryptedBytes, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.timezone("utc", func.now()),
    )

    # Relationships ----------

    # Database constraints + indexes ----------
