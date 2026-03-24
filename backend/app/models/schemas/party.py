# party.py - Party schemas for the e-voting system.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class PartyItem(ResponseSchema):
    """Party response model."""
    id: str = Field(..., description="The unique identifier for the party.")
    party_name: str = Field(..., description="The name of the party.")
    abbreviation: Optional[str] = Field(None, description="The abbreviation of the party.")
    is_active: bool = Field(..., description="Whether the party is currently active.")



class CreateParty(
    RequestSchema
):
    """Create party request model."""
    party_name: str = Field(..., description="The name of the party.")
    abbreviation: Optional[str] = Field(None, description="The abbreviation of the party.")
    is_active: bool = Field(True, description="Whether the party is currently active.")


class UpdateParty(
    RequestSchema
):
    """Update party request model."""
    party_name: Optional[str] = Field(None, description="The name of the party.")
    abbreviation: Optional[str] = Field(None, description="The abbreviation of the party.")
    is_active: Optional[bool] = Field(None, description="Whether the party is currently active.")

class DeleteParty(
    RequestSchema
):
    """Soft delete party request model."""
    party_id: UUID = Field(..., description="The unique identifier for the party.")

