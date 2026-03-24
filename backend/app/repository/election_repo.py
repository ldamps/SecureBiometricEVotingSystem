# election_repo.py - Repository layer for election-related operations.

from app.models.sqlalchemy.election import Election
from app.models.dto.election import UpdateElectionPlainDTO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
from typing import Optional, Type
from uuid import UUID
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()


class ElectionRepository:
    """Election-specific repository operations."""

    # Only these fields can be updated after an election is created.
    # Title, election_type, and allocation_method are immutable.
    _UPDATABLE_FIELDS = frozenset({"status", "voting_opens", "voting_closes"})

    def __init__(self, model: Type[Election] = Election) -> None:
        self._model = model

    # CRUD METHODS ----------

    async def create_election(self, session: AsyncSession, election: Election) -> Election:
        """Persist a new election."""
        try:
            session.add(election)
            await session.flush()

            logger.info(
                "Election created successfully",
                election_id=election.id,
            )
            return election

        except Exception:
            logger.exception("Failed to create election")
            raise

    async def get_election_by_id(
        self,
        session: AsyncSession,
        election_id: UUID,
    ) -> Election:
        """Get an election by its ID."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.id == election_id)
            )
            election = result.scalar_one_or_none()
            if not election:
                raise NotFoundError("Election not found")
            return election

        except Exception:
            logger.exception(
                "Failed to get election by ID",
                election_id=election_id,
            )
            raise

    async def get_all_elections(self, session: AsyncSession) -> list[Election]:
        """Get all elections ordered by creation date (newest first)."""
        try:
            result = await session.execute(
                select(self._model).order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())

        except Exception:
            logger.exception("Failed to get all elections")
            raise

    async def update_election(
        self,
        session: AsyncSession,
        election_id: UUID,
        dto: UpdateElectionPlainDTO,
    ) -> Election:
        """Update an election's mutable fields.

        Only status, voting_opens, and voting_closes can be changed.
        All other election fields are immutable after creation.
        """
        try:
            update_data = {}
            for field in self._UPDATABLE_FIELDS:
                val = getattr(dto, field, None)
                if val is not None:
                    update_data[field] = val

            if not update_data:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == election_id)
                .values(**update_data)
                .returning(self._model)
            )

            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()

            if not updated:
                raise NotFoundError("Election not found")

            logger.info(
                "Election updated successfully",
                election_id=election_id,
                updated_fields=list(update_data.keys()),
            )
            return updated

        except Exception:
            logger.exception(
                "Failed to update election",
                election_id=election_id,
            )
            raise
