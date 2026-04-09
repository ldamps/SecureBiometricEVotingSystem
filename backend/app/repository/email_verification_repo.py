"""Repository layer for email verification codes."""

from __future__ import annotations

import structlog
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sqlalchemy.email_verification import EmailVerificationCode

logger = structlog.get_logger()


class EmailVerificationRepository:
    """CRUD operations for EmailVerificationCode rows."""

    async def create(
        self, session: AsyncSession, record: EmailVerificationCode
    ) -> EmailVerificationCode:
        session.add(record)
        await session.flush()
        logger.info(
            "Email verification code created",
            code_id=record.id,
            voter_id=record.voter_id,
        )
        return record

    async def get_latest_unused(
        self,
        session: AsyncSession,
        voter_id: UUID,
    ) -> EmailVerificationCode | None:
        """Return the most recent unused, non-expired code for a voter."""
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(EmailVerificationCode)
            .where(
                EmailVerificationCode.voter_id == voter_id,
                EmailVerificationCode.is_used.is_(False),
                EmailVerificationCode.expires_at > now,
            )
            .order_by(EmailVerificationCode.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_used(
        self, session: AsyncSession, code_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc)
        await session.execute(
            update(EmailVerificationCode)
            .where(EmailVerificationCode.id == code_id)
            .values(is_used=True, used_at=now)
        )

    async def invalidate_all_for_voter(
        self, session: AsyncSession, voter_id: UUID
    ) -> None:
        """Mark all existing codes for a voter as used (prevents reuse after new code sent)."""
        await session.execute(
            update(EmailVerificationCode)
            .where(
                EmailVerificationCode.voter_id == voter_id,
                EmailVerificationCode.is_used.is_(False),
            )
            .values(is_used=True)
        )
