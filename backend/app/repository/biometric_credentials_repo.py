"""Repository layer for biometric device credentials (match-on-device)."""

from __future__ import annotations

import structlog
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import NotFoundError
from app.models.sqlalchemy.biometric_credentials import DeviceCredential

logger = structlog.get_logger()


class BiometricCredentialsRepository:
    """CRUD operations for DeviceCredential rows."""

    async def create(
        self, session: AsyncSession, credential: DeviceCredential
    ) -> DeviceCredential:
        session.add(credential)
        await session.flush()
        logger.info(
            "Device credential created",
            credential_id=credential.id,
            voter_id=credential.voter_id,
        )
        return credential

    async def get_by_id(
        self, session: AsyncSession, credential_id: UUID
    ) -> DeviceCredential:
        result = await session.execute(
            select(DeviceCredential).where(DeviceCredential.id == credential_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise NotFoundError("Device credential not found")
        return row

    async def get_active_by_voter_and_device(
        self,
        session: AsyncSession,
        voter_id: UUID,
        device_id: str,
    ) -> Optional[DeviceCredential]:
        result = await session.execute(
            select(DeviceCredential).where(
                DeviceCredential.voter_id == voter_id,
                DeviceCredential.device_id == device_id,
                DeviceCredential.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_voter(
        self, session: AsyncSession, voter_id: UUID
    ) -> Optional[DeviceCredential]:
        result = await session.execute(
            select(DeviceCredential)
            .where(
                DeviceCredential.voter_id == voter_id,
                DeviceCredential.is_active.is_(True),
            )
            .order_by(DeviceCredential.created_at.desc())
        )
        return result.scalars().first()

    async def list_active_by_voter(
        self, session: AsyncSession, voter_id: UUID
    ) -> list[DeviceCredential]:
        result = await session.execute(
            select(DeviceCredential).where(
                DeviceCredential.voter_id == voter_id,
                DeviceCredential.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def list_by_voter(
        self, session: AsyncSession, voter_id: UUID
    ) -> list[DeviceCredential]:
        result = await session.execute(
            select(DeviceCredential)
            .where(DeviceCredential.voter_id == voter_id)
            .order_by(DeviceCredential.created_at.desc())
        )
        return list(result.scalars().all())

    async def deactivate(
        self, session: AsyncSession, credential_id: UUID
    ) -> None:
        stmt = (
            update(DeviceCredential)
            .where(DeviceCredential.id == credential_id)
            .values(is_active=False)
        )
        result = await session.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError("Device credential not found")

    async def touch_last_used(
        self, session: AsyncSession, credential_id: UUID
    ) -> None:
        stmt = (
            update(DeviceCredential)
            .where(DeviceCredential.id == credential_id)
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await session.execute(stmt)
