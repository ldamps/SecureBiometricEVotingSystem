# result.py - Response schemas for aggregated election/referendum results.

from typing import Dict, List, Optional

from pydantic import Field

from app.models.base.pydantic_base import ResponseSchema
from app.models.schemas.tally_result import TallyResultItem


class ConstituencyResultItem(ResponseSchema):
    """Aggregated result for a single constituency."""
    id: str = Field(default="", description="Constituency ID.")
    constituency_id: str
    winner_candidate_id: Optional[str] = None
    winner_name: Optional[str] = None
    winner_party_id: Optional[str] = None
    total_votes: int = 0
    tallies: List[TallyResultItem] = Field(default_factory=list)


class ElectionResultResponse(ResponseSchema):
    """Full election result with per-constituency breakdowns and seat allocation."""
    id: str = Field(default="", description="Election ID.")
    election_id: str
    election_title: Optional[str] = None
    status: str = ""
    total_votes: int = 0
    constituencies: List[ConstituencyResultItem] = Field(default_factory=list)
    seat_allocation: Dict[str, int] = Field(
        default_factory=dict,
        description="Party ID -> number of seats won (FPTP).",
    )


class ReferendumResultResponse(ResponseSchema):
    """Aggregated referendum result."""
    id: str = Field(default="", description="Referendum ID.")
    referendum_id: str
    yes_votes: int = 0
    no_votes: int = 0
    total_votes: int = 0
    outcome: str = Field(..., description="YES, NO, or TIE.")
