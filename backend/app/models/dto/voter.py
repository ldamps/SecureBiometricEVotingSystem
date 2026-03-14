# app/models/dto/voter.py - DTOs for voter related operations

from dataclasses import dataclass
from typing import ClassVar, Optional
from app.application.constants import Resource
from uuid import UUID
from datetime import datetime

@dataclass
class VoterBaseDTO:
    """Base Data Transfer Object for voters."""
    __resource__: ClassVar[Resource] = Resource.VOTER

    __encrypted_fields__: ClassVar[list[str]] = [
        "national_insurance_number",
        "first_name",
        "surname",
        "previous_first_name",
        "maiden_name",
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
    maiden_name: Optional[str]
    date_of_birth: datetime
    email: str
    civil_servant: bool
    council_employee: bool
    armed_forces_member: bool
    voter_reference: str
    consituency_id: UUID
    registration_status: str
    failed_auth_attempts: int
    locked_until: Optional[datetime]
    registered_at: datetime


@dataclass
class RegisterVoterPlainDTO(VoterBaseDTO):
    """Plaintext fields provided by the client/API."""
    first_name: str
    surname: str
    previous_first_name: Optional[str]
    maiden_name: Optional[str]
    date_of_birth: datetime
    email: str
    civil_servant: bool
    council_employee: bool
    armed_forces_member: bool



@dataclass
class RegisterVoterEncryptedDTO(VoterBaseDTO):
    """Encrypted fields that are persisted in the database."""



class UpdateVoterPlainDTO(VoterBaseDTO):
    """DTO for updating voter details with plaintext values."""


class UpdateVoterEncryptedDTO(VoterBaseDTO):
    """DTO for updating voter details with encrypted values."""
