# investigation.py - Investigation schemas for the e-voting system.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from typing import Optional
from datetime import datetime


class InvestigationItem(ResponseSchema):
    """Investigation response model."""
    id: str = Field(..., description="The unique identifier for the investigation.")
    error_id: str = Field(..., description="The error report that triggered this investigation.")
    election_id: Optional[str] = Field(None, description="The election this investigation relates to (mutually exclusive with referendum_id).")
    referendum_id: Optional[str] = Field(None, description="The referendum this investigation relates to (mutually exclusive with election_id).")
    raised_by: Optional[str] = Field(None, description="The official who raised the investigation.")
    title: str = Field(..., description="Title of the investigation.")
    description: Optional[str] = Field(None, description="Details of the investigation.")
    severity: str = Field(..., description="Severity level.")
    status: str = Field(..., description="Current status (OPEN, IN_PROGRESS, RESOLVED, CLOSED).")
    category: Optional[str] = Field(None, description="Category of the issue.")
    assigned_to: Optional[str] = Field(None, description="Official assigned to investigate.")
    notes: Optional[str] = Field(None, description="Internal notes on the investigation.")
    resolved_by: Optional[str] = Field(None, description="Official who resolved the investigation.")
    resolution_summary: Optional[str] = Field(None, description="Human-written summary of findings and actions taken to resolve the issue.")
    raised_at: Optional[datetime] = Field(None, description="When the investigation was opened.")
    resolved_at: Optional[datetime] = Field(None, description="When the investigation was resolved.")


class UpdateInvestigationRequest(RequestSchema):
    """Update an investigation's mutable fields."""
    status: Optional[str] = Field(None, description="Updated status (OPEN, IN_PROGRESS, RESOLVED, CLOSED).")
    category: Optional[str] = Field(None, max_length=255, description="Updated category.")
    assigned_to: Optional[str] = Field(None, description="Official ID to assign the investigation to.")
    notes: Optional[str] = Field(None, max_length=5000, description="Updated internal notes.")
    resolved_by: Optional[str] = Field(None, description="Official ID who resolved the investigation.")
    resolution_summary: Optional[str] = Field(None, max_length=5000, description="Required when resolving/closing. Summary of findings and actions taken.")
