import hmac
import hashlib

import structlog
from cryptography.fernet import Fernet

from .base import BaseEncryption, EncryptedField

logger = structlog.get_logger()


class LocalEncryption(BaseEncryption):
    """Fernet-based encryption for local development and testing."""

    def __init__(self, encryption_key: str, hmac_secret: str):
        key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        self._fernet = Fernet(key)
        self._hmac_secret = hmac_secret.encode() if isinstance(hmac_secret, str) else hmac_secret

    def encrypt(self, plaintext: str) -> EncryptedField:
        ciphertext = self._fernet.encrypt(plaintext.encode())
        search_token = self.generate_search_token(plaintext)
        return EncryptedField(ciphertext=ciphertext, search_token=search_token)

    def decrypt(self, encrypted: EncryptedField) -> str:
        return self._fernet.decrypt(encrypted.ciphertext).decode()

    def generate_search_token(self, value: str) -> bytes:
        return hmac.new(self._hmac_secret, value.lower().encode(), hashlib.sha256).digest()
