from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from datetime import datetime
from typing import List, Optional


class VoterLedgerItem(ResponseSchema):
    """Voter ledger response model."""
    id: str = Field(..., description="The unique identifier for the voter ledger entry.")
    voter_id: str = Field(..., description="The unique identifier for the voter.")
    election_id: Optional[str] = Field(None, description="The unique identifier for the election.")
    referendum_id: Optional[str] = Field(None, description="The unique identifier for the referendum.")
    voted_at: Optional[datetime] = Field(None, description="The date and time the voter voted.")

class CreateVoterLedgerRequest(RequestSchema):
    """Request to create a voter ledger entry."""
    election_id: str = Field(..., description="The unique identifier for the election.")
    voted_at: Optional[datetime] = Field(None, description="The date and time the voter voted.")


class ElectionVoterItem(ResponseSchema):
    """A voter's participation status for an election."""
    voter_id: str = Field(..., description="The unique identifier for the voter.")
    first_name: Optional[str] = Field(None, description="The first name of the voter.")
    surname: Optional[str] = Field(None, description="The surname of the voter.")
    has_voted: bool = Field(..., description="Whether the voter has cast their vote.")
    voted_at: Optional[datetime] = Field(None, description="The date and time the voter voted.")


class ElectionVoterListResponse(ResponseSchema):
    """Response listing all voters for an election with their voting status."""
    election_id: str = Field(..., description="The unique identifier for the election.")
    total_voters: int = Field(..., description="Total number of registered voters for this election.")
    total_voted: int = Field(..., description="Number of voters who have voted.")
    total_not_voted: int = Field(..., description="Number of voters who have not voted.")
    voters: List[ElectionVoterItem] = Field(default_factory=list, description="List of voters and their voting status.")


class ReferendumVoterListResponse(ResponseSchema):
    """Response listing all voters for a referendum with their voting status."""
    referendum_id: str = Field(..., description="The unique identifier for the referendum.")
    total_voters: int = Field(..., description="Total number of registered voters for this referendum.")
    total_voted: int = Field(..., description="Number of voters who have voted.")
    total_not_voted: int = Field(..., description="Number of voters who have not voted.")
    voters: List[ElectionVoterItem] = Field(default_factory=list, description="List of voters and their voting status.")
