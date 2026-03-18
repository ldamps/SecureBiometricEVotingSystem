# app/models/dto/voter.py - DTOs for voter related operations

import uuid as uuid_module
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import ClassVar, Optional
from app.application.constants import Resource
from uuid import UUID
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
        "first_name",
        "surname",
        "previous_first_name",
        "previous_surname",
        "date_of_birth",
        "email",
        "voter_reference",
    ]


@dataclass
class VoterDecryptedDTO(VoterBaseDTO):
    """Plaintext shape after decrypting a Voter ORM row (or all-null legacy/migrated row)."""

    id: UUID
    voter_status: str
    registration_status: str
    failed_auth_attempts: int
    national_insurance_number: Optional[str] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    first_name: Optional[str] = None
    surname: Optional[str] = None
    previous_first_name: Optional[str] = None
    previous_surname: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO string from decrypt
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
        return VoterItem(
            id=str(self.id),
            national_insurance_number=self.national_insurance_number,
            passport_number=self.passport_number,
            passport_country=self.passport_country,
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

    _registration_field_names = frozenset({
        "first_name", "surname", "previous_first_name", "previous_surname",
        "date_of_birth", "email", "national_insurance_number", "passport_number",
        "passport_country", "consituency_id", "renew_by", "registration_status",
    })

    @classmethod
    def create_dto(cls, data: VoterRegistrationRequest) -> "RegisterVoterPlainDTO":
        """Build DTO from registration request (no voter_id; used for new voter)."""
        d = {k: v for k, v in data.model_dump().items() if k in cls._registration_field_names}
        d["consituency_id"] = (
            UUID(d["consituency_id"]) if isinstance(d["consituency_id"], str) else d["consituency_id"]
        )
        rs = d["registration_status"]
        if isinstance(rs, str):
            # Request may send "pending"; enum values are "PENDING", "SUSPENDED", "ACTIVE"
            d["registration_status"] = VoterStatus(rs.upper()) if rs.upper() in ("PENDING", "SUSPENDED", "ACTIVE") else VoterStatus.PENDING
        return cls(**d)

@dataclass
class RegisterVoterEncryptionPlainDTO(VoterBaseDTO):
    """Plain values for field-level encryption during registration (see VoterService.register_voter)."""

    first_name: str
    surname: str
    date_of_birth: str
    email: str
    voter_reference: str
    voter_status: str
    constituency_id: UUID
    registration_status: str
    failed_auth_attempts: int
    registered_at: datetime
    renew_by: datetime
    national_insurance_number: Optional[str] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    previous_first_name: Optional[str] = None
    previous_surname: Optional[str] = None
    locked_until: Optional[datetime] = None

    @classmethod
    def from_registration(cls, reg: "RegisterVoterPlainDTO") -> "RegisterVoterEncryptionPlainDTO":
        reg_status = (
            reg.registration_status.value.lower()
            if hasattr(reg.registration_status, "value")
            else str(reg.registration_status).lower()
        )
        if reg_status not in ("pending", "approved", "rejected"):
            reg_status = "pending"
        ni = reg.national_insurance_number
        if not ni or not str(ni).strip():
            ni = f"NONE-{uuid_module.uuid4().hex}"
        else:
            ni = str(ni).strip()
        voter_ref = f"VR-{uuid_module.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        return cls(
            first_name=reg.first_name,
            surname=reg.surname,
            date_of_birth=reg.date_of_birth.isoformat(),
            email=reg.email,
            voter_reference=voter_ref,
            voter_status=reg_status,
            constituency_id=reg.consituency_id,
            registration_status=reg_status,
            failed_auth_attempts=0,
            registered_at=now,
            renew_by=reg.renew_by,
            national_insurance_number=ni,
            passport_number=reg.passport_number.strip() if reg.passport_number and reg.passport_number.strip() else None,
            passport_country=reg.passport_country.strip() if reg.passport_country and reg.passport_country.strip() else None,
            previous_first_name=reg.previous_first_name,
            previous_surname=reg.previous_surname,
            locked_until=None,
        )


@dataclass
class VoterPersistEncryptedDTO:
    """Encrypted columns + metadata for a new Voter row (output of encrypt_dto)."""

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
    first_name: Optional[EncryptedDBField] = None
    surname: Optional[EncryptedDBField] = None
    previous_first_name: Optional[EncryptedDBField] = None
    previous_surname: Optional[EncryptedDBField] = None
    date_of_birth: Optional[EncryptedDBField] = None
    email: Optional[EncryptedDBField] = None
    email_search_token: Optional[str] = None
    voter_reference: Optional[EncryptedDBField] = None
    voter_reference_search_token: Optional[str] = None


def voter_orm_from_persist_encrypted(row: VoterPersistEncryptedDTO) -> Voter:
    """Build a Voter ORM instance from encrypted registration payload."""
    return Voter(
        national_insurance_number=row.national_insurance_number,
        national_insurance_number_search_token=row.national_insurance_number_search_token,
        passport_number=row.passport_number,
        passport_number_search_token=row.passport_number_search_token,
        passport_country=row.passport_country,
        first_name=row.first_name,
        surname=row.surname,
        previous_first_name=row.previous_first_name,
        previous_surname=row.previous_surname,
        date_of_birth=row.date_of_birth,
        email=row.email,
        email_search_token=row.email_search_token,
        voter_reference=row.voter_reference,
        voter_reference_search_token=row.voter_reference_search_token,
        voter_status=row.voter_status,
        constituency_id=row.constituency_id,
        registration_status=row.registration_status,
        failed_auth_attempts=row.failed_auth_attempts,
        locked_until=row.locked_until,
        registered_at=row.registered_at,
        renew_by=row.renew_by,
    )


@dataclass
class RegisterVoterEncryptedDTO(VoterBaseDTO):
    """Encrypted fields that are persisted in the database."""


@dataclass
class UpdateVoterPlainDTO(VoterBaseDTO):
    """DTO for updating voter details with plaintext values."""
    first_name: Optional[str] = None
    surname: Optional[str] = None
    previous_first_name: Optional[str] = None
    previous_surname: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    email: Optional[str] = None
    national_insurance_number: Optional[str] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    consituency_id: Optional[UUID] = None
    renew_by: Optional[datetime] = None
    registration_status: Optional[VoterStatus] = None
    failed_auth_attempts: Optional[int] = None
    locked_until: Optional[datetime] = None
    registered_at: Optional[datetime] = None

    _update_field_names = frozenset({
        "first_name", "surname", "previous_first_name", "previous_surname",
        "date_of_birth", "email", "national_insurance_number", "passport_number",
        "passport_country", "consituency_id", "renew_by", "registration_status",
        "failed_auth_attempts", "locked_until", "registered_at",
    })

    @classmethod
    def create_dto(cls, data: VoterUpdateRequest) -> "UpdateVoterPlainDTO":
        """Build DTO from update request (only fields present in request)."""
        d = {k: v for k, v in data.model_dump().items() if k in cls._update_field_names}
        if d.get("consituency_id") is not None:
            d["consituency_id"] = UUID(d["consituency_id"]) if isinstance(d["consituency_id"], str) else d["consituency_id"]
        if d.get("registration_status") is not None and isinstance(d["registration_status"], str):
            rs = d["registration_status"]
            d["registration_status"] = VoterStatus(rs.upper()) if rs.upper() in ("PENDING", "SUSPENDED", "ACTIVE") else None
        kwargs = {f: d.get(f) for f in cls._update_field_names}
        return cls(**kwargs)
    """DTO for updating voter details with encrypted values."""

