# candidate.py - Candidate schemas for the e-voting system.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from typing import Optional
from uuid import UUID


class CandidateItem(ResponseSchema):
    """Candidate response model."""
    id: str = Field(..., description="The unique identifier for the candidate.")
    election_id: str = Field(..., description="The election the candidate is standing in.")
    constituency_id: str = Field(..., description="The constituency the candidate is standing in.")
    first_name: str = Field(..., description="The candidate's first name.")
    last_name: str = Field(..., description="The candidate's last name.")
    party_id: str = Field(..., description="The party the candidate represents.")
    is_active: bool = Field(..., description="Whether the candidate is currently active.")


class CreateCandidateRequest(RequestSchema):
    """Create candidate request model."""
    constituency_id: UUID = Field(..., description="The constituency the candidate is standing in.")
    first_name: str = Field(..., description="The candidate's first name.")
    last_name: str = Field(..., description="The candidate's last name.")
    party_id: UUID = Field(..., description="The party the candidate represents.")


class UpdateCandidateRequest(RequestSchema):
    """Update candidate request model."""
    first_name: Optional[str] = Field(None, description="The candidate's first name.")
    last_name: Optional[str] = Field(None, description="The candidate's last name.")
    is_active: Optional[bool] = Field(None, description="Whether the candidate is currently active.")
