# candidate_repo.py - Repository layer for candidate-related operations.

from app.models.sqlalchemy.candidate import Candidate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
from typing import Type
from uuid import UUID
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()


class CandidateRepository:
    """Candidate-specific repository operations."""

    _UPDATABLE_FIELDS = frozenset({"first_name", "last_name", "is_active"})

    def __init__(self, model: Type[Candidate] = Candidate) -> None:
        self._model = model

    async def create_candidate(self, session: AsyncSession, candidate: Candidate) -> Candidate:
        """Persist a new candidate."""
        try:
            session.add(candidate)
            await session.flush()
            logger.info("Candidate created successfully", candidate_id=candidate.id)
            return candidate
        except Exception:
            logger.exception("Failed to create candidate")
            raise

    async def get_candidate_by_id(self, session: AsyncSession, candidate_id: UUID) -> Candidate:
        """Get a candidate by its ID."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.id == candidate_id)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                raise NotFoundError("Candidate not found")
            return candidate
        except Exception:
            logger.exception("Failed to get candidate by ID", candidate_id=candidate_id)
            raise

    async def get_candidates_by_election_id(self, session: AsyncSession, election_id: UUID) -> list[Candidate]:
        """Get all candidates for a given election."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.election_id == election_id)
                .order_by(self._model.last_name.asc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get candidates by election ID", election_id=election_id)
            raise

    async def get_candidates_by_party_id(self, session: AsyncSession, party_id: UUID) -> list[Candidate]:
        """Get all candidates belonging to a given party."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.party_id == party_id)
                .order_by(self._model.last_name.asc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get candidates by party ID", party_id=party_id)
            raise

    async def get_candidate_by_election_and_party(
        self, session: AsyncSession, election_id: UUID, constituency_id: UUID, party_id: UUID,
    ) -> Candidate | None:
        """Get the candidate for a specific party in an election constituency (at most one)."""
        try:
            result = await session.execute(
                select(self._model).where(
                    self._model.election_id == election_id,
                    self._model.constituency_id == constituency_id,
                    self._model.party_id == party_id,
                )
            )
            return result.scalars().first()
        except Exception:
            logger.exception("Failed to get candidate by election and party")
            raise

    async def update_candidate(
        self,
        session: AsyncSession,
        candidate_id: UUID,
        update_data: dict,
    ) -> Candidate:
        """Update a candidate's mutable fields."""
        try:
            filtered = {k: v for k, v in update_data.items() if k in self._UPDATABLE_FIELDS and v is not None}
            if not filtered:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == candidate_id)
                .values(**filtered)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()
            if not updated:
                raise NotFoundError("Candidate not found")

            logger.info("Candidate updated successfully", candidate_id=candidate_id)
            return updated
        except Exception:
            logger.exception("Failed to update candidate", candidate_id=candidate_id)
            raise
