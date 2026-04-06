# official.py - Official schemas for the e-voting system.
from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from app.models.sqlalchemy.election_official import OfficialRole
from pydantic import Field
from typing import Optional
from datetime import datetime


class OfficialItem(ResponseSchema):
    """Official response model."""
    id: str = Field(..., description="The unique identifier for the official.")
    username: str = Field(..., description="The username of the official.")
    first_name: Optional[str] = Field(None, description="The first name of the official.")
    last_name: Optional[str] = Field(None, description="The last name of the official.")
    email: Optional[str] = Field(None, description="The email address of the official.")
    role: str = Field(..., description="The role of the official (ADMIN or OFFICER).")
    is_active: bool = Field(..., description="Whether the official is currently active.")
    must_reset_password: bool = Field(..., description="Whether the official must reset their password.")
    failed_login_attempts: int = Field(..., description="The number of failed login attempts.")
    created_by: Optional[str] = Field(None, description="The ID of the admin who created this official.")
    last_login_at: Optional[datetime] = Field(None, description="When the official last logged in.")
    locked_until: Optional[datetime] = Field(None, description="Account lock expiry time.")


class CreateOfficialRequest(RequestSchema):
    """Create an election official (admin-only operation)."""
    username: str = Field(..., min_length=3, max_length=255, description="Unique username for the official.")
    first_name: Optional[str] = Field(None, max_length=255, description="First name of the official.")
    last_name: Optional[str] = Field(None, max_length=255, description="Last name of the official.")
    email: Optional[str] = Field(None, max_length=255, description="Email address of the official.")
    password: Optional[str] = Field(None, min_length=8, max_length=128, description="Temporary password. If omitted, one is generated automatically.")
    role: OfficialRole = Field(..., description="Role to assign (ADMIN or OFFICER).")
    created_by: Optional[str] = Field(None, description="ID of the admin creating this official.")


class UpdateOfficialRequest(RequestSchema):
    """Update an election official's mutable fields."""
    first_name: Optional[str] = Field(None, max_length=255, description="Updated first name.")
    last_name: Optional[str] = Field(None, max_length=255, description="Updated last name.")
    email: Optional[str] = Field(None, max_length=255, description="Updated email address.")
    role: Optional[OfficialRole] = Field(None, description="Updated role (admin-only).")
    is_active: Optional[bool] = Field(None, description="Active status (admin-only).")
