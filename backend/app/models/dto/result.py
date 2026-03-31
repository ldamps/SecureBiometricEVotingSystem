# result.py - DTOs for aggregated election/referendum results.

from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.dto.tally_result import TallyResultDTO
from app.models.schemas.result import (
    ConstituencyResultItem,
    ElectionResultResponse,
    ReferendumResultResponse,
)
from app.models.schemas.tally_result import TallyResultItem


@dataclass
class ConstituencyResultDTO:
    """Aggregated result for a single constituency."""
    constituency_id: UUID
    winner_candidate_id: Optional[UUID] = None
    winner_name: Optional[str] = None
    winner_party_id: Optional[UUID] = None
    total_votes: int = 0
    tallies: List[TallyResultDTO] = field(default_factory=list)

    def to_schema(self) -> ConstituencyResultItem:
        return ConstituencyResultItem(
            id=str(self.constituency_id),
            constituency_id=str(self.constituency_id),
            winner_candidate_id=str(self.winner_candidate_id) if self.winner_candidate_id else None,
            winner_name=self.winner_name,
            winner_party_id=str(self.winner_party_id) if self.winner_party_id else None,
            total_votes=self.total_votes,
            tallies=[t.to_schema() for t in self.tallies],
        )


@dataclass
class ElectionResultDTO:
    """Full election result."""
    __resource__: ClassVar[Resource] = Resource.RESULT
    election_id: UUID = field(default=None)
    election_title: Optional[str] = None
    status: str = ""
    total_votes: int = 0
    constituencies: List[ConstituencyResultDTO] = field(default_factory=list)
    seat_allocation: Dict[str, int] = field(default_factory=dict)

    def to_schema(self) -> ElectionResultResponse:
        return ElectionResultResponse(
            id=str(self.election_id),
            election_id=str(self.election_id),
            election_title=self.election_title,
            status=self.status,
            total_votes=self.total_votes,
            constituencies=[c.to_schema() for c in self.constituencies],
            seat_allocation=self.seat_allocation,
        )


@dataclass
class ReferendumResultDTO:
    """Aggregated referendum result."""
    __resource__: ClassVar[Resource] = Resource.RESULT
    referendum_id: UUID = field(default=None)
    yes_votes: int = 0
    no_votes: int = 0
    total_votes: int = 0
    outcome: str = ""

    def to_schema(self) -> ReferendumResultResponse:
        return ReferendumResultResponse(
            id=str(self.referendum_id),
            referendum_id=str(self.referendum_id),
            yes_votes=self.yes_votes,
            no_votes=self.no_votes,
            total_votes=self.total_votes,
            outcome=self.outcome,
        )
