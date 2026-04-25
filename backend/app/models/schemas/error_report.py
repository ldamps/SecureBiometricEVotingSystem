# error_report.py - Error report schemas for the e-voting system.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from app.models.sqlalchemy.error_report import ErrorReportSeverity
from pydantic import Field, model_validator
from typing import Optional
from datetime import datetime


class ErrorReportItem(ResponseSchema):
    """Error report response model."""
    id: str = Field(..., description="The unique identifier for the error report.")
    election_id: Optional[str] = Field(None, description="The election this report relates to (mutually exclusive with referendum_id).")
    referendum_id: Optional[str] = Field(None, description="The referendum this report relates to (mutually exclusive with election_id).")
    reported_by: Optional[str] = Field(None, description="The official who reported the error.")
    title: str = Field(..., description="Short summary of the error.")
    description: Optional[str] = Field(None, description="Detailed description of the error.")
    severity: str = Field(..., description="Severity level (LOW, MEDIUM, HIGH, CRITICAL).")
    reported_at: Optional[datetime] = Field(None, description="When the error was reported.")


class CreateErrorReportRequest(RequestSchema):
    """Create an error report for an election or referendum."""
    election_id: Optional[str] = Field(None, description="The election this report relates to (mutually exclusive with referendum_id).")
    referendum_id: Optional[str] = Field(None, description="The referendum this report relates to (mutually exclusive with election_id).")
    reported_by: Optional[str] = Field(None, description="The official reporting the error.")
    title: str = Field(..., min_length=3, max_length=255, description="Short summary of the error.")
    description: Optional[str] = Field(None, max_length=5000, description="Detailed description.")
    severity: ErrorReportSeverity = Field(..., description="Severity level.")

    @model_validator(mode="after")
    def _exactly_one_target(self) -> "CreateErrorReportRequest":
        if bool(self.election_id) == bool(self.referendum_id):
            raise ValueError("Exactly one of election_id or referendum_id must be provided.")
        return self


class ErrorReportWithInvestigationItem(ResponseSchema):
    """Error report response that includes the auto-created investigation."""
    error_report: ErrorReportItem = Field(..., description="The created error report.")
    investigation: "InvestigationItem" = Field(..., description="The auto-opened investigation.")


# Avoid circular import — resolve forward ref after InvestigationItem is available
from app.models.schemas.investigation import InvestigationItem  # noqa: E402
ErrorReportWithInvestigationItem.model_rebuild()
