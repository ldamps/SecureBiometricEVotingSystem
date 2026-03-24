# voter_passport.py - Voter passport schemas for the e-voting system.
from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from datetime import datetime
from typing import Optional


class VoterPassportItem(ResponseSchema):
    """Voter passport response model."""
    id: str = Field(..., description="The unique identifier for the passport entry.")
    passport_number: Optional[str] = Field(None, description="The passport number.")
    issuing_country: Optional[str] = Field(None, description="The country that issued the passport.")
    expiry_date: Optional[datetime] = Field(None, description="The passport expiry date.")
    is_primary: bool = Field(..., description="Whether this is the primary passport for the voter.")


class CreateVoterPassportRequest(RequestSchema):
    """Request to add a passport to a voter."""
    passport_number: str = Field(..., description="The passport number.")
    issuing_country: str = Field(..., description="The country that issued the passport.")
    expiry_date: Optional[datetime] = Field(None, description="The passport expiry date.")
    is_primary: bool = Field(False, description="Whether this is the primary passport for the voter.")


class UpdateVoterPassportRequest(RequestSchema):
    """Request to update a voter's passport."""
    passport_number: Optional[str] = Field(None, description="The passport number.")
    issuing_country: Optional[str] = Field(None, description="The country that issued the passport.")
    expiry_date: Optional[datetime] = Field(None, description="The passport expiry date.")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary passport for the voter.")


class PassportEntry(RequestSchema):
    """A passport entry submitted as part of voter registration."""
    passport_number: str = Field(..., description="The passport number.")
    issuing_country: str = Field(..., description="The country that issued the passport.")
    expiry_date: Optional[datetime] = Field(None, description="The passport expiry date.")
    is_primary: bool = Field(False, description="Whether this is the primary passport for the voter.")
