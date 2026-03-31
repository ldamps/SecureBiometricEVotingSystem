# tally_result.py - DTOs for tally result operations.

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.tally_result import TallyResultItem
from app.models.sqlalchemy.tally_result import TallyResult


@dataclass
class TallyResultBaseDTO:
    """Base class for tally-result DTOs."""
    __resource__: ClassVar[Resource] = Resource.TALLY_RESULT
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class TallyResultDTO(TallyResultBaseDTO):
    """Plaintext tally result DTO (read-only — tallies are incremented internally)."""
    id: UUID = field(default=None)
    election_id: Optional[UUID] = None
    constituency_id: Optional[UUID] = None
    candidate_id: Optional[UUID] = None
    referendum_id: Optional[UUID] = None
    choice: Optional[str] = None
    vote_count: int = 0
    tallied_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, model: TallyResult) -> "TallyResultDTO":
        return cls(
            id=model.id,
            election_id=model.election_id,
            constituency_id=model.constituency_id,
            candidate_id=model.candidate_id,
            referendum_id=model.referendum_id,
            choice=model.choice,
            vote_count=model.vote_count,
            tallied_at=model.tallied_at,
        )

    def to_schema(self) -> TallyResultItem:
        return TallyResultItem(
            id=str(self.id),
            election_id=str(self.election_id) if self.election_id else None,
            constituency_id=str(self.constituency_id) if self.constituency_id else None,
            candidate_id=str(self.candidate_id) if self.candidate_id else None,
            referendum_id=str(self.referendum_id) if self.referendum_id else None,
            choice=self.choice,
            vote_count=self.vote_count,
            tallied_at=self.tallied_at,
        )
