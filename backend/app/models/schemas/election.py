# election.py - Election schemas for the e-voting system.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from app.models.sqlalchemy.election import ElectionType, ElectionScope, ElectionStatus
from pydantic import Field
from datetime import datetime
from typing import Optional


class ElectionItem(ResponseSchema):
    """Election response model."""
    id: str = Field(..., description="The unique identifier for the election.")
    title: str = Field(..., description="The title of the election.")
    election_type: str = Field(..., description="The type of election.")
    scope: str = Field(..., description="The scope of the election.")
    allocation_method: str = Field(..., description="The allocation method for the election.")
    status: str = Field(..., description="The status of the election.")
    voting_opens: Optional[datetime] = Field(None, description="The date and time the election opens for voting.")
    voting_closes: Optional[datetime] = Field(None, description="The date and time the election closes for voting.")
    created_by: Optional[str] = Field(None, description="The ID of the election official who created this election.")


class CreateElectionRequest(RequestSchema):
    """Create election request model."""
    title: str = Field(..., description="The title of the election.")
    election_type: ElectionType = Field(..., description="The type of election.")
    scope: ElectionScope = Field(..., description="The scope of the election.")
    allocation_method: str = Field(..., description="The allocation method for the election.")
    status: ElectionStatus = Field(..., description="The status of the election.")
    voting_opens: Optional[datetime] = Field(None, description="The date and time the election opens for voting.")
    voting_closes: Optional[datetime] = Field(None, description="The date and time the election closes for voting.")
    created_by: Optional[str] = Field(None, description="The ID of the election official who created this election.")


class UpdateElectionRequest(RequestSchema):
    """Update election request model.

    Only status, voting_opens, and voting_closes can be modified
    after an election has been created. All other fields are immutable.
    """
    status: Optional[ElectionStatus] = Field(None, description="The status of the election.")
    voting_opens: Optional[datetime] = Field(None, description="The date and time the election opens for voting.")
    voting_closes: Optional[datetime] = Field(None, description="The date and time the election closes for voting.")
