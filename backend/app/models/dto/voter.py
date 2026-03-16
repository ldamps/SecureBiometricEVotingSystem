# app/models/dto/voter.py - DTOs for voter related operations

from dataclasses import asdict, dataclass
from typing import ClassVar, Optional
from app.application.constants import Resource
from uuid import UUID
from datetime import datetime
from app.models.schemas.voter import VoterItem
from app.models.sqlalchemy.voter import VoterStatus


@dataclass
class VoterBaseDTO:
    """Base Data Transfer Object for voters."""
    __resource__: ClassVar[Resource] = Resource.VOTER
    __encrypted_fields__: ClassVar[list[str]] = [
        "national_insurance_number",
        "passport_number",
        "passport_country",
        "first_name",
        "surname",
        "previous_first_name",
        "previous_surname",
        "date_of_birth",
        "email",
        "voter_reference",
    ]


@dataclass
class VoterDTO(VoterBaseDTO):
    """Data Transfer Object for voter details."""
    id: UUID
    national_insurance_number: Optional[str]
    first_name: str
    surname: str
    previous_first_name: Optional[str]
    previous_surname: Optional[str]
    date_of_birth: datetime
    email: str
    voter_reference: str
    consituency_id: UUID
    registration_status: str
    failed_auth_attempts: int
    locked_until: Optional[datetime]
    registered_at: datetime
    renew_by: datetime

    def to_schema(self) -> VoterItem:
        return VoterItem(**asdict(self))


@dataclass
class RegisterVoterPlainDTO(VoterBaseDTO):
    """Plaintext fields provided by the client/API."""
    first_name: str
    surname: str
    previous_first_name: Optional[str]
    previous_surname: Optional[str]
    date_of_birth: datetime
    email: str
    national_insurance_number: Optional[str]
    passport_number: Optional[str]
    passport_country: Optional[str]
    consituency_id: UUID
    renew_by: datetime
    registration_status: VoterStatus

    @classmethod
    def create_dto(cls, model: VoterItem, voter_id: UUID):
        return cls(
            **model.model_dump(),
            voter_id=voter_id,
        )



@dataclass
class RegisterVoterEncryptedDTO(VoterBaseDTO):
    """Encrypted fields that are persisted in the database."""


@dataclass
class UpdateVoterPlainDTO(VoterBaseDTO):
    """DTO for updating voter details with plaintext values."""
    first_name: Optional[str]

@dataclass
class UpdateVoterEncryptedDTO(VoterBaseDTO):
    """DTO for updating voter details with encrypted values."""
