# tally_result.py - Response schemas for tally results.

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.base.pydantic_base import ResponseSchema


class TallyResultItem(ResponseSchema):
    """A single tally row — either an election candidate count or a referendum choice count."""
    id: str
    election_id: Optional[str] = None
    constituency_id: Optional[str] = None
    candidate_id: Optional[str] = None
    party_id: Optional[str] = None
    referendum_id: Optional[str] = None
    choice: Optional[str] = None
    vote_count: int = Field(..., description="Total votes counted.")
    tallied_at: Optional[datetime] = None
