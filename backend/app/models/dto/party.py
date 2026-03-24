# party_dto.py - Party DTOs for the e-voting system.

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.party import PartyItem
from app.models.sqlalchemy.party import Party


@dataclass
class PartyBaseDTO:
    """Base Data Transfer Object for parties."""
    __resource__: ClassVar[Resource] = Resource.PARTY
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class PartyDTO(PartyBaseDTO):
    """Plaintext party DTO — target for decrypt_model and source for to_schema."""

    id: UUID = None
    party_name: str = ""
    abbreviation: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def to_schema(self) -> PartyItem:
        return PartyItem(
            id=str(self.id),
            party_name=self.party_name,
            abbreviation=self.abbreviation,
            is_active=self.is_active,
        )


@dataclass
class CreatePartyPlainDTO(PartyBaseDTO):
    """Plaintext fields for creating a party."""

    party_name: str = ""
    abbreviation: Optional[str] = None

    @classmethod
    def create_dto(cls, data) -> "CreatePartyPlainDTO":
        return cls(
            party_name=data.party_name,
            abbreviation=data.abbreviation,
        )


@dataclass
class CreatePartyEncryptedDTO(PartyBaseDTO):
    """Encrypted fields for persisting a new party row.

    Parties have no encrypted fields — this DTO simply mirrors
    the plain DTO so it can pass through the standard encrypt pipeline.
    """

    party_name: str = ""
    abbreviation: Optional[str] = None

    def to_model(self) -> Party:
        return Party(**asdict(self))
