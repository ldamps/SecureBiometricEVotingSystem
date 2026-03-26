# constituency.py - Read-only constituency response schemas.

from app.models.base.pydantic_base import ResponseSchema
from pydantic import Field
from typing import Optional


class ConstituencyItem(ResponseSchema):
    """Constituency response model (read-only)."""

    id: str = Field(..., description="The unique identifier for the constituency.")
    name: str = Field(..., description="The name of the constituency (UK county).")
    country: str = Field(..., description="The country within the UK (England, Scotland, Wales, Northern Ireland).")
    county: Optional[str] = Field(None, description="The county name (same as name for most constituencies).")
    region: Optional[str] = Field(None, description="The region within the country.")
    is_active: bool = Field(..., description="Whether the constituency is currently active.")
