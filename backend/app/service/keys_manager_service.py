from __future__ import annotations

import os
import uuid
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.encryption.base import BaseEncryption, EncryptedField, EncryptionPurpose
from app.models.dto.encryption_key import CreateEncryptionKeyDTO, EncryptionKeyDTO
from app.repository.keys_manager_repo import KeysManagerRepository
from app.service.encryption_service import EncryptionArgs

logger = structlog.get_logger()

# Every org must have a DEK for each of these purposes before data can be written.
_ALL_PURPOSES = [
    EncryptionPurpose.DATABASE,
    EncryptionPurpose.SEARCH,
    EncryptionPurpose.STORAGE,
]


class KeysManagerService:
    """Manages the full DEK lifecycle: creation, retrieval, and rotation.

    Key hierarchy
    -------------
    KMS Key (KEK)  ──wraps──▶  DEK (stored encrypted in DB)  ──encrypts──▶  field data

    The plain DEK is never written to disk or the database.  Only the
    KMS-wrapped form lives in the encryption_key table.  Plain DEKs are
    decrypted on demand and cached in memory for the lifetime of the service.

    Rotation
    --------
    Rotating a DEK generates a new 256-bit key and deactivates the previous
    row (is_active=False).  Existing records are NOT re-encrypted — they store
    their dek_version so the correct (older) DEK can be fetched for decryption.
    New writes always use the current active DEK.  This limits the blast radius
    of a compromised key to only the data encrypted under that specific version.
    """

    def __init__(
        self,
        encryption: BaseEncryption,
        keys_repo: KeysManagerRepository,
        kms_key_id: str,
        kms_key_region: str,
    ) -> None:
        self._encryption = encryption
        self._keys_repo = keys_repo
        self._kms_key_id = kms_key_id
        self._kms_key_region = kms_key_region
        # (str(org_id), purpose.value, version) -> plain DEK bytes
        self._dek_cache: dict[tuple, bytes] = {}

    # ------------------------------------------------------------------ #
    #  Initialisation                                                      #
    # ------------------------------------------------------------------ #

    async def init_org_keys(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID] = None,
    ) -> dict[str, EncryptionKeyDTO]:
        """Ensure a DEK exists for every purpose for the given org (or system if None).

        Idempotent: if an active DEK already exists for a purpose it is left
        untouched.  Returns a mapping of purpose.value -> EncryptionKeyDTO.
        """
        result: dict[str, EncryptionKeyDTO] = {}
        for purpose in _ALL_PURPOSES:
            existing = await self._keys_repo.get_active(session, org_id, purpose.value)
            if existing:
                result[purpose.value] = existing
                logger.debug("DEK already exists", org_id=org_id, purpose=purpose.value)
            else:
                dto = await self._create_dek(session, org_id, purpose)
                result[purpose.value] = dto
                logger.info("Created DEK", org_id=org_id, purpose=purpose.value, version=dto.version)
        return result

    # ------------------------------------------------------------------ #
    #  DEK resolution                                                      #
    # ------------------------------------------------------------------ #

    async def get_dek(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID],
        purpose: EncryptionPurpose,
        version: Optional[int] = None,
    ) -> tuple[bytes, int]:
        """Return (plain_dek_bytes, version) for the given org/purpose/version.

        If *version* is None the currently active (latest) DEK is returned.
        Plain DEKs are cached so KMS is only called once per unique version.
        """
        if version is None:
            key_dto = await self._keys_repo.get_active(session, org_id, purpose.value)
        else:
            key_dto = await self._keys_repo.get_by_version(session, org_id, purpose.value, version)

        if key_dto is None:
            raise KeyError(
                f"No DEK found for org={org_id} purpose={purpose.value} version={version}. "
                "Call init_org_keys() first."
            )

        cache_key = (str(org_id), purpose.value, key_dto.version)
        if cache_key not in self._dek_cache:
            # Decrypt the stored DEK using KMS — this is the only time KMS is called per version.
            encrypted_field = EncryptedField(ciphertext=key_dto.encrypted_dek)
            plain_text = self._encryption.decrypt(encrypted_field)
            self._dek_cache[cache_key] = plain_text.encode("latin-1")

        return self._dek_cache[cache_key], key_dto.version

    async def build_encryption_args(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID] = None,
    ) -> EncryptionArgs:
        """Build an EncryptionArgs snapshot for use by EncryptionMapperService.

        Loads the active encrypted DEK bytes for every purpose so downstream
        services can resolve plain DEKs lazily without further DB round-trips.
        """
        encrypted_deks: dict[str, bytes] = {}
        current_version = 1

        for purpose in _ALL_PURPOSES:
            key_dto = await self._keys_repo.get_active(session, org_id, purpose.value)
            if key_dto is None:
                raise KeyError(
                    f"No active DEK for org={org_id} purpose={purpose.value}. "
                    "Call init_org_keys() first."
                )
            encrypted_deks[purpose.value] = key_dto.encrypted_dek
            current_version = key_dto.version

        return EncryptionArgs(
            org_id=org_id,
            encrypted_deks=encrypted_deks,
            kms_key_id=self._kms_key_id,
            kms_key_region=self._kms_key_region,
            current_dek_version=current_version,
        )

    # ------------------------------------------------------------------ #
    #  Rotation                                                            #
    # ------------------------------------------------------------------ #

    async def rotate_dek(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID],
        purpose: EncryptionPurpose,
    ) -> EncryptionKeyDTO:
        """Generate a new DEK version and deactivate the previous one.

        After rotation:
        - New writes use the new (higher-version) DEK.
        - Old records still decrypt correctly because EncryptedDBField stores
          its dek_version, and get_dek() can fetch any historical version.
        """
        await self._keys_repo.deactivate_all(session, org_id, purpose.value)
        dto = await self._create_dek(session, org_id, purpose)
        logger.info("Rotated DEK", org_id=org_id, purpose=purpose.value, new_version=dto.version)
        return dto

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    async def _create_dek(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID],
        purpose: EncryptionPurpose,
    ) -> EncryptionKeyDTO:
        """Generate a raw DEK, wrap it with KMS, persist it, and warm the cache."""
        raw_dek = os.urandom(32)  # 256-bit — never written to storage in plaintext

        # Wrap the raw DEK bytes with KMS.
        # latin-1 is a safe byte-transparent encoding for the round-trip.
        encrypted_field: EncryptedField = self._encryption.encrypt(raw_dek.decode("latin-1"))

        next_ver = await self._keys_repo.next_version(session, org_id, purpose.value)
        dto = await self._keys_repo.create(
            session,
            CreateEncryptionKeyDTO(
                org_id=org_id,
                purpose=purpose.value,
                version=next_ver,
                encrypted_dek=encrypted_field.ciphertext,
                kms_key_id=self._kms_key_id,
                kms_key_region=self._kms_key_region,
            ),
        )

        # Warm the cache so the very first encrypt call after creation is free.
        self._dek_cache[(str(org_id), purpose.value, next_ver)] = raw_dek
        return dto
