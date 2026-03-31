# auth.py - Authentication schemas for the e-voting system.

from app.models.base.pydantic_base import RequestSchema, ResponseSchema
from pydantic import Field
from typing import Optional
from datetime import datetime


class LoginRequest(RequestSchema):
    """Login with username and password."""
    username: str = Field(..., min_length=1, max_length=255, description="Official's username.")
    password: str = Field(..., min_length=1, max_length=128, description="Official's password.")


class TokenResponse(ResponseSchema):
    """JWT token pair returned after successful login."""
    access_token: str = Field(..., description="Short-lived JWT access token.")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token.")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer').")
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class RefreshTokenRequest(RequestSchema):
    """Exchange a refresh token for a new access token."""
    refresh_token: str = Field(..., description="The refresh token to exchange.")


class ChangePasswordRequest(RequestSchema):
    """Change the current user's password."""
    current_password: str = Field(..., min_length=1, max_length=128, description="Current password.")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password (min 8 chars).")


class ChangePasswordResponse(ResponseSchema):
    """Confirmation of a successful password change."""
    detail: str = Field(..., description="Confirmation message.")


class AuthenticatedUser(ResponseSchema):
    """The currently authenticated user's profile."""
    id: str = Field(..., description="Official ID.")
    username: str = Field(..., description="Username.")
    role: str = Field(..., description="Role (ADMIN or OFFICER).")
    must_reset_password: bool = Field(..., description="Whether a password reset is required.")
