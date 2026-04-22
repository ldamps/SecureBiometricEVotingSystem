# voter.py - Voter schemas for the e-voting system.
import re
from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from app.models.schemas.voter_passport import VoterPassportItem, PassportEntry
from pydantic import EmailStr, Field, model_validator
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from uuid import UUID

# UK NI number (HMRC full rules): first letter excludes D,F,I,Q,U,V;
# second letter excludes D,F,I,O,Q,U,V; then 6 digits and a suffix A-D.
_NI_RE = re.compile(
    r"^(?![DFIQUV])[A-CEGHJ-PR-TW-Z](?![DFIOQUV])[A-CEGHJ-NPR-TW-Z]\d{6}[A-D]$",
    re.IGNORECASE,
)


def voter_orm_to_item_dict(voter: Any) -> dict[str, Any]:
    """Build a dict suitable for VoterItem from a Voter ORM instance (constituency_id -> constituency_id, bytes -> str)."""
    d = voter.to_dict()
    d["constituency_id"] = d.get("constituency_id")
    for k, v in list(d.items()):
        if isinstance(v, bytes):
            d[k] = v.decode("utf-8", errors="replace")
    return d


class VoterItem(ResponseSchema):
    """Voter response model. Uses constituency_id (API) mapped from ORM attribute constituency_id.

    Encrypted fields may be null after DB migration or until re-registration.
    """
    id: str = Field(..., description="The unique identifier for the voter.")
    national_insurance_number: Optional[str] = Field(None, description="The national insurance number for the voter.")
    first_name: Optional[str] = Field(None, description="The first name of the voter.")
    surname: Optional[str] = Field(None, description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    maiden_name: Optional[str] = Field(None, description="The maiden name of the voter.")
    date_of_birth: Optional[datetime] = Field(None, description="The date of birth of the voter.")
    email: Optional[str] = Field(None, description="The email address of the voter.")
    voter_reference: Optional[str] = Field(None, description="The voter reference for the voter.")
    constituency_id: Optional[UUID] = Field(None, description="The constituency identifier for the voter.")
    nationality_category: str = Field(..., description="The nationality category of the voter.")
    immigration_status: Optional[str] = Field(None, description="The immigration status of the voter (non-British only).")
    immigration_status_expiry: Optional[datetime] = Field(None, description="When the immigration status expires.")
    voter_status: str = Field(..., description="The voter status (PENDING, ACTIVE, SUSPENDED).")
    registration_status: str = Field(..., description="The registration status of the voter.")
    failed_auth_attempts: int = Field(..., description="The number of failed authentication attempts for the voter.")
    locked_until: Optional[datetime] = Field(None, description="The date and time the voter was locked until.")
    registered_at: Optional[datetime] = Field(None, description="The date and time the voter was registered.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the voter's account needs to be renewed by.")
    passports: list[VoterPassportItem] = Field(default_factory=list, description="The voter's passport entries.")

    @classmethod
    def from_orm_voter(cls, voter: Any) -> "VoterItem":
        """Build VoterItem from a Voter ORM instance."""
        return cls.model_validate(voter_orm_to_item_dict(voter))


class VoterRegistrationRequest(RequestSchema):
    """Voter registration request model.

    Identity requirement: the voter must provide either a national insurance
    number or at least one passport entry (or both).  The NI number is the
    preferred anchor identifier.
    """
    kyc_session_id: Optional[str] = Field(None, description="The Stripe Identity verification session ID. Required for passport-based registration only.")
    first_name: str = Field(..., description="The first name of the voter.")
    surname: str = Field(..., description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    previous_surname: Optional[str] = Field(None, description="The previous surname of the voter.")
    date_of_birth: datetime = Field(..., description="The date of birth of the voter.")
    email: EmailStr = Field(..., description="The email address of the voter.")
    national_insurance_number: Optional[str] = Field(None, description="The national insurance number of the voter.")
    passports: list[PassportEntry] = Field(default_factory=list, description="Passport entries for the voter. Required if no NI number.")
    nationality_category: str = Field(..., description="The nationality category of the voter.")
    immigration_status: Optional[str] = Field(None, description="The immigration status (non-British voters only).")
    immigration_status_expiry: Optional[datetime] = Field(None, description="When the immigration status expires.")
    renew_by: datetime = Field(..., description="The date and time the voter's account needs to be renewed by.")

    @model_validator(mode="after")
    def validate_registration(self) -> "VoterRegistrationRequest":
        # --- Identity: NI or passport required ---
        ni = self.national_insurance_number
        has_ni = ni is not None and ni.strip() != ""
        has_passport = len(self.passports) > 0
        if not has_ni and not has_passport:
            raise ValueError(
                "At least one form of identity is required: "
                "provide a national insurance number or at least one passport entry."
            )

        # --- KYC required for passport-based registration (no NI) ---
        if not has_ni and has_passport:
            if not self.kyc_session_id or not self.kyc_session_id.strip():
                raise ValueError(
                    "KYC identity verification is required when registering with a passport. "
                    "Please complete the Stripe Identity verification."
                )

        # --- NI format validation ---
        if has_ni and not _NI_RE.match(ni.strip().replace(" ", "")):
            raise ValueError(
                "National Insurance number format is invalid. "
                "Expected format: two letters, six digits, one letter (A–D), e.g. QQ123456C."
            )

        # --- Age validation (minimum 14 to register) ---
        now = datetime.now(timezone.utc)
        dob = self.date_of_birth
        if dob:
            if dob.tzinfo is None:
                dob = dob.replace(tzinfo=timezone.utc)
            age = (now - dob).days // 365
            if age < 14:
                raise ValueError(
                    "You must be at least 14 years old to register to vote."
                )

        # --- Passport expiry: must not be expired more than 5 years ---
        for p in self.passports:
            if p.expiry_date:
                exp = p.expiry_date
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                max_expired = now - timedelta(days=5 * 365)
                if exp < max_expired:
                    raise ValueError(
                        f"Passport {p.passport_number} expired more than 5 years ago "
                        f"and cannot be used for identification."
                    )

        # --- Immigration status expiry: must not be in the past ---
        if self.immigration_status and self.immigration_status_expiry:
            exp = self.immigration_status_expiry
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now:
                raise ValueError(
                    "Immigration status has expired. You are not eligible to register "
                    "with an expired immigration status."
                )

        return self


class VerifyIdentityRequest(RequestSchema):
    """Request model for verifying a voter's identity by name and address."""
    full_name: str = Field(..., description="The voter's full name (first name and surname).")
    address_line1: str = Field(..., description="Address line 1.")
    address_line2: Optional[str] = Field(None, description="Address line 2.")
    city: str = Field(..., description="City or town.")
    postcode: Optional[str] = Field(None, description="Postcode.")


class VerifyIdentityResponse(ResponseSchema):
    """Response model for a successful identity verification."""
    verified: bool = Field(..., description="Whether the voter's identity was verified.")
    voter_id: Optional[str] = Field(None, description="The voter's ID if verified.")
    message: str = Field(..., description="A message describing the verification result.")


class VoterUpdateRequest(RequestSchema):
    """Voter update request model.

    Passport entries are managed separately via the passport sub-routes.
    System-controlled fields (voter_status, registration_status,
    failed_auth_attempts, locked_until) cannot be updated via this endpoint.
    """
    first_name: Optional[str] = Field(None, description="The first name of the voter.")
    surname: Optional[str] = Field(None, description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    previous_surname: Optional[str] = Field(None, description="The previous surname of the voter.")
    date_of_birth: Optional[datetime] = Field(None, description="The date of birth of the voter.")
    email: Optional[str] = Field(None, description="The email address of the voter.")
    nationality_category: Optional[str] = Field(None, description="The nationality category of the voter.")
    immigration_status: Optional[str] = Field(None, description="The immigration status (non-British voters only).")
    immigration_status_expiry: Optional[datetime] = Field(None, description="When the immigration status expires.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the voter's account needs to be renewed by.")

