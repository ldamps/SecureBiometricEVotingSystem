from __future__ import annotations

import hashlib
import hmac
import json
import os
import struct
from dataclasses import dataclass
from typing import Optional

import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.infra.encryption.base import EncryptionPurpose
from app.models.base.sqlalchemy_base import EncryptedDBField

logger = structlog.get_logger()


@dataclass
class EncryptionArgs:
    """Resolved encryption context passed to encrypt/decrypt helpers.

    encrypted_deks maps each EncryptionPurpose to the KMS-encrypted DEK bytes
    (as stored in the encryption_key table).  The plain DEK is resolved lazily
    by EncryptionService.get_dek() via the BaseEncryption (KMS) layer.
    """

    org_id: Optional[object]          # UUID | None — None for system-scoped keys
    encrypted_deks: dict[str, bytes]  # purpose.value -> encrypted DEK bytes
    kms_key_id: str
    kms_key_region: str
    current_dek_version: int


class EncryptionService:
    """AES-256-GCM field and stream encryption using caller-supplied DEKs.

    This service is pure crypto: it takes pre-resolved plaintext DEKs and
    applies AES-256-GCM.  Key resolution (DEK store → KMS decrypt → plain DEK)
    is handled by KeysManagerService.
    """

    # ------------------------------------------------------------------ #
    #  Field encryption / decryption                                       #
    # ------------------------------------------------------------------ #

    def encrypt_field(
        self,
        plaintext: str,
        dek: bytes,
        dek_version: int,
        search_dek: Optional[bytes] = None,
    ) -> EncryptedDBField:
        """AES-256-GCM encrypt a string field.

        If *search_dek* is provided an HMAC-SHA256 blind index is computed and
        stored on the returned EncryptedDBField so the field can be queried
        without decryption.
        """
        nonce = os.urandom(12)
        aesgcm = AESGCM(dek)
        combined = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        ciphertext, tag = combined[:-16], combined[-16:]

        search_token: Optional[str] = None
        if search_dek is not None:
            search_token = hmac.new(
                search_dek, plaintext.lower().encode("utf-8"), hashlib.sha256
            ).hexdigest()

        return EncryptedDBField(
            ciphertext=ciphertext.hex(),
            nonce=nonce.hex(),
            tag=tag.hex(),
            dek_version=dek_version,
            search_token=search_token,
        )

    def decrypt_field(self, field: EncryptedDBField, dek: bytes) -> str:
        """Decrypt a single EncryptedDBField, returning the original string."""
        combined = bytes.fromhex(field.ciphertext) + bytes.fromhex(field.tag)
        nonce = bytes.fromhex(field.nonce)
        aesgcm = AESGCM(dek)
        return aesgcm.decrypt(nonce, combined, None).decode("utf-8")

    def create_search_token(self, value: str, search_dek: bytes) -> str:
        """HMAC-SHA256 blind index for querying searchable encrypted fields.

        Lowercase-normalised so case-insensitive lookups work transparently.
        Returns a hex digest.
        """
        return hmac.new(
            search_dek, value.lower().encode("utf-8"), hashlib.sha256
        ).hexdigest()

    # ------------------------------------------------------------------ #
    #  Stream encryption / decryption  (storage / blob use-case)          #
    # ------------------------------------------------------------------ #

    def encrypt_stream(self, data: bytes, dek: bytes, dek_version: int) -> bytes:
        """Encrypt a binary blob in one shot with AES-256-GCM.

        Output wire format:
          [4-byte big-endian header length]
          [UTF-8 JSON header: {"nonce": hex, "tag": hex, "dek_version": int}]
          [raw ciphertext bytes]
        """
        nonce = os.urandom(12)
        aesgcm = AESGCM(dek)
        combined = aesgcm.encrypt(nonce, data, None)
        ciphertext, tag = combined[:-16], combined[-16:]

        header = json.dumps(
            {"nonce": nonce.hex(), "tag": tag.hex(), "dek_version": dek_version}
        ).encode("utf-8")
        return struct.pack(">I", len(header)) + header + ciphertext

    def decrypt_stream(self, data: bytes, dek: bytes) -> bytes:
        """Decrypt output produced by encrypt_stream."""
        (header_len,) = struct.unpack(">I", data[:4])
        header = json.loads(data[4 : 4 + header_len])
        ciphertext = data[4 + header_len :]

        nonce = bytes.fromhex(header["nonce"])
        tag = bytes.fromhex(header["tag"])
        aesgcm = AESGCM(dek)
        return aesgcm.decrypt(nonce, ciphertext + tag, None)
