"""Audit log model - immutable event log for security-relevant actions."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin


class AuditEventType(str, enum.Enum):
    """Categorised event types for auditing."""

    # Voter lifecycle
    VOTER_REGISTERED = "VOTER_REGISTERED"
    VOTER_UPDATED = "VOTER_UPDATED"
    VOTER_SUSPENDED = "VOTER_SUSPENDED"
    VOTER_REACTIVATED = "VOTER_REACTIVATED"

    # Election lifecycle
    ELECTION_CREATED = "ELECTION_CREATED"
    ELECTION_UPDATED = "ELECTION_UPDATED"
    ELECTION_STATUS_CHANGED = "ELECTION_STATUS_CHANGED"

    # Voting
    VOTE_CAST = "VOTE_CAST"
    BALLOT_TOKEN_ISSUED = "BALLOT_TOKEN_ISSUED"

    # Candidates / parties
    CANDIDATE_ADDED = "CANDIDATE_ADDED"
    CANDIDATE_REMOVED = "CANDIDATE_REMOVED"

    # Officials
    OFFICIAL_CREATED = "OFFICIAL_CREATED"
    OFFICIAL_LOGIN = "OFFICIAL_LOGIN"
    OFFICIAL_LOGIN_FAILED = "OFFICIAL_LOGIN_FAILED"
    OFFICIAL_LOGOUT = "OFFICIAL_LOGOUT"

    # Biometrics
    BIOMETRIC_ENROLLED = "BIOMETRIC_ENROLLED"
    BIOMETRIC_VERIFIED = "BIOMETRIC_VERIFIED"
    BIOMETRIC_FAILED = "BIOMETRIC_FAILED"

    # Error reporting / investigations
    ERROR_REPORT_CREATED = "ERROR_REPORT_CREATED"
    INVESTIGATION_OPENED = "INVESTIGATION_OPENED"
    INVESTIGATION_UPDATED = "INVESTIGATION_UPDATED"
    INVESTIGATION_RESOLVED = "INVESTIGATION_RESOLVED"

    # System
    SYSTEM_ERROR = "SYSTEM_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    DATA_EXPORT = "DATA_EXPORT"


class AuditActorType(str, enum.Enum):
    """Who performed the action."""

    OFFICIAL = "OFFICIAL"
    VOTER = "VOTER"
    SYSTEM = "SYSTEM"


class AuditAction(str, enum.Enum):
    """High-level CRUD action category."""

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    VERIFY = "VERIFY"
    EXPORT = "EXPORT"


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Immutable audit log entry for security-relevant events.

    Rows in this table must never be updated or deleted.
    """

    __tablename__ = "audit_log"

    # What happened
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)

    # Who did it
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True,
    )
    actor_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # What was affected
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True,
    )

    # Optional election/referendum scope (for scoped queries)
    election_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True,
    )
    referendum_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True,
    )

    # Structured metadata
    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Immutable timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.timezone("utc", func.now()),
    )

    # Database constraints + indexes ----------
