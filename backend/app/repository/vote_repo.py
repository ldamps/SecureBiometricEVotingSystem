# vote_repo.py - Repository layer for vote-related operations.

from typing import Type
from uuid import UUID

import structlog
from sqlalchemy import func, select
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

    async def get_constituency_ids_for_election(
        self,
        session: AsyncSession,
        election_id: UUID,
    ) -> list[UUID]:
        """Get distinct constituency IDs that have ranked votes for an election."""
        result = await session.execute(
            select(func.distinct(self._model.constituency_id))
            .where(
                self._model.election_id == election_id,
                self._model.constituency_id.isnot(None),
            )
        )
        return [row[0] for row in result.all()]

    async def get_ranked_votes_by_constituency(
        self,
        session: AsyncSession,
        election_id: UUID,
        constituency_id: UUID,
    ) -> list[Vote]:
        """Get ranked votes for a single constituency, ordered for ballot grouping.

        Fetches only one constituency at a time to keep memory bounded
        (typically ~70K voters per constituency at UK scale).
        """
        result = await session.execute(
            select(self._model)
            .where(
                self._model.election_id == election_id,
                self._model.constituency_id == constituency_id,
                self._model.candidate_id.isnot(None),
                self._model.preference_rank.isnot(None),
            )
            .order_by(self._model.blind_token_hash, self._model.preference_rank)
        )
        return list(result.scalars().all())
