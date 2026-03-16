# app/models/dto/voter.py - DTOs for voter related operations

import uuid as uuid_module
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import ClassVar, Optional
from app.application.constants import Resource
from uuid import UUID
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

    def to_model(self) -> Voter:
        """Build Voter ORM instance for persistence. EncryptedBytes fields stored as plain bytes for now."""
        # DB constraint: registration_status IN ('pending', 'approved', 'rejected')
        reg_status = (
            self.registration_status.value.lower()
            if hasattr(self.registration_status, "value")
            else str(self.registration_status).lower()
        )
        # Ensure we use a value allowed by the DB constraint
        if reg_status not in ("pending", "approved", "rejected"):
            reg_status = "pending"
        ni = self.national_insurance_number
        if not ni or not ni.strip():
            ni = f"NONE-{uuid_module.uuid4().hex}"
        voter_ref = f"VR-{uuid_module.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        def _enc(s: Optional[str]) -> Optional[bytes]:
            return s.encode("utf-8") if s else None

        return Voter(
            national_insurance_number=ni,
            passport_number=self.passport_number,
            passport_country=self.passport_country,
            first_name=_enc(self.first_name),
            surname=_enc(self.surname),
            previous_first_name=_enc(self.previous_first_name),
            previous_surname=_enc(self.previous_surname),
            date_of_birth=_enc(self.date_of_birth.isoformat() if self.date_of_birth else None),
            email=_enc(self.email),
            voter_reference=voter_ref,
            voter_status=reg_status,
            constituency_id=self.consituency_id,
            registration_status=reg_status,
            failed_auth_attempts=0,
            locked_until=None,
            registered_at=now,
            renew_by=self.renew_by,
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

