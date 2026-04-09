"""Pydantic schemas for email-based verification code flow."""

from pydantic import Field

from app.models.base.pydantic_base import RequestSchema, ResponseSchema


class SendCodeRequest(RequestSchema):
    """Request to send a verification code to the voter's registered email."""
    voter_id: str = Field(..., description="UUID of the voter.")


class SendCodeResponse(ResponseSchema):
    """Acknowledgement that a code was sent (does not reveal the code)."""
    id: str = Field(default="", description="Placeholder.")
    sent: bool = Field(..., description="Whether the code was sent successfully.")
    message: str = Field(..., description="Human-readable result.")


class VerifyCodeRequest(RequestSchema):
    """Submit the 6-digit code for verification."""
    voter_id: str = Field(..., description="UUID of the voter.")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code.")


class VerifyCodeResponse(ResponseSchema):
    """Result of code verification."""
    id: str = Field(default="", description="Placeholder.")
    verified: bool = Field(..., description="Whether the code was correct and valid.")
    message: str = Field(..., description="Human-readable result.")
