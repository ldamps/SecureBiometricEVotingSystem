"""Pydantic schemas for the match-on-device biometric flow.

Enrollment: mobile device registers a public key bound to face+ear biometrics.
Verification: server issues a challenge, device signs it after local match.
"""

from pydantic import Field
from typing import Optional
from datetime import datetime

from app.models.base.pydantic_base import ResponseSchema, RequestSchema


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class EnrollDeviceRequest(RequestSchema):
    """Sent by the mobile app after the voter enrols face + ear on-device."""
    voter_id: str = Field(..., description="UUID of the registered voter.")
    public_key_pem: str = Field(
        ...,
        description="PEM-encoded ECDSA P-256 public key (SubjectPublicKeyInfo).",
    )
    device_id: str = Field(..., description="Opaque device identifier from the mobile app.")
    modalities: str = Field(
        default="face,ear",
        description="Comma-separated biometric modalities enrolled on the device.",
    )
    attestation: Optional[str] = Field(
        None,
        description="Base64-encoded device attestation blob (Android SafetyNet / iOS DeviceCheck).",
    )
    device_label: Optional[str] = Field(
        None,
        description="Human-readable label for the device (e.g. 'My iPhone').",
    )
    encrypted_key_bundle: Optional[str] = Field(
        None,
        description="JSON-encoded AES-GCM encrypted ECDSA private key bundle. "
        "Encrypted with a key derived from the voter's biometric features. "
        "The server cannot decrypt this — only a matching biometric can.",
    )


class EnrollDeviceResponse(ResponseSchema):
    """Returned after a successful device enrollment."""
    id: str = Field(..., description="UUID of the created device credential.")
    voter_id: str = Field(..., description="UUID of the voter.")
    device_id: str = Field(..., description="The enrolled device identifier.")
    modalities: str = Field(..., description="Enrolled biometric modalities.")
    is_active: bool = Field(..., description="Whether the credential is active.")
    enrolled_at: datetime = Field(..., description="When the credential was created.")


# ---------------------------------------------------------------------------
# Challenge-response verification
# ---------------------------------------------------------------------------

class CreateChallengeRequest(RequestSchema):
    """Request a new verification challenge for a voter."""
    voter_id: str = Field(..., description="UUID of the voter requesting verification.")


class CreateChallengeResponse(ResponseSchema):
    """Server-generated challenge the device must sign."""
    id: str = Field(..., description="UUID of the challenge (used when submitting the response).")
    challenge: str = Field(..., description="Hex-encoded random challenge bytes.")
    expires_at: datetime = Field(..., description="When this challenge expires (UTC).")


class VerifyBiometricRequest(RequestSchema):
    """Submitted by the device after a successful on-device biometric match."""
    challenge_id: str = Field(..., description="UUID of the challenge being answered.")
    device_id: Optional[str] = Field(None, description="Device that performed the biometric match (optional for web-only flows).")
    signature: str = Field(
        ...,
        description="Base64-encoded ECDSA signature of the challenge bytes.",
    )


class VerifyBiometricResponse(ResponseSchema):
    """Result of the biometric verification."""
    id: str = Field(default="", description="Placeholder (no entity returned).")
    verified: bool = Field(..., description="Whether the signature was valid and the voter is authenticated.")
    voter_id: Optional[str] = Field(None, description="UUID of the verified voter (if verified).")
    message: str = Field(..., description="Human-readable result description.")


# ---------------------------------------------------------------------------
# Device credential listing
# ---------------------------------------------------------------------------

class DeviceCredentialItem(ResponseSchema):
    """Public view of a registered device credential (no secrets)."""
    id: str = Field(..., description="UUID of the credential.")
    voter_id: str = Field(..., description="UUID of the voter.")
    device_id: str = Field(..., description="Device identifier.")
    modalities: str = Field(..., description="Enrolled biometric modalities.")
    device_label: Optional[str] = Field(None, description="Human-readable device label.")
    is_active: bool = Field(..., description="Whether the credential is currently active.")
    last_used_at: Optional[datetime] = Field(None, description="Last successful verification time.")
    created_at: datetime = Field(..., description="When the credential was enrolled.")
    encrypted_key_bundle: Optional[str] = Field(None, description="AES-GCM encrypted private key bundle (biometric-bound).")
