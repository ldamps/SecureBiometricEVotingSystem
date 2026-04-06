"""Pydantic request / response schemas for KYC verification."""

from app.models.base.pydantic_base import RequestSchema, ResponseSchema
from pydantic import Field
from typing import Optional


class CreateKYCSessionRequest(RequestSchema):
    """Request to create a new KYC verification session."""
    email: Optional[str] = Field(None, description="Optional email to associate with the session for tracking.")
    allowed_document_types: Optional[list[str]] = Field(
        None,
        description="Stripe document types to accept: passport, driving_license, id_card. Defaults to all three.",
    )


class CreateKYCSessionResponse(ResponseSchema):
    """Response containing the Stripe session details for the frontend."""
    session_id: str = Field(..., description="The Stripe VerificationSession ID.")
    client_secret: str = Field(..., description="Client secret for the embedded verification UI.")


class KYCExtractedAddress(ResponseSchema):
    """Address extracted from the identity document."""
    line1: str = Field("", description="Address line 1.")
    line2: str = Field("", description="Address line 2.")
    city: str = Field("", description="City.")
    postal_code: str = Field("", description="Postal code.")
    country: str = Field("", description="Country code (e.g. GB).")


class KYCExtractedData(ResponseSchema):
    """Data extracted from the verified identity document."""
    first_name: str = Field("", description="First name from the document.")
    last_name: str = Field("", description="Last name from the document.")
    date_of_birth: str = Field("", description="Date of birth in dd/mm/yyyy format.")
    document_number: str = Field("", description="Document number (e.g. passport number).")
    document_type: str = Field("", description="Document type (e.g. passport, driving_license).")
    address: Optional[KYCExtractedAddress] = Field(None, description="Address from the document, if available.")


class KYCVerifiedOutputsResponse(ResponseSchema):
    """Response containing the data extracted from a verified identity document."""
    session_id: str = Field(..., description="The Stripe VerificationSession ID.")
    verified: bool = Field(..., description="Whether the session has been verified.")
    extracted_data: Optional[KYCExtractedData] = Field(None, description="Extracted data from the document. Null if not yet verified.")


class KYCStatusResponse(ResponseSchema):
    """Response containing the current verification status."""
    session_id: str = Field(..., description="The Stripe VerificationSession ID.")
    status: str = Field(..., description="Current status: requires_input, processing, verified, or canceled.")
    last_error: Optional[str] = Field(None, description="Last error message, if any.")
