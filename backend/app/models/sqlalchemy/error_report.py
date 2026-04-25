"""Error report model - reported issue for an election or referendum."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedColumn, EncryptedDBField, UUIDPrimaryKeyMixin


class ErrorReportSeverity(str, enum.Enum):
    """Error report severity."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorReport(Base, UUIDPrimaryKeyMixin):
    """Error or issue reported for an election or referendum by an official.

    Exactly one of ``election_id`` / ``referendum_id`` must be set.
    """

    __tablename__ = "error_report"

    election_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    referendum_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("referendum.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    reported_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("election_official.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    severity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reported_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------
    __table_args__ = (
        CheckConstraint(
            "(election_id IS NOT NULL AND referendum_id IS NULL) OR "
            "(election_id IS NULL AND referendum_id IS NOT NULL)",
            name="ck_error_report_election_xor_referendum",
        ),
    )
