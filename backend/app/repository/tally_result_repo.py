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
        constituency_id: UUID | None,
        candidate_id: UUID | None = None,
        party_id: UUID | None = None,
    ) -> TallyResult:
        """Increment vote count for a candidate or party, creating the tally row if needed.

        For FPTP / AMS constituency: candidate_id is set.
        For AMS regional: party_id is set.
        """
        filters = [
            self._model.election_id == election_id,
            self._model.constituency_id == constituency_id,
        ]
        if candidate_id:
            filters.append(self._model.candidate_id == candidate_id)
        else:
            filters.append(self._model.candidate_id.is_(None))
        if party_id:
            filters.append(self._model.party_id == party_id)
        else:
            filters.append(self._model.party_id.is_(None))

        result = await session.execute(select(self._model).where(*filters))
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
                "Tally incremented",
                tally_id=tally.id,
                vote_count=tally.vote_count,
            )
        else:
            tally = TallyResult(
                election_id=election_id,
                constituency_id=constituency_id,
                candidate_id=candidate_id,
                party_id=party_id,
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
                party_id=party_id,
            )

        return tally

    async def get_tallies_by_election(
        self,
        session: AsyncSession,
        election_id: UUID,
    ) -> list[TallyResult]:
        """Get all tally rows for an election, ordered by vote count descending."""
        result = await session.execute(
            select(self._model)
            .where(self._model.election_id == election_id)
            .order_by(self._model.vote_count.desc())
        )
        return list(result.scalars().all())

    async def get_tallies_by_constituency(
        self,
        session: AsyncSession,
        election_id: UUID,
        constituency_id: UUID,
    ) -> list[TallyResult]:
        """Get tally rows for an election + constituency, ordered by vote count descending."""
        result = await session.execute(
            select(self._model)
            .where(
                self._model.election_id == election_id,
                self._model.constituency_id == constituency_id,
            )
            .order_by(self._model.vote_count.desc())
        )
        return list(result.scalars().all())

    async def get_tallies_by_referendum(
        self,
        session: AsyncSession,
        referendum_id: UUID,
    ) -> list[TallyResult]:
        """Get tally rows for a referendum, ordered by choice."""
        result = await session.execute(
            select(self._model)
            .where(self._model.referendum_id == referendum_id)
            .order_by(self._model.choice.asc())
        )
        return list(result.scalars().all())

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
