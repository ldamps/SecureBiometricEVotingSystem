"""Unit tests for EncryptionService — encrypt/decrypt round-trips and search tokens."""

import os

import pytest

from app.models.base.sqlalchemy_base import EncryptedDBField
from app.service.encryption_service import EncryptionService


@pytest.fixture
def svc():
    return EncryptionService()


@pytest.fixture
def dek():
    """A random 256-bit AES key."""
    return os.urandom(32)


@pytest.fixture
def search_dek():
    """A random HMAC key for blind indexes."""
    return os.urandom(32)


# ---------------------------------------------------------------------------
# Field encryption / decryption round-trip
# ---------------------------------------------------------------------------

class TestFieldEncryption:
    def test_encrypt_then_decrypt_recovers_plaintext(self, svc, dek):
        plaintext = "John Smith"
        encrypted = svc.encrypt_field(plaintext, dek, dek_version=1)
        decrypted = svc.decrypt_field(encrypted, dek)
        assert decrypted == plaintext

    def test_encrypt_returns_encrypted_db_field(self, svc, dek):
        encrypted = svc.encrypt_field("test", dek, dek_version=1)
        assert isinstance(encrypted, EncryptedDBField)
        assert encrypted.ciphertext
        assert encrypted.nonce
        assert encrypted.tag
        assert encrypted.dek_version == 1

    def test_ciphertext_differs_from_plaintext(self, svc, dek):
        plaintext = "Sensitive PII Data"
        encrypted = svc.encrypt_field(plaintext, dek, dek_version=1)
        assert encrypted.ciphertext != plaintext
        assert plaintext not in encrypted.ciphertext

    def test_two_encryptions_of_same_plaintext_produce_different_ciphertext(self, svc, dek):
        plaintext = "Same input"
        enc1 = svc.encrypt_field(plaintext, dek, dek_version=1)
        enc2 = svc.encrypt_field(plaintext, dek, dek_version=1)
        # Different random nonces => different ciphertext
        assert enc1.ciphertext != enc2.ciphertext
        assert enc1.nonce != enc2.nonce

    def test_decrypt_with_wrong_key_fails(self, svc, dek):
        encrypted = svc.encrypt_field("secret", dek, dek_version=1)
        wrong_key = os.urandom(32)
        with pytest.raises(Exception):
            svc.decrypt_field(encrypted, wrong_key)

    def test_tampered_ciphertext_fails_authentication(self, svc, dek):
        encrypted = svc.encrypt_field("secret", dek, dek_version=1)
        # Flip a byte in the ciphertext
        ct_bytes = bytes.fromhex(encrypted.ciphertext)
        tampered = bytes([ct_bytes[0] ^ 0xFF]) + ct_bytes[1:]
        encrypted.ciphertext = tampered.hex()
        with pytest.raises(Exception):
            svc.decrypt_field(encrypted, dek)

    def test_tampered_tag_fails_authentication(self, svc, dek):
        encrypted = svc.encrypt_field("secret", dek, dek_version=1)
        tag_bytes = bytes.fromhex(encrypted.tag)
        tampered = bytes([tag_bytes[0] ^ 0xFF]) + tag_bytes[1:]
        encrypted.tag = tampered.hex()
        with pytest.raises(Exception):
            svc.decrypt_field(encrypted, dek)

    def test_encrypts_unicode_correctly(self, svc, dek):
        plaintext = "名前は太郎です"
        encrypted = svc.encrypt_field(plaintext, dek, dek_version=1)
        assert svc.decrypt_field(encrypted, dek) == plaintext

    def test_encrypts_empty_string(self, svc, dek):
        encrypted = svc.encrypt_field("", dek, dek_version=1)
        assert svc.decrypt_field(encrypted, dek) == ""


# ---------------------------------------------------------------------------
# Search tokens (HMAC blind index)
# ---------------------------------------------------------------------------

class TestSearchTokens:
    def test_search_token_included_when_search_dek_provided(self, svc, dek, search_dek):
        encrypted = svc.encrypt_field("John", dek, dek_version=1, search_dek=search_dek)
        assert encrypted.search_token is not None

    def test_no_search_token_without_search_dek(self, svc, dek):
        encrypted = svc.encrypt_field("John", dek, dek_version=1)
        assert encrypted.search_token is None

    def test_search_token_is_deterministic(self, svc, dek, search_dek):
        enc1 = svc.encrypt_field("John", dek, dek_version=1, search_dek=search_dek)
        enc2 = svc.encrypt_field("John", dek, dek_version=1, search_dek=search_dek)
        assert enc1.search_token == enc2.search_token

    def test_search_token_case_insensitive(self, svc, dek, search_dek):
        enc_upper = svc.encrypt_field("JOHN", dek, dek_version=1, search_dek=search_dek)
        enc_lower = svc.encrypt_field("john", dek, dek_version=1, search_dek=search_dek)
        assert enc_upper.search_token == enc_lower.search_token

    def test_different_values_produce_different_search_tokens(self, svc, dek, search_dek):
        enc1 = svc.encrypt_field("Alice", dek, dek_version=1, search_dek=search_dek)
        enc2 = svc.encrypt_field("Bob", dek, dek_version=1, search_dek=search_dek)
        assert enc1.search_token != enc2.search_token

    def test_create_search_token_matches_field_search_token(self, svc, dek, search_dek):
        encrypted = svc.encrypt_field("John", dek, dek_version=1, search_dek=search_dek)
        standalone_token = svc.create_search_token("John", search_dek)
        assert encrypted.search_token == standalone_token

    def test_create_search_token_case_insensitive(self, svc, search_dek):
        token1 = svc.create_search_token("POSTCODE", search_dek)
        token2 = svc.create_search_token("postcode", search_dek)
        assert token1 == token2


# ---------------------------------------------------------------------------
# Stream encryption / decryption
# ---------------------------------------------------------------------------

class TestStreamEncryption:
    def test_stream_encrypt_decrypt_round_trip(self, svc, dek):
        data = b"Binary payload for storage"
        encrypted = svc.encrypt_stream(data, dek, dek_version=1)
        decrypted = svc.decrypt_stream(encrypted, dek)
        assert decrypted == data

    def test_stream_encrypt_produces_different_output_each_time(self, svc, dek):
        data = b"Same payload"
        enc1 = svc.encrypt_stream(data, dek, dek_version=1)
        enc2 = svc.encrypt_stream(data, dek, dek_version=1)
        assert enc1 != enc2

    def test_stream_decrypt_with_wrong_key_fails(self, svc, dek):
        encrypted = svc.encrypt_stream(b"secret blob", dek, dek_version=1)
        with pytest.raises(Exception):
            svc.decrypt_stream(encrypted, os.urandom(32))
