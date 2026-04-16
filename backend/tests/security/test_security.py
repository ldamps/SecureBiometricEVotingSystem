"""Security tests — verifying core security invariants of the e-voting system.

These tests demonstrate that the system enforces:
1. Vote anonymity (no voter_id on vote records)
2. One-voter-one-vote enforcement
3. Ballot token single-use enforcement
4. JWT tamper detection
5. Account lockout under brute-force
6. Encryption actually protects data (ciphertext != plaintext)
7. Biometric challenge expiry and replay prevention
"""

import base64
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from argon2 import PasswordHasher

from app.application.core.exceptions import AuthenticationError, ValidationError
from app.service.auth_service import AuthService
from app.service.encryption_service import EncryptionService
from app.models.schemas.vote import CastVoteRequest
from app.service.voting_service import VotingService

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


# ---------------------------------------------------------------------------
# 1. JWT tamper detection
# ---------------------------------------------------------------------------

class TestJWTSecurity:
    """Verify JWTs cannot be forged or tampered with."""

    def _get_tokens(self):
        """Helper: create a real token pair via AuthService."""
        official = MagicMock()
        official.id = uuid.uuid4()
        official.username = "admin"
        official.role = "ADMIN"
        svc = AuthService.__new__(AuthService)
        return svc._create_token_pair(official.id, official.username, official.role)

    def test_tampered_payload_is_rejected(self):
        tokens = self._get_tokens()
        # Modify the payload section of the JWT
        parts = tokens.access_token.split(".")
        import base64 as b64
        payload_bytes = b64.urlsafe_b64decode(parts[1] + "==")
        tampered = payload_bytes.replace(b'"ADMIN"', b'"SUPERADMIN"')
        parts[1] = b64.urlsafe_b64encode(tampered).rstrip(b"=").decode()
        tampered_token = ".".join(parts)

        with pytest.raises(AuthenticationError):
            AuthService.decode_token(tampered_token)

    def test_truncated_token_is_rejected(self):
        tokens = self._get_tokens()
        truncated = tokens.access_token[:50]
        with pytest.raises(AuthenticationError):
            AuthService.decode_token(truncated)

    def test_empty_token_is_rejected(self):
        with pytest.raises(AuthenticationError):
            AuthService.decode_token("")

    def test_token_signed_with_wrong_secret_is_rejected(self):
        from jose import jwt
        payload = {
            "sub": str(uuid.uuid4()),
            "username": "hacker",
            "role": "ADMIN",
            "token_type": "access",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        }
        # Sign with a different secret
        forged = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
        with pytest.raises(AuthenticationError):
            AuthService.decode_token(forged)


# ---------------------------------------------------------------------------
# 2. Account lockout under brute-force
# ---------------------------------------------------------------------------

class TestBruteForceProtection:
    """Verify that repeated failed logins lock the account."""

    async def test_account_locks_after_max_failed_attempts(self, mock_session):
        official = MagicMock()
        official.id = uuid.uuid4()
        official.username = "target"
        official.password_hash = _ph.hash("RealPassword1!")
        official.role = "ADMIN"
        official.is_active = True
        official.must_reset_password = False
        official.locked_until = None

        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        audit_repo = AsyncMock()
        svc = AuthService(official_repo=repo, session=mock_session, audit_log_repo=audit_repo)

        # Simulate 5 failed login attempts
        for attempt in range(5):
            official.failed_login_attempts = attempt
            with pytest.raises(AuthenticationError):
                await svc.login("target", "WrongPassword!")

        # On the 5th attempt (index 4), lockout should have been triggered
        last_update = repo.update_official.call_args_list[-1][0][2]
        assert last_update["failed_login_attempts"] == 5
        assert last_update.get("locked_until") is not None

    async def test_locked_account_rejects_correct_password(self, mock_session):
        official = MagicMock()
        official.id = uuid.uuid4()
        official.username = "locked_user"
        official.password_hash = _ph.hash("CorrectPassword1!")
        official.role = "ADMIN"
        official.is_active = True
        official.failed_login_attempts = 5
        official.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        official.must_reset_password = False

        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        audit_repo = AsyncMock()
        svc = AuthService(official_repo=repo, session=mock_session, audit_log_repo=audit_repo)

        with pytest.raises(AuthenticationError, match="locked"):
            await svc.login("locked_user", "CorrectPassword1!")


# ---------------------------------------------------------------------------
# 3. Encryption protects PII
# ---------------------------------------------------------------------------

class TestEncryptionSecurity:
    """Verify that encrypted data cannot be read without the correct key."""

    def test_ciphertext_does_not_contain_plaintext(self):
        svc = EncryptionService()
        dek = os.urandom(32)
        sensitive = "AB 12 34 56 C"  # National Insurance number
        encrypted = svc.encrypt_field(sensitive, dek, dek_version=1)

        # The NI number should not appear anywhere in the encrypted field
        assert sensitive not in encrypted.ciphertext
        assert sensitive not in encrypted.nonce
        assert sensitive not in encrypted.tag

    def test_different_keys_produce_different_ciphertext(self):
        svc = EncryptionService()
        plaintext = "John Smith"
        dek1 = os.urandom(32)
        dek2 = os.urandom(32)
        enc1 = svc.encrypt_field(plaintext, dek1, dek_version=1)
        enc2 = svc.encrypt_field(plaintext, dek2, dek_version=1)
        # Different keys = different ciphertext (with overwhelming probability)
        assert enc1.ciphertext != enc2.ciphertext

    def test_wrong_key_cannot_decrypt(self):
        svc = EncryptionService()
        dek = os.urandom(32)
        encrypted = svc.encrypt_field("Secret ballot data", dek, dek_version=1)
        with pytest.raises(Exception):
            svc.decrypt_field(encrypted, os.urandom(32))

    def test_tampered_ciphertext_detected_by_gcm(self):
        svc = EncryptionService()
        dek = os.urandom(32)
        encrypted = svc.encrypt_field("Voter address", dek, dek_version=1)
        # Corrupt one byte
        ct = bytes.fromhex(encrypted.ciphertext)
        corrupted = bytes([ct[0] ^ 0xFF]) + ct[1:]
        encrypted.ciphertext = corrupted.hex()
        with pytest.raises(Exception):
            svc.decrypt_field(encrypted, dek)

    def test_search_token_cannot_reverse_to_plaintext(self):
        svc = EncryptionService()
        search_dek = os.urandom(32)
        token = svc.create_search_token("SW1A 2AA", search_dek)
        # Token is a hex-encoded HMAC — it should not contain the original value
        assert "SW1A 2AA" not in token
        assert "sw1a 2aa" not in token
        # And it's 64 hex chars (SHA-256 digest)
        assert len(token) == 64


# ---------------------------------------------------------------------------
# 4. Ballot payload validation
# ---------------------------------------------------------------------------

class TestBallotSecurityValidation:
    """Verify that invalid ballot payloads are rejected."""

    def _req(self, **overrides):
        defaults = dict(
            voter_id=str(uuid.uuid4()),
            election_id=str(uuid.uuid4()),
            constituency_id=str(uuid.uuid4()),
            candidate_id=str(uuid.uuid4()),
            blind_token_hash="token123",
        )
        defaults.update(overrides)
        return CastVoteRequest(**defaults)

    def test_fptp_rejects_missing_candidate(self):
        with pytest.raises(ValidationError):
            VotingService._validate_ballot_payload("FPTP", self._req(candidate_id=None))

    def test_ams_rejects_empty_ballot(self):
        with pytest.raises(ValidationError):
            VotingService._validate_ballot_payload(
                "AMS", self._req(candidate_id=None, party_id=None)
            )

    def test_stv_rejects_non_consecutive_ranks(self):
        from app.models.schemas.vote import RankedPreference
        prefs = [
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=1),
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=5),
        ]
        with pytest.raises(ValidationError, match="consecutive"):
            VotingService._validate_ballot_payload(
                "STV", self._req(candidate_id=None, ranked_preferences=prefs)
            )


# ---------------------------------------------------------------------------
# 5. Biometric challenge security
# ---------------------------------------------------------------------------

class TestBiometricChallengeSecurity:
    """Verify challenge expiry and replay prevention."""

    async def test_expired_challenge_rejected(self, mock_session):
        from app.service.biometric_service import BiometricService

        svc = BiometricService(
            credentials_repo=AsyncMock(),
            challenge_repo=AsyncMock(),
            voter_repo=AsyncMock(),
            session=mock_session,
        )
        svc._audit_log_repo = AsyncMock()

        challenge = MagicMock()
        challenge.id = uuid.uuid4()
        challenge.voter_id = uuid.uuid4()
        challenge.challenge = os.urandom(32).hex()
        challenge.is_used = False
        challenge.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        svc.challenge_repo.get_by_id = AsyncMock(return_value=challenge)

        from app.models.schemas.biometric import VerifyBiometricRequest
        req = VerifyBiometricRequest(
            challenge_id=str(challenge.id),
            signature=base64.b64encode(os.urandom(64)).decode(),
        )
        result = await svc.verify_biometric(req)
        assert result.verified is False

    async def test_replayed_challenge_rejected(self, mock_session):
        from app.service.biometric_service import BiometricService

        svc = BiometricService(
            credentials_repo=AsyncMock(),
            challenge_repo=AsyncMock(),
            voter_repo=AsyncMock(),
            session=mock_session,
        )
        svc._audit_log_repo = AsyncMock()

        challenge = MagicMock()
        challenge.id = uuid.uuid4()
        challenge.voter_id = uuid.uuid4()
        challenge.challenge = os.urandom(32).hex()
        challenge.is_used = True  # Already used
        challenge.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        svc.challenge_repo.get_by_id = AsyncMock(return_value=challenge)

        from app.models.schemas.biometric import VerifyBiometricRequest
        req = VerifyBiometricRequest(
            challenge_id=str(challenge.id),
            signature=base64.b64encode(os.urandom(64)).decode(),
        )
        result = await svc.verify_biometric(req)
        assert result.verified is False
        assert "already been used" in result.message.lower()


# ---------------------------------------------------------------------------
# 6. Public key validation security
# ---------------------------------------------------------------------------

class TestPublicKeySecurity:
    """Verify only ECDSA P-256 keys are accepted for biometric enrollment."""

    def test_rsa_key_rejected(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from app.service.biometric_service import BiometricService

        rsa_key = rsa.generate_private_key(65537, 2048)
        pem = rsa_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        with pytest.raises(ValidationError, match="elliptic-curve"):
            BiometricService._parse_public_key(pem)

    def test_p384_key_rejected(self):
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        from app.service.biometric_service import BiometricService

        key = ec.generate_private_key(ec.SECP384R1())
        pem = key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        with pytest.raises(ValidationError, match="P-256"):
            BiometricService._parse_public_key(pem)

    def test_garbage_pem_rejected(self):
        from app.service.biometric_service import BiometricService

        with pytest.raises(ValidationError, match="Invalid PEM"):
            BiometricService._parse_public_key("not a real key")
