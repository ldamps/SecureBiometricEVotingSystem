# app/models/dto/investigation.py - DTOs for investigation operations.

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.investigation import InvestigationItem, UpdateInvestigationRequest


@dataclass
class InvestigationBaseDTO:
    """Base DTO for investigations."""
    __resource__: ClassVar[Resource] = Resource.INVESTIGATION
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class InvestigationDTO(InvestigationBaseDTO):
    """Plaintext investigation DTO — source for to_schema."""

    id: UUID = None
    error_id: UUID = None
    election_id: UUID = None
    raised_by: Optional[UUID] = None
    title: str = ""
    description: Optional[str] = None
    severity: str = ""
    status: str = ""
    category: Optional[str] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    resolved_by: Optional[UUID] = None
    raised_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def to_schema(self) -> InvestigationItem:
        return InvestigationItem(
            id=str(self.id),
            error_id=str(self.error_id),
            election_id=str(self.election_id),
            raised_by=str(self.raised_by) if self.raised_by else None,
            title=self.title,
            description=self.description,
            severity=self.severity,
            status=self.status,
            category=self.category,
            assigned_to=str(self.assigned_to) if self.assigned_to else None,
            notes=self.notes,
            resolved_by=str(self.resolved_by) if self.resolved_by else None,
            raised_at=self.raised_at,
            resolved_at=self.resolved_at,
        )


@dataclass
class UpdateInvestigationPlainDTO(InvestigationBaseDTO):
    """Plaintext fields for updating an investigation."""

    investigation_id: Optional[UUID] = None
    status: Optional[str] = None
    category: Optional[str] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    resolved_by: Optional[UUID] = None

    @classmethod
    def create_dto(cls, data: UpdateInvestigationRequest, investigation_id: UUID) -> "UpdateInvestigationPlainDTO":
        d = data.model_dump(exclude_none=True)
        if "assigned_to" in d:
            d["assigned_to"] = UUID(d["assigned_to"]) if isinstance(d["assigned_to"], str) else d["assigned_to"]
        if "resolved_by" in d:
            d["resolved_by"] = UUID(d["resolved_by"]) if isinstance(d["resolved_by"], str) else d["resolved_by"]
        return cls(**d, investigation_id=investigation_id)
