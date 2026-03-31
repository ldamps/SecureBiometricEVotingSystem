# result.py - Response schemas for aggregated election/referendum results.
# Modelled on the UK FPTP parliamentary system (650 constituencies, 326 majority).

from typing import Dict, List, Optional

from pydantic import Field

from app.models.base.pydantic_base import ResponseSchema
from app.models.schemas.tally_result import TallyResultItem


class ConstituencyResultItem(ResponseSchema):
    """Aggregated result for a single constituency (one seat)."""
    id: str = Field(default="", description="Constituency ID.")
    constituency_id: str
    winner_candidate_id: Optional[str] = None
    winner_name: Optional[str] = None
    winner_party_id: Optional[str] = None
    total_votes: int = 0
    tallies: List[TallyResultItem] = Field(default_factory=list)


class ElectionResultResponse(ResponseSchema):
    """Full election result with per-constituency breakdowns and seat allocation.

    In UK general elections each constituency elects one MP via FPTP.
    The party that wins 326+ of 650 seats forms the government.
    """
    id: str = Field(default="", description="Election ID.")
    election_id: str
    election_title: Optional[str] = None
    status: str = ""
    total_votes: int = 0
    total_seats: int = Field(0, description="Total number of constituencies contested.")
    majority_threshold: int = Field(0, description="Seats required for a majority (total_seats // 2 + 1).")
    constituencies: List[ConstituencyResultItem] = Field(default_factory=list)
    seat_allocation: Dict[str, int] = Field(
        default_factory=dict,
        description="Party ID -> number of seats won (FPTP).",
    )
    winning_party_id: Optional[str] = Field(
        None,
        description="Party ID that reached the majority threshold, or null if no majority.",
    )


class ReferendumResultResponse(ResponseSchema):
    """Aggregated referendum result."""
    id: str = Field(default="", description="Referendum ID.")
    referendum_id: str
    yes_votes: int = 0
    no_votes: int = 0
    total_votes: int = 0
    outcome: str = Field(..., description="YES, NO, or TIE.")
