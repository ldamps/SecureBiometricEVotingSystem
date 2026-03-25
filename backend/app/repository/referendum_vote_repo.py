# referendum_vote_repo.py - Repository layer for referendum vote operations.

from typing import Type
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sqlalchemy.referendum_vote import ReferendumVote

logger = structlog.get_logger()


class ReferendumVoteRepository:
    """Repository layer for referendum-vote-related operations."""

    def __init__(self, model: Type[ReferendumVote] = ReferendumVote) -> None:
        self._model = model

    async def create_vote(self, session: AsyncSession, vote: ReferendumVote) -> ReferendumVote:
        """Persist a new referendum vote."""
        try:
            session.add(vote)
            await session.flush()

            logger.info("Referendum vote created successfully", vote_id=vote.id)
            return vote

        except Exception:
            logger.exception("Failed to create referendum vote")
            raise

    async def get_vote_by_blind_token_hash(
        self,
        session: AsyncSession,
        blind_token_hash: str,
    ) -> ReferendumVote | None:
        """Get a referendum vote by its blind token hash."""
        result = await session.execute(
            select(self._model).where(self._model.blind_token_hash == blind_token_hash)
        )
        return result.scalar_one_or_none()
