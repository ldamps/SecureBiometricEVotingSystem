"""Unit tests for BiometricService — key validation, challenge lifecycle, signature verify."""

import base64
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils as asym_utils

from app.application.core.exceptions import ValidationError
from app.service.biometric_service import BiometricService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_p256_keypair():
    """Generate an ECDSA P-256 key pair; return (private_key, public_key_pem)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_key, public_pem


def _make_service(session):
    credentials_repo = AsyncMock()
    credentials_repo.list_active_by_voter = AsyncMock(return_value=[])
    credentials_repo.create = AsyncMock(side_effect=lambda s, cred: cred)
    challenge_repo = AsyncMock()
    voter_repo = AsyncMock()
    voter_repo.get_voter_by_id = AsyncMock()
    address_repo = AsyncMock()
    address_repo.get_all_addresses_by_voter_id = AsyncMock(return_value=[])

    svc = BiometricService(
        credentials_repo=credentials_repo,
        challenge_repo=challenge_repo,
        voter_repo=voter_repo,
        session=session,
        address_repo=address_repo,
    )
    svc._audit_log_repo = AsyncMock()
    return svc


def _make_credential(public_key_pem: str, voter_id: uuid.UUID, device_id: str = "dev1"):
    cred = MagicMock()
    cred.id = uuid.uuid4()
    cred.voter_id = voter_id
    cred.public_key_pem = public_key_pem
    cred.device_id = device_id
    cred.is_active = True
    cred.last_used_at = None
    cred.created_at = datetime.now(timezone.utc)
    return cred


def _make_challenge(voter_id: uuid.UUID, challenge_hex: str, expired: bool = False, used: bool = False):
    ch = MagicMock()
    ch.id = uuid.uuid4()
    ch.voter_id = voter_id
    ch.challenge = challenge_hex
    ch.is_used = used
    if expired:
        ch.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    else:
        ch.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    return ch


# ---------------------------------------------------------------------------
# Public key validation
# ---------------------------------------------------------------------------

class TestPublicKeyValidation:
    def test_valid_p256_key_accepted(self):
        _, pem = _generate_p256_keypair()
        key = BiometricService._parse_public_key(pem)
        assert isinstance(key, ec.EllipticCurvePublicKey)

    def test_invalid_pem_raises(self):
        with pytest.raises(ValidationError, match="Invalid PEM"):
            BiometricService._parse_public_key("not-a-key")

    def test_non_ec_key_raises(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        rsa_key = rsa.generate_private_key(65537, 2048)
        rsa_pem = rsa_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        with pytest.raises(ValidationError, match="elliptic-curve"):
            BiometricService._parse_public_key(rsa_pem)

    def test_wrong_curve_raises(self):
        # P-384 instead of P-256
        key = ec.generate_private_key(ec.SECP384R1())
        pem = key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        with pytest.raises(ValidationError, match="P-256"):
            BiometricService._parse_public_key(pem)


# ---------------------------------------------------------------------------
# Challenge lifecycle
# ---------------------------------------------------------------------------

class TestChallengeLifecycle:
    async def test_expired_challenge_returns_not_verified(self, mock_session):
        svc = _make_service(mock_session)
        voter_id = uuid.uuid4()
        _, pub_pem = _generate_p256_keypair()

        challenge = _make_challenge(voter_id, os.urandom(32).hex(), expired=True)
        svc.challenge_repo.get_by_id = AsyncMock(return_value=challenge)

        from app.models.schemas.biometric import VerifyBiometricRequest
        req = VerifyBiometricRequest(
            challenge_id=str(challenge.id),
            signature=base64.b64encode(b"\x00" * 64).decode(),
        )
        result = await svc.verify_biometric(req)
        assert result.verified is False
        assert "expired" in result.message.lower()

    async def test_already_used_challenge_returns_not_verified(self, mock_session):
        svc = _make_service(mock_session)
        voter_id = uuid.uuid4()

        challenge = _make_challenge(voter_id, os.urandom(32).hex(), used=True)
        svc.challenge_repo.get_by_id = AsyncMock(return_value=challenge)

        from app.models.schemas.biometric import VerifyBiometricRequest
        req = VerifyBiometricRequest(
            challenge_id=str(challenge.id),
            signature=base64.b64encode(b"\x00" * 64).decode(),
        )
        result = await svc.verify_biometric(req)
        assert result.verified is False
        assert "already been used" in result.message.lower()


# ---------------------------------------------------------------------------
# ECDSA signature verification
# ---------------------------------------------------------------------------

class TestSignatureVerification:
    async def test_valid_signature_verifies(self, mock_session):
        svc = _make_service(mock_session)
        voter_id = uuid.uuid4()
        private_key, pub_pem = _generate_p256_keypair()

        # Create a challenge
        challenge_bytes = os.urandom(32)
        challenge = _make_challenge(voter_id, challenge_bytes.hex())
        svc.challenge_repo.get_by_id = AsyncMock(return_value=challenge)

        # Create credential
        credential = _make_credential(pub_pem, voter_id)
        svc.credentials_repo.get_active_by_voter_and_device = AsyncMock(return_value=None)
        svc.credentials_repo.get_active_by_voter = AsyncMock(return_value=credential)

        # Sign the challenge with the private key (IEEE P1363 format = r||s, 64 bytes)
        der_sig = private_key.sign(challenge_bytes, ec.ECDSA(hashes.SHA256()))
        r, s = asym_utils.decode_dss_signature(der_sig)
        raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        sig_b64 = base64.b64encode(raw_sig).decode()

        from app.models.schemas.biometric import VerifyBiometricRequest
        req = VerifyBiometricRequest(
            challenge_id=str(challenge.id),
            signature=sig_b64,
            device_id="dev1",
        )
        result = await svc.verify_biometric(req)
        assert result.verified is True
        assert result.voter_id == str(voter_id)

    async def test_invalid_signature_fails_verification(self, mock_session):
        svc = _make_service(mock_session)
        voter_id = uuid.uuid4()
        _, pub_pem = _generate_p256_keypair()

        challenge_bytes = os.urandom(32)
        challenge = _make_challenge(voter_id, challenge_bytes.hex())
        svc.challenge_repo.get_by_id = AsyncMock(return_value=challenge)

        credential = _make_credential(pub_pem, voter_id)
        svc.credentials_repo.get_active_by_voter_and_device = AsyncMock(return_value=None)
        svc.credentials_repo.get_active_by_voter = AsyncMock(return_value=credential)

        # Random invalid signature
        fake_sig = base64.b64encode(os.urandom(64)).decode()

        from app.models.schemas.biometric import VerifyBiometricRequest
        req = VerifyBiometricRequest(
            challenge_id=str(challenge.id),
            signature=fake_sig,
        )
        result = await svc.verify_biometric(req)
        assert result.verified is False

    async def test_no_active_credential_fails_verification(self, mock_session):
        svc = _make_service(mock_session)
        voter_id = uuid.uuid4()

        challenge = _make_challenge(voter_id, os.urandom(32).hex())
        svc.challenge_repo.get_by_id = AsyncMock(return_value=challenge)
        svc.credentials_repo.get_active_by_voter_and_device = AsyncMock(return_value=None)
        svc.credentials_repo.get_active_by_voter = AsyncMock(return_value=None)

        from app.models.schemas.biometric import VerifyBiometricRequest
        req = VerifyBiometricRequest(
            challenge_id=str(challenge.id),
            signature=base64.b64encode(os.urandom(64)).decode(),
        )
        result = await svc.verify_biometric(req)
        assert result.verified is False
        assert "no active device credential" in result.message.lower()
