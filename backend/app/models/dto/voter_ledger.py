# app/models/dto/voter_ledger.py - DTOs for voter ledger related operations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.base.sqlalchemy_base import EncryptedDBField
from app.models.schemas.voter_ledger import VoterLedgerItem, CreateVoterLedgerRequest
from app.models.sqlalchemy.voter_ledger import VoterLedger

@dataclass
class VoterLedgerBaseDTO:
    """Base Data Transfer Object for voter ledger."""
    __resource__: ClassVar[Resource] = Resource.VOTER_LEDGER
    __encrypted_fields__: ClassVar[list[str]] = []

@dataclass
class VoterLedgerDTO(VoterLedgerBaseDTO):
    """Plaintext voter ledger DTO — target for decrypt_model and source for to_schema."""
    id: UUID
    voter_id: UUID
    election_id: UUID
    voted_at: datetime

    def to_schema(self) -> VoterLedgerItem:
        return VoterLedgerItem(
            id=str(self.id),
            voter_id=str(self.voter_id),
            election_id=str(self.election_id),
            voted_at=self.voted_at,
        )

@dataclass
class CreateVoterLedgerPlainDTO(VoterLedgerBaseDTO):
    """Plaintext fields for creating a voter ledger entry."""
    voter_id: Optional[UUID] = None
    election_id: Optional[UUID] = None
    voted_at: Optional[datetime] = None

    @classmethod
    def create_dto(cls, data: CreateVoterLedgerRequest, voter_id: UUID) -> "CreateVoterLedgerPlainDTO":
        return cls(
            voter_id=voter_id,
            election_id=data.election_id,
            voted_at=data.voted_at,
        )

@dataclass
class CreateVoterLedgerEncryptedDTO(VoterLedgerBaseDTO):
    """Encrypted fields for persisting a new voter ledger row."""
    voter_id: Optional[UUID] = None
    election_id: Optional[UUID] = None
    voted_at: Optional[datetime] = None

    def to_model(self) -> VoterLedger:
        return VoterLedger(**asdict(self))