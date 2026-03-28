"""Repository layer for biometric verification challenges."""

from __future__ import annotations

import structlog
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import NotFoundError
from app.models.sqlalchemy.biometric_credentials import BiometricChallenge

logger = structlog.get_logger()


class BiometricChallengeRepository:
    """CRUD operations for BiometricChallenge rows."""

    async def create(
        self, session: AsyncSession, challenge: BiometricChallenge
    ) -> BiometricChallenge:
        session.add(challenge)
        await session.flush()
        logger.info(
            "Biometric challenge created",
            challenge_id=challenge.id,
            voter_id=challenge.voter_id,
        )
        return challenge

    async def get_by_id(
        self, session: AsyncSession, challenge_id: UUID
    ) -> BiometricChallenge:
        result = await session.execute(
            select(BiometricChallenge).where(BiometricChallenge.id == challenge_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise NotFoundError("Biometric challenge not found")
        return row

    async def mark_used(
        self, session: AsyncSession, challenge_id: UUID
    ) -> None:
        stmt = (
            update(BiometricChallenge)
            .where(BiometricChallenge.id == challenge_id)
            .values(is_used=True, used_at=datetime.now(timezone.utc))
        )
        await session.execute(stmt)
