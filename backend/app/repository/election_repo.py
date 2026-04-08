# election_repo.py - Repository layer for election-related operations.

from app.models.sqlalchemy.election import Election, election_constituency
from app.models.dto.election import UpdateElectionPlainDTO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, update
from sqlalchemy.orm import selectinload
import structlog
from typing import Optional, Type
from uuid import UUID
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()


class ElectionRepository:
    """Election-specific repository operations."""

    # Fields that can always be updated.
    _ALWAYS_UPDATABLE = frozenset({"status", "voting_opens", "voting_closes"})
    # Additional fields that can be updated while in DRAFT status.
    _DRAFT_UPDATABLE = frozenset({"title", "election_type", "scope", "allocation_method"})

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
                select(self._model)
                .options(selectinload(self._model.constituencies))
                .where(self._model.id == election_id)
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
                select(self._model)
                .options(selectinload(self._model.constituencies))
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())

        except Exception:
            logger.exception("Failed to get all elections")
            raise

    async def get_elections_by_constituency(
        self,
        session: AsyncSession,
        constituency_id: UUID,
    ) -> list[Election]:
        """Get elections for a constituency.

        Returns elections that include the given constituency plus
        national elections (those with no constituencies assigned).
        """
        try:
            # Election IDs linked to this constituency
            has_constituency = (
                select(election_constituency.c.election_id)
                .where(election_constituency.c.constituency_id == constituency_id)
            )

            # Election IDs that have any constituency links at all
            has_any_constituency = (
                select(election_constituency.c.election_id).distinct()
            )

            result = await session.execute(
                select(self._model)
                .options(selectinload(self._model.constituencies))
                .where(
                    or_(
                        self._model.id.in_(has_constituency),
                        ~self._model.id.in_(has_any_constituency),
                    )
                )
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())

        except Exception:
            logger.exception(
                "Failed to get elections by constituency",
                constituency_id=constituency_id,
            )
            raise

    async def update_election(
        self,
        session: AsyncSession,
        election_id: UUID,
        dto: UpdateElectionPlainDTO,
        is_draft: bool = False,
    ) -> Election:
        """Update an election's mutable fields.

        When *is_draft* is True, title/election_type/scope/allocation_method
        are also editable.
        """
        try:
            allowed = self._ALWAYS_UPDATABLE | (self._DRAFT_UPDATABLE if is_draft else frozenset())
            update_data = {}
            for field in allowed:
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
