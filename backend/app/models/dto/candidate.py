# candidate_dto.py - Candidate DTOs for the e-voting system.

from dataclasses import asdict, dataclass
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.candidate import CandidateItem, CreateCandidateRequest
from app.models.sqlalchemy.candidate import Candidate


@dataclass
class CandidateBaseDTO:
    """Base Data Transfer Object for candidates."""
    __resource__: ClassVar[Resource] = Resource.CANDIDATE
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class CandidateDTO(CandidateBaseDTO):
    """Plaintext candidate DTO — target for decrypt_model and source for to_schema."""

    id: UUID = None
    election_id: UUID = None
    constituency_id: UUID = None
    first_name: str = ""
    last_name: str = ""
    party_id: UUID = None
    is_active: bool = True

    def to_schema(self) -> CandidateItem:
        return CandidateItem(
            id=str(self.id),
            election_id=str(self.election_id),
            constituency_id=str(self.constituency_id),
            first_name=self.first_name,
            last_name=self.last_name,
            party_id=str(self.party_id),
            is_active=self.is_active,
        )


@dataclass
class CreateCandidatePlainDTO(CandidateBaseDTO):
    """Plaintext fields for creating a candidate."""

    election_id: UUID = None
    constituency_id: UUID = None
    first_name: str = ""
    last_name: str = ""
    party_id: UUID = None

    @classmethod
    def create_dto(cls, data: CreateCandidateRequest, election_id: UUID) -> "CreateCandidatePlainDTO":
        return cls(
            election_id=election_id,
            constituency_id=data.constituency_id,
            first_name=data.first_name,
            last_name=data.last_name,
            party_id=data.party_id,
        )


@dataclass
class CreateCandidateEncryptedDTO(CandidateBaseDTO):
    """Encrypted fields for persisting a new candidate row.

    Candidates have no encrypted fields — this DTO simply mirrors
    the plain DTO so it can pass through the standard encrypt pipeline.
    """

    election_id: UUID = None
    constituency_id: UUID = None
    first_name: str = ""
    last_name: str = ""
    party_id: UUID = None

    def to_model(self) -> Candidate:
        return Candidate(**asdict(self))
