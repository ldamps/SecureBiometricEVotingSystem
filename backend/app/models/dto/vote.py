# app/models/dto/vote.py - DTOs for vote-related operations.

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.sqlalchemy.vote import Vote


@dataclass
class VoteBaseDTO:
    """Base Data Transfer Object for vote."""
    __resource__: ClassVar[Resource] = Resource.VOTE
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class CreateVotePlainDTO(VoteBaseDTO):
    """Plaintext fields for casting a vote (anonymous — no voter_id)."""
    election_id: Optional[UUID] = None
    constituency_id: Optional[UUID] = None
    candidate_id: Optional[UUID] = None
    blind_token_hash: Optional[str] = None
    receipt_code: Optional[str] = None
    email_sent: bool = False
    cast_at: Optional[datetime] = None


@dataclass
class CreateVoteEncryptedDTO(VoteBaseDTO):
    """Encrypted fields for persisting a new vote row."""
    election_id: Optional[UUID] = None
    constituency_id: Optional[UUID] = None
    candidate_id: Optional[UUID] = None
    blind_token_hash: Optional[str] = None
    receipt_code: Optional[str] = None
    email_sent: bool = False
    cast_at: Optional[datetime] = None

    def to_model(self) -> Vote:
        return Vote(**asdict(self))
