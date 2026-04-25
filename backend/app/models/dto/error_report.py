# app/models/dto/error_report.py - DTOs for error report operations.

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.error_report import ErrorReportItem, CreateErrorReportRequest
from app.models.sqlalchemy.error_report import ErrorReport, ErrorReportSeverity


@dataclass
class ErrorReportBaseDTO:
    """Base DTO for error reports."""
    __resource__: ClassVar[Resource] = Resource.ERROR_REPORT
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class ErrorReportDTO(ErrorReportBaseDTO):
    """Plaintext error report DTO — source for to_schema."""

    id: UUID = None
    election_id: Optional[UUID] = None
    referendum_id: Optional[UUID] = None
    reported_by: Optional[UUID] = None
    title: str = ""
    description: Optional[str] = None
    severity: str = ""
    reported_at: Optional[datetime] = None

    def to_schema(self) -> ErrorReportItem:
        return ErrorReportItem(
            id=str(self.id),
            election_id=str(self.election_id) if self.election_id else None,
            referendum_id=str(self.referendum_id) if self.referendum_id else None,
            reported_by=str(self.reported_by) if self.reported_by else None,
            title=self.title,
            description=self.description,
            severity=self.severity,
            reported_at=self.reported_at,
        )


@dataclass
class CreateErrorReportPlainDTO(ErrorReportBaseDTO):
    """Plaintext fields for creating an error report."""

    election_id: Optional[UUID] = None
    referendum_id: Optional[UUID] = None
    reported_by: Optional[UUID] = None
    title: str = ""
    description: Optional[str] = None
    severity: str = ""

    @classmethod
    def create_dto(cls, data: CreateErrorReportRequest) -> "CreateErrorReportPlainDTO":
        d = data.model_dump()
        if d.get("election_id"):
            d["election_id"] = UUID(d["election_id"]) if isinstance(d["election_id"], str) else d["election_id"]
        else:
            d["election_id"] = None
        if d.get("referendum_id"):
            d["referendum_id"] = UUID(d["referendum_id"]) if isinstance(d["referendum_id"], str) else d["referendum_id"]
        else:
            d["referendum_id"] = None
        if d.get("reported_by"):
            d["reported_by"] = UUID(d["reported_by"]) if isinstance(d["reported_by"], str) else d["reported_by"]
        d["severity"] = d["severity"].value if isinstance(d["severity"], ErrorReportSeverity) else d["severity"]
        return cls(**d)
