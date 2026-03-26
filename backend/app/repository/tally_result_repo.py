# tally_result_repo.py - Repository layer for tally-result operations.

from datetime import datetime
from typing import Type
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sqlalchemy.tally_result import TallyResult

logger = structlog.get_logger()


class TallyResultRepository:
    """Repository layer for tally-result-related operations."""

    def __init__(self, model: Type[TallyResult] = TallyResult) -> None:
        self._model = model

    async def increment_vote_count(
        self,
        session: AsyncSession,
        election_id: UUID,
        constituency_id: UUID,
        candidate_id: UUID,
    ) -> TallyResult:
        """Increment vote count for a candidate, creating the tally row if needed."""
        # Try to find existing tally row
        result = await session.execute(
            select(self._model).where(
                self._model.election_id == election_id,
                self._model.constituency_id == constituency_id,
                self._model.candidate_id == candidate_id,
            )
        )
        tally = result.scalar_one_or_none()

        now = datetime.now()

        if tally:
            # Increment existing row
            stmt = (
                update(self._model)
                .where(self._model.id == tally.id)
                .values(vote_count=self._model.vote_count + 1, tallied_at=now)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            tally = result.scalar_one()
            logger.info(
                "Tally incremented",
                tally_id=tally.id,
                vote_count=tally.vote_count,
            )
        else:
            # Create new tally row
            tally = TallyResult(
                election_id=election_id,
                constituency_id=constituency_id,
                candidate_id=candidate_id,
                vote_count=1,
                tallied_at=now,
            )
            session.add(tally)
            await session.flush()
            logger.info(
                "Tally created",
                tally_id=tally.id,
                election_id=election_id,
                candidate_id=candidate_id,
            )

        return tally

    async def increment_referendum_vote_count(
        self,
        session: AsyncSession,
        referendum_id: UUID,
        choice: str,
    ) -> TallyResult:
        """Increment vote count for a referendum choice (YES/NO), creating the tally row if needed."""
        result = await session.execute(
            select(self._model).where(
                self._model.referendum_id == referendum_id,
                self._model.choice == choice,
            )
        )
        tally = result.scalar_one_or_none()

        now = datetime.now()

        if tally:
            stmt = (
                update(self._model)
                .where(self._model.id == tally.id)
                .values(vote_count=self._model.vote_count + 1, tallied_at=now)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            tally = result.scalar_one()
            logger.info(
                "Referendum tally incremented",
                tally_id=tally.id,
                vote_count=tally.vote_count,
            )
        else:
            tally = TallyResult(
                referendum_id=referendum_id,
                choice=choice,
                vote_count=1,
                tallied_at=now,
            )
            session.add(tally)
            await session.flush()
            logger.info(
                "Referendum tally created",
                tally_id=tally.id,
                referendum_id=referendum_id,
                choice=choice,
            )

        return tally
