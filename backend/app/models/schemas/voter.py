# voter.py - Voter schemas for the e-voting system.
from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from datetime import datetime
from typing import Optional

class VoterItem(ResponseSchema):
    """Voter response model."""
    id: str = Field(..., description="The unique identifier for the voter.")
    national_insurance_number: Optional[str] = Field(None, description="The national insurance number for the voter.")
    passport_number: Optional[str] = Field(None, description="The passport number for the voter.")
    passport_country: Optional[str] = Field(None, description="The country of the voter's passport.")
    first_name: str = Field(..., description="The first name of the voter.")
    surname: str = Field(..., description="The surname of the voter.")
    previous_first_name: Optional[str] = Field(None, description="The previous first name of the voter.")
    maiden_name: Optional[str] = Field(None, description="The maiden name of the voter.")
    date_of_birth: datetime = Field(..., description="The date of birth of the voter.")
    email: str = Field(..., description="The email address of the voter.")
    voter_reference: str = Field(..., description="The voter reference for the voter.")
    consituency_id: str = Field(..., description="The constituency identifier for the voter.")
    registration_status: str = Field(..., description="The registration status of the voter.")
    failed_auth_attempts: int = Field(..., description="The number of failed authentication attempts for the voter.")
    locked_until: Optional[datetime] = Field(None, description="The date and time the voter was locked until.")
    registered_at: datetime = Field(..., description="The date and time the voter was registered.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the voter's account needs to be renewed by.")


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
    consituency_id: str = Field(..., description="The constituency identifier for the voter.")
    renew_by: datetime = Field(..., description="The date and time the voter's account needs to be renewed by.")
    registration_status: str = Field(..., description="The registration status of the voter.")
    failed_auth_attempts: int = Field(..., description="The number of failed authentication attempts for the voter.")
    locked_until: Optional[datetime] = Field(None, description="The date and time the voter was locked until.")
    registered_at: datetime = Field(..., description="The date and time the voter was registered.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the voter's account needs to be renewed by.")
    

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
    consituency_id: Optional[str] = Field(None, description="The constituency identifier for the voter.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the voter's account needs to be renewed by.") 
    registration_status: Optional[str] = Field(None, description="The registration status of the voter.")
    failed_auth_attempts: Optional[int] = Field(None, description="The number of failed authentication attempts for the voter.")
    locked_until: Optional[datetime] = Field(None, description="The date and time the voter was locked until.")
      


