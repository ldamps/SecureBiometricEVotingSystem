# voter.py - Voter schemas for the e-voting system.
from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
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
    passport_number: Optional[str] = Field(None, description="The passport number for the voter.")
    passport_country: Optional[str] = Field(None, description="The country of the voter's passport.")
    passport_expiry_date: Optional[datetime] = Field(None, description="The expiry date of the voter's passport.")
    first_name: Optional[str] = Field(None, description="The first name of the voter.")
    surname: Optional[str] = Field(None, description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    maiden_name: Optional[str] = Field(None, description="The maiden name of the voter.")
    date_of_birth: Optional[datetime] = Field(None, description="The date of birth of the voter.")
    email: Optional[str] = Field(None, description="The email address of the voter.")
    voter_reference: Optional[str] = Field(None, description="The voter reference for the voter.")
    constituency_id: Optional[UUID] = Field(None, description="The constituency identifier for the voter.")
    registration_status: str = Field(..., description="The registration status of the voter.")
    failed_auth_attempts: int = Field(..., description="The number of failed authentication attempts for the voter.")
    locked_until: Optional[datetime] = Field(None, description="The date and time the voter was locked until.")
    registered_at: Optional[datetime] = Field(None, description="The date and time the voter was registered.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the voter's account needs to be renewed by.")

    @classmethod
    def from_orm_voter(cls, voter: Any) -> "VoterItem":
        """Build VoterItem from a Voter ORM instance."""
        return cls.model_validate(voter_orm_to_item_dict(voter))


class VoterRegistrationRequest(RequestSchema):
    """Voter registration request model."""
    first_name: str = Field(..., description="The first name of the voter.")
    surname: str = Field(..., description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    previous_surname: Optional[str] = Field(None, description="The previous surname of the voter.")
    date_of_birth: datetime = Field(..., description="The date of birth of the voter.")
    email: str = Field(..., description="The email address of the voter.")
    national_insurance_number: Optional[str] = Field(None, description="The national insurance number of the voter.")
    passport_number: Optional[str] = Field(None, description="The passport number of the voter.")
    passport_country: Optional[str] = Field(None, description="The country of the voter's passport.")
    passport_expiry_date: Optional[datetime] = Field(None, description="The expiry date of the voter's passport.")
    constituency_id: UUID = Field(..., description="The constituency identifier for the voter.")
    renew_by: datetime = Field(..., description="The date and time the voter's account needs to be renewed by.")
    registration_status: str = Field(..., description="The registration status of the voter.")


class VoterUpdateRequest(RequestSchema):
    """Voter update request model."""
    first_name: Optional[str] = Field(None, description="The first name of the voter.")
    surname: Optional[str] = Field(None, description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    previous_surname: Optional[str] = Field(None, description="The previous surname of the voter.")
    date_of_birth: Optional[datetime] = Field(None, description="The date of birth of the voter.")
    email: Optional[str] = Field(None, description="The email address of the voter.")
    passport_number: Optional[str] = Field(None, description="The passport number of the voter.")
    passport_country: Optional[str] = Field(None, description="The country of the voter's passport.")
    passport_expiry_date: Optional[datetime] = Field(None, description="The expiry date of the voter's passport.")
    constituency_id: Optional[UUID] = Field(None, description="The constituency identifier for the voter.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the voter's account needs to be renewed by.") 
    registration_status: Optional[str] = Field(None, description="The registration status of the voter.")
    failed_auth_attempts: Optional[int] = Field(None, description="The number of failed authentication attempts for the voter.")
    locked_until: Optional[datetime] = Field(None, description="The date and time the voter was locked until.")
      


