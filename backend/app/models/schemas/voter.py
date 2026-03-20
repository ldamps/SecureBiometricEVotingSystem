# voter.py - Voter schemas for the e-voting system.
from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from app.models.schemas.voter_passport import VoterPassportItem, PassportEntry
from pydantic import Field, model_validator
from datetime import datetime
from typing import Any, Optional
from uuid import UUID


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
    first_name: str = Field(..., description="The first name of the voter.")
    surname: str = Field(..., description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    previous_surname: Optional[str] = Field(None, description="The previous surname of the voter.")
    date_of_birth: datetime = Field(..., description="The date of birth of the voter.")
    email: str = Field(..., description="The email address of the voter.")
    national_insurance_number: Optional[str] = Field(None, description="The national insurance number of the voter.")
    passports: list[PassportEntry] = Field(default_factory=list, description="Passport entries for the voter. Required if no NI number.")
    nationality_category: str = Field(..., description="The nationality category of the voter.")
    immigration_status: Optional[str] = Field(None, description="The immigration status (non-British voters only).")
    immigration_status_expiry: Optional[datetime] = Field(None, description="When the immigration status expires.")
    constituency_id: UUID = Field(..., description="The constituency identifier for the voter.")
    renew_by: datetime = Field(..., description="The date and time the voter's account needs to be renewed by.")
    registration_status: str = Field(..., description="The registration status of the voter.")

    @model_validator(mode="after")
    def require_ni_or_passport(self) -> "VoterRegistrationRequest":
        ni = self.national_insurance_number
        has_ni = ni is not None and ni.strip() != ""
        has_passport = len(self.passports) > 0
        if not has_ni and not has_passport:
            raise ValueError(
                "At least one form of identity is required: "
                "provide a national insurance number or at least one passport entry."
            )
        return self


class VerifyIdentityRequest(RequestSchema):
    """Request model for verifying a voter's identity by name and address."""
    full_name: str = Field(..., description="The voter's full name (first name and surname).")
    address_line1: str = Field(..., description="Address line 1.")
    address_line2: Optional[str] = Field(None, description="Address line 2.")
    city: str = Field(..., description="City or town.")
    postcode: str = Field(..., description="Postcode.")


class VerifyIdentityResponse(ResponseSchema):
    """Response model for a successful identity verification."""
    verified: bool = Field(..., description="Whether the voter's identity was verified.")
    voter_id: Optional[str] = Field(None, description="The voter's ID if verified.")
    message: str = Field(..., description="A message describing the verification result.")


class VoterUpdateRequest(RequestSchema):
    """Voter update request model.

    Passport entries are managed separately via the passport sub-routes.
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
    constituency_id: Optional[UUID] = Field(None, description="The constituency identifier for the voter.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the voter's account needs to be renewed by.")
    registration_status: Optional[str] = Field(None, description="The registration status of the voter.")
    failed_auth_attempts: Optional[int] = Field(None, description="The number of failed authentication attempts for the voter.")
    locked_until: Optional[datetime] = Field(None, description="The date and time the voter was locked until.")

