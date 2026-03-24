from enum import Enum
from typing import Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

class EncryptionPurpose(Enum):
    """Encryption purpose."""
    DATABASE = "DATABASE"
    STORAGE = "STORAGE"
    SEARCH = "SEARCH"


@dataclass
class EncryptedField:
    """Encrypted field."""
    ciphertext: bytes
    search_token: Optional[bytes] = None


class BaseEncryption(ABC):
    """Abstract base class for encryption implementations."""

    @abstractmethod
    def encrypt(self, plaintext: str) -> EncryptedField:
        """Encrypt plaintext and return an EncryptedField."""
        ...

    @abstractmethod
    def decrypt(self, encrypted: EncryptedField) -> str:
        """Decrypt an EncryptedField and return plaintext."""
        ...

    @abstractmethod
    def generate_search_token(self, value: str) -> bytes:
        """Generate a deterministic HMAC search token for the given value."""
        ...
