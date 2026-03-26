from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dto.encryption_key import CreateEncryptionKeyDTO, EncryptionKeyDTO
from app.models.sqlalchemy.encryption_key import EncryptionKey


class KeysManagerRepository:
    """Persistence layer for encrypted DEK records."""

    async def create(
        self, session: AsyncSession, dto: CreateEncryptionKeyDTO
    ) -> EncryptionKeyDTO:
        key = EncryptionKey(
            org_id=dto.org_id,
            purpose=dto.purpose,
            version=dto.version,
            encrypted_dek=dto.encrypted_dek,
            kms_key_id=dto.kms_key_id,
            kms_key_region=dto.kms_key_region,
            is_active=True,
        )
        session.add(key)
        await session.flush()
        return self._to_dto(key)

    async def get_active(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID],
        purpose: str,
    ) -> Optional[EncryptionKeyDTO]:
        """Return the active (highest-version) DEK for the given org and purpose."""
        stmt = (
            select(EncryptionKey)
            .where(
                EncryptionKey.org_id == org_id,
                EncryptionKey.purpose == purpose,
                EncryptionKey.is_active.is_(True),
            )
            .order_by(EncryptionKey.version.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        key = result.scalar_one_or_none()
        return self._to_dto(key) if key else None

    async def get_by_version(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID],
        purpose: str,
        version: int,
    ) -> Optional[EncryptionKeyDTO]:
        """Return a specific DEK version (needed for decrypting older records)."""
        stmt = select(EncryptionKey).where(
            EncryptionKey.org_id == org_id,
            EncryptionKey.purpose == purpose,
            EncryptionKey.version == version,
        )
        result = await session.execute(stmt)
        key = result.scalar_one_or_none()
        return self._to_dto(key) if key else None

    async def deactivate_all(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID],
        purpose: str,
    ) -> None:
        """Mark all DEKs for an org+purpose as inactive (used before inserting a new rotation)."""
        stmt = (
            update(EncryptionKey)
            .where(
                EncryptionKey.org_id == org_id,
                EncryptionKey.purpose == purpose,
            )
            .values(is_active=False)
        )
        await session.execute(stmt)

    async def next_version(
        self,
        session: AsyncSession,
        org_id: Optional[uuid.UUID],
        purpose: str,
    ) -> int:
        """Return max(version)+1 for the given org+purpose, or 1 if none exist."""
        stmt = select(func.max(EncryptionKey.version)).where(
            EncryptionKey.org_id == org_id,
            EncryptionKey.purpose == purpose,
        )
        result = await session.execute(stmt)
        current_max = result.scalar_one_or_none()
        return (current_max or 0) + 1

    @staticmethod
    def _to_dto(key: EncryptionKey) -> EncryptionKeyDTO:
        return EncryptionKeyDTO(
            id=key.id,
            org_id=key.org_id,
            purpose=key.purpose,
            version=key.version,
            encrypted_dek=key.encrypted_dek,
            kms_key_id=key.kms_key_id,
            kms_key_region=key.kms_key_region,
            is_active=key.is_active,
        )
