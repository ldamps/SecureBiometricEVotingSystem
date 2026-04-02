# audit_log.py - Audit log schemas for the e-voting system.

from app.models.base.pydantic_base import ResponseSchema
from pydantic import Field
from typing import Any, Dict, Optional
from datetime import datetime


class AuditLogItem(ResponseSchema):
    """Audit log response model."""
    id: str = Field(..., description="The unique identifier for the audit log entry.")
    event_type: str = Field(..., description="Categorised event type (e.g. VOTER_REGISTERED, VOTE_CAST).")
    action: str = Field(..., description="High-level action (CREATE, READ, UPDATE, DELETE, LOGIN, etc.).")
    summary: str = Field(..., description="Human-readable summary of what happened.")
    actor_id: Optional[str] = Field(None, description="ID of the user who performed the action.")
    actor_type: Optional[str] = Field(None, description="Type of actor (OFFICIAL, VOTER, SYSTEM).")
    resource_type: Optional[str] = Field(None, description="Type of resource affected (e.g. voter, election).")
    resource_id: Optional[str] = Field(None, description="ID of the resource affected.")
    election_id: Optional[str] = Field(None, description="Election scope (if applicable).")
    event_metadata: Optional[Dict[str, Any]] = Field(None, description="Structured metadata for the event.")
    created_at: Optional[datetime] = Field(None, description="When the event occurred (UTC).")
