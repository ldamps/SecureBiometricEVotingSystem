# app/models/dto/voter.py - DTOs for voter related operations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.base.sqlalchemy_base import EncryptedDBField
from app.models.schemas.voter import VoterItem, VoterRegistrationRequest, VoterUpdateRequest
from app.models.sqlalchemy.voter import Voter, VoterStatus


@dataclass
class VoterBaseDTO:
    """Base Data Transfer Object for voters."""
    __resource__: ClassVar[Resource] = Resource.VOTER
    __encrypted_fields__: ClassVar[list[str]] = [
        "national_insurance_number",
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
    """Plaintext voter DTO — target for decrypt_model and source for to_schema."""

    id: UUID
    voter_status: str
    registration_status: str
    failed_auth_attempts: int
    national_insurance_number: Optional[str] = None
    first_name: Optional[str] = None
    surname: Optional[str] = None
    previous_first_name: Optional[str] = None
    previous_surname: Optional[str] = None
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    voter_reference: Optional[str] = None
    constituency_id: Optional[UUID] = None
    nationality_category: str = ""
    immigration_status: Optional[str] = None
    immigration_status_expiry: Optional[datetime] = None
    locked_until: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    renew_by: Optional[datetime] = None
    # passports are populated externally (not an encrypted field)
    _passports_schema: Optional[list] = None

    def to_schema(self) -> VoterItem:
        dob: Optional[datetime] = None
        if self.date_of_birth:
            s = self.date_of_birth.strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                dob = datetime.fromisoformat(s)
            except ValueError:
                pass

        return VoterItem(
            id=str(self.id),
            national_insurance_number=self.national_insurance_number,
            first_name=self.first_name,
            surname=self.surname,
            previous_first_name=self.previous_first_name,
            maiden_name=self.previous_surname,
            date_of_birth=dob,
            email=self.email,
            voter_reference=self.voter_reference,
            constituency_id=self.constituency_id,
            nationality_category=self.nationality_category,
            immigration_status=self.immigration_status,
            immigration_status_expiry=self.immigration_status_expiry,
            registration_status=self.registration_status,
            failed_auth_attempts=self.failed_auth_attempts,
            locked_until=self.locked_until,
            registered_at=self.registered_at,
            renew_by=self.renew_by,
            passports=self._passports_schema or [],
        )


@dataclass
class RegisterVoterPlainDTO(VoterBaseDTO):
    """Plaintext fields provided by the client for voter registration.

    Includes both client-provided fields and service-computed fields
    (voter_reference, voter_status, timestamps) needed for encryption.
    """
    first_name: str = ""
    surname: str = ""
    previous_first_name: Optional[str] = None
    previous_surname: Optional[str] = None
    date_of_birth: Optional[str] = None
    email: str = ""
    national_insurance_number: Optional[str] = None
    voter_reference: Optional[str] = None
    voter_status: Optional[str] = None
    nationality_category: str = ""
    immigration_status: Optional[str] = None
    immigration_status_expiry: Optional[datetime] = None
    constituency_id: Optional[UUID] = None
    registration_status: Optional[str] = None
    failed_auth_attempts: int = 0
    registered_at: Optional[datetime] = None
    renew_by: Optional[datetime] = None
    locked_until: Optional[datetime] = None

    @classmethod
    def create_dto(cls, data: VoterRegistrationRequest) -> "RegisterVoterPlainDTO":
        d = data.model_dump(exclude={"passports"})
        return cls(**d)


@dataclass
class RegisterVoterEncryptedDTO(VoterBaseDTO):
    """Encrypted fields for persisting a new voter row."""
    voter_status: str = ""
    constituency_id: Optional[UUID] = None
    registration_status: str = ""
    failed_auth_attempts: int = 0
    locked_until: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    renew_by: Optional[datetime] = None
    nationality_category: str = ""
    immigration_status: Optional[str] = None
    immigration_status_expiry: Optional[datetime] = None
    national_insurance_number: Optional[EncryptedDBField] = None
    national_insurance_number_search_token: Optional[str] = None
    first_name: Optional[EncryptedDBField] = None
    surname: Optional[EncryptedDBField] = None
    previous_first_name: Optional[EncryptedDBField] = None
    previous_surname: Optional[EncryptedDBField] = None
    date_of_birth: Optional[EncryptedDBField] = None
    email: Optional[EncryptedDBField] = None
    email_search_token: Optional[str] = None
    voter_reference: Optional[EncryptedDBField] = None
    voter_reference_search_token: Optional[str] = None

    def to_model(self) -> Voter:
        return Voter(**asdict(self))


@dataclass
class UpdateVoterPlainDTO(VoterBaseDTO):
    """Plaintext fields for updating a voter."""
    voter_id: Optional[UUID] = None
    first_name: Optional[str] = None
    surname: Optional[str] = None
    previous_first_name: Optional[str] = None
    previous_surname: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    email: Optional[str] = None
    national_insurance_number: Optional[str] = None
    nationality_category: Optional[str] = None
    immigration_status: Optional[str] = None
    immigration_status_expiry: Optional[datetime] = None
    constituency_id: Optional[UUID] = None
    renew_by: Optional[datetime] = None
    registration_status: Optional[str] = None
    failed_auth_attempts: Optional[int] = None
    locked_until: Optional[datetime] = None

    @classmethod
    def create_dto(cls, data: VoterUpdateRequest, voter_id: UUID) -> "UpdateVoterPlainDTO":
        return cls(**data.model_dump(), voter_id=voter_id)


@dataclass
class UpdateVoterEncryptedDTO(VoterBaseDTO):
    """Encrypted fields for updating a voter row."""
    voter_id: Optional[UUID] = None
    national_insurance_number: Optional[EncryptedDBField] = None
    national_insurance_number_search_token: Optional[str] = None
    first_name: Optional[EncryptedDBField] = None
    surname: Optional[EncryptedDBField] = None
    previous_first_name: Optional[EncryptedDBField] = None
    previous_surname: Optional[EncryptedDBField] = None
    date_of_birth: Optional[EncryptedDBField] = None
    email: Optional[EncryptedDBField] = None
    email_search_token: Optional[str] = None
    voter_reference: Optional[EncryptedDBField] = None
    voter_reference_search_token: Optional[str] = None
    nationality_category: Optional[str] = None
    immigration_status: Optional[str] = None
    immigration_status_expiry: Optional[datetime] = None
    constituency_id: Optional[UUID] = None
    renew_by: Optional[datetime] = None
    registration_status: Optional[str] = None
    failed_auth_attempts: Optional[int] = None
    locked_until: Optional[datetime] = None
