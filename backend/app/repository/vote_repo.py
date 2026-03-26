# vote_repo.py - Repository layer for vote-related operations.

from typing import Type
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import NotFoundError
from app.models.sqlalchemy.vote import Vote

logger = structlog.get_logger()


class VoteRepository:
    """Repository layer for vote-related operations."""

    def __init__(self, model: Type[Vote] = Vote) -> None:
        self._model = model

    async def create_vote(self, session: AsyncSession, vote: Vote) -> Vote:
        """Persist a new vote."""
        try:
            session.add(vote)
            await session.flush()

            logger.info("Vote created successfully", vote_id=vote.id)
            return vote

        except Exception:
            logger.exception("Failed to create vote")
            raise

    async def get_vote_by_blind_token_hash(
        self,
        session: AsyncSession,
        blind_token_hash: str,
    ) -> Vote | None:
        """Get a vote by its blind token hash (check for duplicate votes)."""
        result = await session.execute(
            select(self._model).where(self._model.blind_token_hash == blind_token_hash)
        )
        return result.scalar_one_or_none()
