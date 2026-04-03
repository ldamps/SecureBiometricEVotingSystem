"""Service layer for match-on-device biometric verification.

Handles three operations:
1. Enrollment — register a device's public key for a voter.
2. Challenge — issue a single-use cryptographic nonce.
3. Verification — validate the device's ECDSA signature of the challenge.
"""

from __future__ import annotations

import base64
import os
import structlog
from datetime import datetime, timedelta, timezone
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sqlalchemy.biometric_credentials import DeviceCredential, BiometricChallenge
from app.models.schemas.biometric import (
    EnrollDeviceRequest,
    EnrollDeviceResponse,
    CreateChallengeRequest,
    CreateChallengeResponse,
    VerifyBiometricRequest,
    VerifyBiometricResponse,
    DeviceCredentialItem,
)
from app.application.core.exceptions import ValidationError
from app.repository.biometric_credentials_repo import BiometricCredentialsRepository
from app.repository.biometric_challenge_repo import BiometricChallengeRepository
from app.repository.voter_repo import VoterRepository
from app.repository.audit_log_repo import AuditLogRepository
from app.models.sqlalchemy.audit_log import AuditLog

logger = structlog.get_logger()

# Challenge validity window
CHALLENGE_TTL = timedelta(minutes=5)


class BiometricService:
    """Orchestrates the match-on-device biometric flow."""

    def __init__(
        self,
        credentials_repo: BiometricCredentialsRepository,
        challenge_repo: BiometricChallengeRepository,
        voter_repo: VoterRepository,
        session: AsyncSession,
    ):
        self.credentials_repo = credentials_repo
        self.challenge_repo = challenge_repo
        self.voter_repo = voter_repo
        self.session = session
        self._audit_log_repo = AuditLogRepository()


    async def enroll_device(self, request: EnrollDeviceRequest) -> EnrollDeviceResponse:
        """Register a mobile device's public key for a voter.

        Validates the PEM key is a valid ECDSA P-256 public key, then
        persists the credential.  If the same voter+device already has an
        active credential, it is deactivated first (re-enrollment).
        """
        voter_id = UUID(request.voter_id)

        # Verify the voter exists before enrolling
        await self.voter_repo.get_voter_by_id(self.session, voter_id)

        # Validate the public key parses as ECDSA P-256
        self._parse_public_key(request.public_key_pem)

        # Deactivate any existing credential for this voter+device
        existing = await self.credentials_repo.get_active_by_voter_and_device(
            self.session, voter_id, request.device_id
        )
        if existing:
            await self.credentials_repo.deactivate(self.session, existing.id)
            logger.info(
                "Deactivated previous credential for re-enrollment",
                old_credential_id=existing.id,
            )

        credential = DeviceCredential(
            voter_id=voter_id,
            public_key_pem=request.public_key_pem,
            device_id=request.device_id,
            modalities=request.modalities,
            attestation=request.attestation,
            device_label=request.device_label,
            encrypted_key_bundle=request.encrypted_key_bundle,
        )
        credential = await self.credentials_repo.create(self.session, credential)

        # Audit: biometric enrolled
        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="BIOMETRIC_ENROLLED",
                action="CREATE",
                summary=f"Biometric device enrolled for voter {voter_id}",
                resource_type="biometric_credential",
                resource_id=credential.id,
                actor_type="VOTER",
                actor_id=voter_id,
            ),
        )

        return EnrollDeviceResponse(
            id=str(credential.id),
            voter_id=str(credential.voter_id),
            device_id=credential.device_id,
            modalities=credential.modalities,
            is_active=credential.is_active,
            enrolled_at=credential.created_at,
        )


    async def create_challenge(
        self, request: CreateChallengeRequest
    ) -> CreateChallengeResponse:
        """Generate a fresh random challenge for the voter's device to sign."""
        voter_id = UUID(request.voter_id)

        # Verify the voter exists before creating a challenge
        await self.voter_repo.get_voter_by_id(self.session, voter_id)

        # 32 random bytes → 64 hex chars
        challenge_bytes = os.urandom(32)
        challenge_hex = challenge_bytes.hex()

        now = datetime.now(timezone.utc)
        challenge = BiometricChallenge(
            voter_id=voter_id,
            challenge=challenge_hex,
            expires_at=now + CHALLENGE_TTL,
        )
        challenge = await self.challenge_repo.create(self.session, challenge)

        return CreateChallengeResponse(
            id=str(challenge.id),
            challenge=challenge_hex,
            expires_at=challenge.expires_at,
        )

    async def verify_biometric(
        self, request: VerifyBiometricRequest
    ) -> VerifyBiometricResponse:
        """Verify the ECDSA signature the device produced after an on-device
        biometric match.

        Steps:
        1. Retrieve and validate the challenge (exists, not used, not expired).
        2. Find the active credential for the voter + device.
        3. Verify the ECDSA signature over the challenge bytes.
        4. Mark the challenge as used and update last_used_at on the credential.
        """
        challenge_id = UUID(request.challenge_id)

        # 1. Retrieve challenge
        challenge = await self.challenge_repo.get_by_id(self.session, challenge_id)

        if challenge.is_used:
            return VerifyBiometricResponse(
                verified=False,
                message="Challenge has already been used.",
            )

        now = datetime.now(timezone.utc)
        if now > challenge.expires_at:
            return VerifyBiometricResponse(
                verified=False,
                message="Challenge has expired.",
            )

        # 2. Find active credential
        credential = await self.credentials_repo.get_active_by_voter_and_device(
            self.session, challenge.voter_id, request.device_id
        )
        if not credential:
            return VerifyBiometricResponse(
                verified=False,
                message="No active device credential found for this voter and device.",
            )

        # 3. Verify ECDSA signature
        try:
            public_key = self._parse_public_key(credential.public_key_pem)
            signature_bytes = base64.b64decode(request.signature)
            challenge_bytes = bytes.fromhex(challenge.challenge)

            public_key.verify(
                signature_bytes,
                challenge_bytes,
                ec.ECDSA(hashes.SHA256()),
            )
        except (InvalidSignature, Exception) as exc:
            logger.warning(
                "Biometric signature verification failed",
                voter_id=str(challenge.voter_id),
                error=str(exc),
            )

            # Audit: biometric verification failed
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="BIOMETRIC_FAILED",
                    action="VERIFY",
                    summary=f"Biometric verification failed for voter {challenge.voter_id}",
                    resource_type="biometric_credential",
                    actor_type="VOTER",
                    actor_id=challenge.voter_id,
                ),
            )

            return VerifyBiometricResponse(
                verified=False,
                message="Signature verification failed.",
            )

        # 4. Mark used & update last_used_at
        await self.challenge_repo.mark_used(self.session, challenge_id)
        await self.credentials_repo.touch_last_used(self.session, credential.id)

        # Audit: biometric verification succeeded
        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="BIOMETRIC_VERIFIED",
                action="VERIFY",
                summary=f"Biometric verification succeeded for voter {challenge.voter_id}",
                resource_type="biometric_credential",
                resource_id=credential.id,
                actor_type="VOTER",
                actor_id=challenge.voter_id,
            ),
        )

        logger.info(
            "Biometric verification succeeded",
            voter_id=str(challenge.voter_id),
            credential_id=str(credential.id),
        )

        return VerifyBiometricResponse(
            verified=True,
            voter_id=str(challenge.voter_id),
            message="Biometric verification successful.",
        )

    async def list_credentials(self, voter_id: UUID) -> list[DeviceCredentialItem]:
        """List all device credentials for a voter."""
        rows = await self.credentials_repo.list_by_voter(self.session, voter_id)
        return [
            DeviceCredentialItem(
                id=str(row.id),
                voter_id=str(row.voter_id),
                device_id=row.device_id,
                modalities=row.modalities,
                device_label=row.device_label,
                is_active=row.is_active,
                last_used_at=row.last_used_at,
                created_at=row.created_at,
                encrypted_key_bundle=row.encrypted_key_bundle,
            )
            for row in rows
        ]

    async def revoke_credential(self, credential_id: UUID) -> None:
        """Deactivate a device credential."""
        await self.credentials_repo.deactivate(self.session, credential_id)

    @staticmethod
    def _parse_public_key(pem: str) -> ec.EllipticCurvePublicKey:
        """Parse and validate a PEM-encoded ECDSA P-256 public key."""
        try:
            key = serialization.load_pem_public_key(pem.encode("utf-8"))
        except (ValueError, Exception) as exc:
            raise ValidationError(f"Invalid PEM public key: {exc}") from exc
        if not isinstance(key, ec.EllipticCurvePublicKey):
            raise ValidationError("Key is not an elliptic-curve public key")
        if not isinstance(key.curve, ec.SECP256R1):
            raise ValidationError("Key must use the P-256 (secp256r1) curve")
        return key