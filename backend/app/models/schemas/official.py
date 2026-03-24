# official.py - Official schemas for the e-voting system.
from app.models.base.pydantic_base import ResponseSchema
from pydantic import Field
from typing import Optional


class OfficialItem(ResponseSchema):
    """Official response model."""
    id: str = Field(..., description="The unique identifier for the official.")
    username: str = Field(..., description="The username of the official.")
    first_name: str = Field(..., description="The first name of the official.")
    last_name: str = Field(..., description="The last name of the official.")
    email: str = Field(..., description="The email address of the official.")
    role: str = Field(..., description="The role of the official.")
    is_active: bool = Field(..., description="Whether the official is currently active.")
    must_reset_password: bool = Field(..., description="Whether the official must reset their password.")
    failed_login_attempts: int = Field(..., description="The number of failed login attempts for the official.")

