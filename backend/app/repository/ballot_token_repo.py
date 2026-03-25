# ballot_token_repo.py - Repository layer for ballot token operations.

from typing import Type
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sqlalchemy.ballot_token import BallotToken

logger = structlog.get_logger()


class BallotTokenRepository:
    """Repository layer for ballot-token-related operations."""

    def __init__(self, model: Type[BallotToken] = BallotToken) -> None:
        self._model = model

    async def get_by_blind_token_hash(
        self,
        session: AsyncSession,
        blind_token_hash: UUID,
    ) -> BallotToken | None:
        """Retrieve a ballot token by its blind_token_hash."""
        result = await session.execute(
            select(self._model).where(self._model.blind_token_hash == blind_token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_as_used(
        self,
        session: AsyncSession,
        ballot_token_id: UUID,
        used_at,
    ) -> BallotToken:
        """Mark a ballot token as used."""
        stmt = (
            update(self._model)
            .where(self._model.id == ballot_token_id)
            .values(is_used=True, used_at=used_at)
            .returning(self._model)
        )
        result = await session.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            raise ValueError("Ballot token not found")

        logger.info("Ballot token marked as used", ballot_token_id=ballot_token_id)
        return token
