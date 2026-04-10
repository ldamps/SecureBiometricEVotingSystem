"""Email verification code service.

Generates, sends, and verifies 6-digit codes as an alternative to
biometric verification when updating voter registration details.
"""

import secrets
import structlog
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sqlalchemy.email_verification import EmailVerificationCode
from app.repository.email_verification_repo import EmailVerificationRepository
from app.service.email_service import EmailService

logger = structlog.get_logger()

CODE_TTL_MINUTES = 10
CODE_LENGTH = 6


class EmailVerificationService:
    """Generate and verify email-based one-time codes."""

    def __init__(
        self,
        repo: EmailVerificationRepository,
        session: AsyncSession,
        email_service: EmailService,
    ) -> None:
        self._repo = repo
        self._session = session
        self._email_service = email_service

    async def send_code(self, voter_id: UUID, voter_email: str) -> str:
        """Generate a code, persist it, and email it to the voter.

        Returns the created code record's ID.
        """
        # Invalidate any previous unused codes for this voter.
        await self._repo.invalidate_all_for_voter(self._session, voter_id)

        code = "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=CODE_TTL_MINUTES)

        record = EmailVerificationCode(
            voter_id=voter_id,
            code=code,
            expires_at=expires_at,
        )
        await self._repo.create(self._session, record)

        # Send the code via email (non-fatal on failure: let the caller
        # decide how to handle email send errors).
        self._email_service.send_verification_code(voter_email, code)

        logger.info(
            "Verification code sent",
            voter_id=str(voter_id),
            code_id=str(record.id),
        )
        return str(record.id)

    async def verify_code(self, voter_id: UUID, code: str) -> bool:
        """Check the code against the most recent unused code for the voter."""
        record = await self._repo.get_latest_unused(self._session, voter_id)
        if record is None:
            logger.info("No valid code found", voter_id=str(voter_id))
            return False

        if record.code != code:
            logger.info("Code mismatch", voter_id=str(voter_id))
            return False

        await self._repo.mark_used(self._session, record.id)
        logger.info(
            "Verification code verified",
            voter_id=str(voter_id),
            code_id=str(record.id),
        )
        return True
