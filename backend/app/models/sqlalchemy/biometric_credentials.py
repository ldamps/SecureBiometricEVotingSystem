"""Biometric credential models for match-on-device architecture.

DeviceCredential — stores the public key for a voter's enrolled device.
BiometricChallenge — single-use nonce for challenge-response verification.

NO biometric template data is stored server-side.  All biometric matching
(face + ear) happens exclusively on the voter's mobile device.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.sqlalchemy.voter import Voter


# ---------------------------------------------------------------------------
# DeviceCredential — replaces the old BiometricTemplate
# ---------------------------------------------------------------------------

class DeviceCredential(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Public-key credential registered from a voter's mobile device.

    The voter enrols face + ear biometrics on their phone.  The device
    generates an ECDSA P-256 key pair whose private key is bound to a
    successful on-device biometric match.  Only the **public key** is
    sent to this server — the biometric templates never leave the device.

    During verification the server issues a random challenge; the device
    signs it (after a local biometric match) and the server verifies the
    signature against the stored public key.
    """

    __tablename__ = "device_credential"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which biometric modalities the device enrolled (e.g. "face,ear")
    modalities: Mapped[str] = mapped_column(
        String(255), nullable=False, default="face,ear"
    )

    # PEM-encoded ECDSA P-256 public key (SubjectPublicKeyInfo)
    public_key_pem: Mapped[str] = mapped_column(Text, nullable=False)

    # Opaque device identifier supplied by the mobile app
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Optional device attestation blob (platform key attestation from
    # Android SafetyNet / iOS DeviceCheck) — stored as base64 text.
    attestation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Human-readable label the voter chose ("My iPhone", "Work phone", …)
    device_label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    last_used_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Relationships ----------
    voter: Mapped["Voter"] = relationship(
        "Voter",
        back_populates="device_credentials",
        lazy="select",
    )


# ---------------------------------------------------------------------------
# BiometricChallenge — single-use nonce for verification
# ---------------------------------------------------------------------------

class BiometricChallenge(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Single-use cryptographic challenge issued to a voter's device.

    The device must sign the challenge (after a local biometric match)
    and return the signature for server-side verification.
    """

    __tablename__ = "biometric_challenge"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Random challenge bytes encoded as hex string
    challenge: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    # Challenge expiry — typically 5 minutes from creation
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    used_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
