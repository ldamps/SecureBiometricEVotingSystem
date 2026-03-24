# referendum.py - Referendum schemas for the e-voting system.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from typing import Optional
from datetime import datetime


class ReferendumItem(ResponseSchema):
    """Referendum response model."""
    id: str = Field(..., description="The unique identifier for the referendum.")
    title: str = Field(..., description="The title of the referendum.")
    question: str = Field(..., description="The yes/no question posed to voters.")
    description: Optional[str] = Field(None, description="Additional context for the question.")
    scope: str = Field(..., description="The scope of the referendum (NATIONAL, REGIONAL, LOCAL).")
    status: str = Field(..., description="The status of the referendum (OPEN, CLOSED).")
    voting_opens: Optional[datetime] = Field(None, description="When voting opens.")
    voting_closes: Optional[datetime] = Field(None, description="When voting closes.")
    is_active: bool = Field(..., description="Whether the referendum is currently active.")


class CreateReferendumRequest(RequestSchema):
    """Create referendum request model."""
    title: str = Field(..., description="The title of the referendum.")
    question: str = Field(..., description="The yes/no question posed to voters.")
    description: Optional[str] = Field(None, description="Additional context for the question.")
    scope: str = Field(..., description="The scope of the referendum (NATIONAL, REGIONAL, LOCAL).")
    status: Optional[str] = Field("OPEN", description="The status of the referendum.")
    voting_opens: Optional[datetime] = Field(None, description="When voting opens.")
    voting_closes: Optional[datetime] = Field(None, description="When voting closes.")


class UpdateReferendumRequest(RequestSchema):
    """Update referendum request model."""
    question: Optional[str] = Field(None, description="The yes/no question posed to voters.")
    description: Optional[str] = Field(None, description="Additional context for the question.")
    status: Optional[str] = Field(None, description="The status of the referendum.")
    voting_opens: Optional[datetime] = Field(None, description="When voting opens.")
    voting_closes: Optional[datetime] = Field(None, description="When voting closes.")
    is_active: Optional[bool] = Field(None, description="Whether the referendum is currently active.")
