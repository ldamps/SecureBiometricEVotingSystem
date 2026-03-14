from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from datetime import datetime
from typing import Optional


class VoterItem(ResponseSchema):
    """Voter response model."""
    id: str = Field(..., description="The unique identifier for the voter.")
    national_insurance_number: str = Field(..., description="The national insurance number for the voter.")
    first_name: str = Field(..., description="The first name of the voter.")
    surname: str = Field(..., description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    maiden_name: Optional[str] = Field(None, description="The maiden name of the voter.")
    date_of_birth: datetime = Field(..., description="The date of birth of the voter.")
    email: str = Field(..., description="The email address of the voter.")
    civil_servant: bool = Field(..., description="Whether the voter is a civil servant.")
    council_employee: bool = Field(..., description="Whether the voter is a council employee.")
    armed_forces_member: bool = Field(..., description="Whether the voter is an armed forces member.")
    voter_reference: str = Field(..., description="The voter reference for the voter.")
    consituency_id: str = Field(..., description="The constituency identifier for the voter.")
    registration_status: str = Field(..., description="The registration status of the voter.")
    failed_auth_attempts: int = Field(..., description="The number of failed authentication attempts for the voter.")
    locked_until: Optional[datetime] = Field(None, description="The date and time the voter was locked until.")
    registered_at: datetime = Field(..., description="The date and time the voter was registered.")


class VoterUpdateRequest(RequestSchema):
    """Voter update request model."""


