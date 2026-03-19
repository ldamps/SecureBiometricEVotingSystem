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
        "passport_number",
        "passport_country",
        "passport_expiry_date",
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
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    passport_expiry_date: Optional[str] = None
    first_name: Optional[str] = None
    surname: Optional[str] = None
    previous_first_name: Optional[str] = None
    previous_surname: Optional[str] = None
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    voter_reference: Optional[str] = None
    constituency_id: Optional[UUID] = None
    locked_until: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    renew_by: Optional[datetime] = None

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

        ped: Optional[datetime] = None
        if self.passport_expiry_date:
            s = self.passport_expiry_date.strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                ped = datetime.fromisoformat(s)
            except ValueError:
                pass

        return VoterItem(
            id=str(self.id),
            national_insurance_number=self.national_insurance_number,
            passport_number=self.passport_number,
            passport_country=self.passport_country,
            passport_expiry_date=ped,
            first_name=self.first_name,
            surname=self.surname,
            previous_first_name=self.previous_first_name,
            maiden_name=self.previous_surname,
            date_of_birth=dob,
            email=self.email,
            voter_reference=self.voter_reference,
            consituency_id=str(self.constituency_id) if self.constituency_id else None,
            registration_status=self.registration_status,
            failed_auth_attempts=self.failed_auth_attempts,
            locked_until=self.locked_until,
            registered_at=self.registered_at,
            renew_by=self.renew_by,
        )


@dataclass
class RegisterVoterPlainDTO(VoterBaseDTO):
    """Plaintext fields provided by the client for voter registration."""
    first_name: str = ""
    surname: str = ""
    previous_first_name: Optional[str] = None
    previous_surname: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    email: str = ""
    national_insurance_number: Optional[str] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    passport_expiry_date: Optional[datetime] = None
    consituency_id: Optional[UUID] = None
    renew_by: Optional[datetime] = None
    registration_status: Optional[str] = None

    @classmethod
    def create_dto(cls, data: VoterRegistrationRequest) -> "RegisterVoterPlainDTO":
        return cls(**data.model_dump())


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
    national_insurance_number: Optional[EncryptedDBField] = None
    national_insurance_number_search_token: Optional[str] = None
    passport_number: Optional[EncryptedDBField] = None
    passport_number_search_token: Optional[str] = None
    passport_country: Optional[EncryptedDBField] = None
    passport_expiry_date: Optional[EncryptedDBField] = None
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
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    passport_expiry_date: Optional[datetime] = None
    consituency_id: Optional[UUID] = None
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
    passport_number: Optional[EncryptedDBField] = None
    passport_number_search_token: Optional[str] = None
    passport_country: Optional[EncryptedDBField] = None
    passport_expiry_date: Optional[EncryptedDBField] = None
    first_name: Optional[EncryptedDBField] = None
    surname: Optional[EncryptedDBField] = None
    previous_first_name: Optional[EncryptedDBField] = None
    previous_surname: Optional[EncryptedDBField] = None
    date_of_birth: Optional[EncryptedDBField] = None
    email: Optional[EncryptedDBField] = None
    email_search_token: Optional[str] = None
    voter_reference: Optional[EncryptedDBField] = None
    voter_reference_search_token: Optional[str] = None
    consituency_id: Optional[UUID] = None
    renew_by: Optional[datetime] = None
    registration_status: Optional[str] = None
    failed_auth_attempts: Optional[int] = None
    locked_until: Optional[datetime] = None
