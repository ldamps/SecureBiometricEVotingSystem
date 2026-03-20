# app/models/dto/voter_passport.py - DTOs for voter passport operations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.base.sqlalchemy_base import EncryptedDBField
from app.models.schemas.voter_passport import (
    VoterPassportItem,
    CreateVoterPassportRequest,
    UpdateVoterPassportRequest,
)
from app.models.sqlalchemy.voter_passport import VoterPassport


@dataclass
class VoterPassportBaseDTO:
    """Base Data Transfer Object for voter passports."""
    __resource__: ClassVar[Resource] = Resource.VOTER_PASSPORT
    __encrypted_fields__: ClassVar[list[str]] = [
        "passport_number",
        "issuing_country",
        "expiry_date",
    ]


@dataclass
class VoterPassportDTO(VoterPassportBaseDTO):
    """Plaintext passport DTO — target for decrypt_model and source for to_schema."""

    id: UUID = None
    voter_id: UUID = None
    passport_number: Optional[str] = None
    issuing_country: Optional[str] = None
    expiry_date: Optional[str] = None
    is_primary: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_schema(self) -> VoterPassportItem:
        ed: Optional[datetime] = None
        if self.expiry_date:
            s = self.expiry_date.strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                ed = datetime.fromisoformat(s)
            except ValueError:
                pass

        return VoterPassportItem(
            id=str(self.id),
            passport_number=self.passport_number,
            issuing_country=self.issuing_country,
            expiry_date=ed,
            is_primary=self.is_primary,
        )


@dataclass
class CreateVoterPassportPlainDTO(VoterPassportBaseDTO):
    """Plaintext fields for creating a voter passport entry."""
    voter_id: Optional[UUID] = None
    passport_number: str = ""
    issuing_country: str = ""
    expiry_date: Optional[str] = None
    is_primary: bool = False

    @classmethod
    def create_dto(cls, data: CreateVoterPassportRequest, voter_id: UUID) -> "CreateVoterPassportPlainDTO":
        return cls(
            voter_id=voter_id,
            passport_number=data.passport_number,
            issuing_country=data.issuing_country,
            expiry_date=data.expiry_date.isoformat() if data.expiry_date else None,
            is_primary=data.is_primary,
        )


@dataclass
class CreateVoterPassportEncryptedDTO(VoterPassportBaseDTO):
    """Encrypted fields for persisting a new voter passport row."""
    voter_id: Optional[UUID] = None
    is_primary: bool = False
    passport_number: Optional[EncryptedDBField] = None
    passport_number_search_token: Optional[str] = None
    issuing_country: Optional[EncryptedDBField] = None
    expiry_date: Optional[EncryptedDBField] = None

    def to_model(self) -> VoterPassport:
        return VoterPassport(**asdict(self))


@dataclass
class UpdateVoterPassportPlainDTO(VoterPassportBaseDTO):
    """Plaintext fields for updating a voter passport."""
    passport_id: Optional[UUID] = None
    voter_id: Optional[UUID] = None
    passport_number: Optional[str] = None
    issuing_country: Optional[str] = None
    expiry_date: Optional[str] = None
    is_primary: Optional[bool] = None

    @classmethod
    def create_dto(cls, data: UpdateVoterPassportRequest, passport_id: UUID, voter_id: UUID) -> "UpdateVoterPassportPlainDTO":
        return cls(
            passport_id=passport_id,
            voter_id=voter_id,
            passport_number=data.passport_number,
            issuing_country=data.issuing_country,
            expiry_date=data.expiry_date.isoformat() if data.expiry_date else None,
            is_primary=data.is_primary,
        )


@dataclass
class UpdateVoterPassportEncryptedDTO(VoterPassportBaseDTO):
    """Encrypted fields for updating a voter passport row."""
    passport_id: Optional[UUID] = None
    voter_id: Optional[UUID] = None
    is_primary: Optional[bool] = None
    passport_number: Optional[EncryptedDBField] = None
    passport_number_search_token: Optional[str] = None
    issuing_country: Optional[EncryptedDBField] = None
    expiry_date: Optional[EncryptedDBField] = None
