# election.py - Election schemas for the e-voting system.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from app.models.sqlalchemy.election import (
    ElectionType,
    ElectionScope,
    ElectionStatus,
    AllocationMethod,
    ELECTION_TYPE_ALLOCATION_MAP,
)
from pydantic import Field, model_validator
from datetime import datetime
from typing import Optional


class ElectionItem(ResponseSchema):
    """Election response model."""
    id: str = Field(..., description="The unique identifier for the election.")
    title: str = Field(..., description="The title of the election.")
    election_type: str = Field(..., description="The type of election.")
    scope: str = Field(..., description="The scope of the election.")
    allocation_method: str = Field(..., description="The electoral system (derived from election type).")
    status: str = Field(..., description="The status of the election.")
    voting_opens: Optional[datetime] = Field(None, description="The date and time the election opens for voting.")
    voting_closes: Optional[datetime] = Field(None, description="The date and time the election closes for voting.")
    created_by: Optional[str] = Field(None, description="The ID of the election official who created this election.")


class CreateElectionRequest(RequestSchema):
    """Create election request model.

    The allocation_method is automatically derived from the election_type
    based on the UK electoral system mapping. It does not need to be provided.
    """
    title: str = Field(..., description="The title of the election.")
    election_type: ElectionType = Field(..., description="The type of election.")
    scope: ElectionScope = Field(..., description="The scope of the election.")
    allocation_method: Optional[str] = Field(None, description="Auto-derived from election_type. Ignored if provided.")
    status: ElectionStatus = Field(..., description="The status of the election.")
    voting_opens: Optional[datetime] = Field(None, description="The date and time the election opens for voting.")
    voting_closes: Optional[datetime] = Field(None, description="The date and time the election closes for voting.")
    created_by: Optional[str] = Field(None, description="The ID of the election official who created this election.")

    @model_validator(mode="after")
    def derive_allocation_method(self) -> "CreateElectionRequest":
        """Automatically set allocation_method from the election_type."""
        self.allocation_method = ELECTION_TYPE_ALLOCATION_MAP[self.election_type].value
        return self


class UpdateElectionRequest(RequestSchema):
    """Update election request model.

    Only status, voting_opens, and voting_closes can be modified
    after an election has been created. All other fields are immutable.
    """
    status: Optional[ElectionStatus] = Field(None, description="The status of the election.")
    voting_opens: Optional[datetime] = Field(None, description="The date and time the election opens for voting.")
    voting_closes: Optional[datetime] = Field(None, description="The date and time the election closes for voting.")
