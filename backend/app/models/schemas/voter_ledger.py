from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from datetime import datetime
from typing import Optional


class VoterLedgerItem(ResponseSchema):
    """Voter ledger response model."""
    id: str = Field(..., description="The unique identifier for the voter ledger entry.")
    voter_id: str = Field(..., description="The unique identifier for the voter.")
    election_id: str = Field(..., description="The unique identifier for the election.")
    voted_at: Optional[datetime] = Field(None, description="The date and time the voter voted.")

class CreateVoterLedgerRequest(RequestSchema):
    """Request to create a voter ledger entry."""
    election_id: str = Field(..., description="The unique identifier for the election.")
    voted_at: Optional[datetime] = Field(None, description="The date and time the voter voted.")
