# app/models/dto/ballot.py - DTOs for ballot token operations.

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.base.sqlalchemy_base import EncryptedDBField
from app.models.schemas.ballot_token import BallotTokenItem
from app.models.sqlalchemy.ballot_token import BallotToken


@dataclass
class BallotTokenBaseDTO:
    """Base Data Transfer Object for ballot tokens."""
    __resource__: ClassVar[Resource] = Resource.BALLOT_TOKEN
    __encrypted_fields__: ClassVar[list[str]] = ["blind_token_hash"]


@dataclass
class BallotTokenDTO(BallotTokenBaseDTO):
    """Plaintext ballot token DTO — target for decrypt_model and source for to_schema."""

    id: UUID = None
    election_id: Optional[UUID] = None
    constituency_id: Optional[UUID] = None
    referendum_id: Optional[UUID] = None
    blind_token_hash: Optional[str] = None
    is_used: bool = False
    issued_at: Optional[datetime] = None
    used_at: Optional[datetime] = None

    def to_schema(self) -> BallotTokenItem:
        return BallotTokenItem(
            id=str(self.id),
            election_id=str(self.election_id) if self.election_id else None,
            constituency_id=str(self.constituency_id) if self.constituency_id else None,
            referendum_id=str(self.referendum_id) if self.referendum_id else None,
            blind_token_hash=self.blind_token_hash or "",
            is_used=self.is_used,
            issued_at=self.issued_at,
            used_at=self.used_at,
        )


@dataclass
class CreateBallotTokenPlainDTO(BallotTokenBaseDTO):
    """Plaintext fields for creating a ballot token."""

    election_id: Optional[UUID] = None
    constituency_id: Optional[UUID] = None
    referendum_id: Optional[UUID] = None
    blind_token_hash: str = ""
    is_used: bool = False
    issued_at: Optional[datetime] = None


@dataclass
class CreateBallotTokenEncryptedDTO(BallotTokenBaseDTO):
    """Encrypted fields for persisting a new ballot token row.

    blind_token_hash is encrypted; a search token is generated automatically.
    """

    election_id: Optional[UUID] = None
    constituency_id: Optional[UUID] = None
    referendum_id: Optional[UUID] = None
    blind_token_hash: Optional[EncryptedDBField] = None
    blind_token_hash_search_token: Optional[str] = None
    is_used: bool = False
    issued_at: Optional[datetime] = None

    def to_model(self) -> BallotToken:
        return BallotToken(
            election_id=self.election_id,
            constituency_id=self.constituency_id,
            referendum_id=self.referendum_id,
            blind_token_hash=self.blind_token_hash,
            blind_token_hash_search_token=self.blind_token_hash_search_token,
            is_used=self.is_used,
            issued_at=self.issued_at,
        )
