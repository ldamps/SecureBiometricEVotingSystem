# app/models/dto/audit_log.py - DTOs for audit log operations.

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.audit_log import AuditLogItem


@dataclass
class AuditLogBaseDTO:
    """Base DTO for audit logs."""
    __resource__: ClassVar[Resource] = Resource.AUDIT_LOG
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class AuditLogDTO(AuditLogBaseDTO):
    """Plaintext audit log DTO — source for to_schema."""

    id: UUID = None
    event_type: str = ""
    action: str = ""
    summary: str = ""
    actor_id: Optional[UUID] = None
    actor_type: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    election_id: Optional[UUID] = None
    referendum_id: Optional[UUID] = None
    event_metadata: Optional[dict] = None
    created_at: Optional[datetime] = None

    def to_schema(self) -> AuditLogItem:
        return AuditLogItem(
            id=str(self.id),
            event_type=self.event_type,
            action=self.action,
            summary=self.summary,
            actor_id=str(self.actor_id) if self.actor_id else None,
            actor_type=self.actor_type,
            resource_type=self.resource_type,
            resource_id=str(self.resource_id) if self.resource_id else None,
            election_id=str(self.election_id) if self.election_id else None,
            referendum_id=str(self.referendum_id) if self.referendum_id else None,
            event_metadata=self.event_metadata,
            created_at=self.created_at,
        )


@dataclass
class CreateAuditLogDTO:
    """Fields needed to create an audit log entry."""

    event_type: str
    action: str
    summary: str
    actor_id: Optional[UUID] = None
    actor_type: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    election_id: Optional[UUID] = None
    referendum_id: Optional[UUID] = None
    event_metadata: Optional[dict] = None
