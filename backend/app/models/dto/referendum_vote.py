# app/models/dto/referendum_vote.py - DTOs for referendum vote operations.

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.sqlalchemy.referendum_vote import ReferendumVote


@dataclass
class ReferendumVoteBaseDTO:
    """Base Data Transfer Object for referendum vote."""
    __resource__: ClassVar[Resource] = Resource.VOTE
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class CreateReferendumVotePlainDTO(ReferendumVoteBaseDTO):
    """Plaintext fields for casting a referendum vote (anonymous — no voter_id)."""
    referendum_id: Optional[UUID] = None
    choice: Optional[str] = None
    blind_token_hash: Optional[str] = None
    receipt_code: Optional[str] = None
    email_sent: bool = False
    cast_at: Optional[datetime] = None


@dataclass
class CreateReferendumVoteEncryptedDTO(ReferendumVoteBaseDTO):
    """Encrypted fields for persisting a new referendum vote row."""
    referendum_id: Optional[UUID] = None
    choice: Optional[str] = None
    blind_token_hash: Optional[str] = None
    receipt_code: Optional[str] = None
    email_sent: bool = False
    cast_at: Optional[datetime] = None

    def to_model(self) -> ReferendumVote:
        return ReferendumVote(**asdict(self))
