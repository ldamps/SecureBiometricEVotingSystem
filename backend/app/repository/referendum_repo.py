# referendum_repo.py - Repository layer for referendum-related operations.

from app.models.sqlalchemy.referendum import Referendum, referendum_constituency
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_
from sqlalchemy.orm import selectinload
import structlog
from typing import Type
from uuid import UUID
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()


class ReferendumRepository:
    """Referendum-specific repository operations."""

    _UPDATABLE_FIELDS = frozenset({"question", "description", "status", "voting_opens", "voting_closes", "is_active"})

    def __init__(self, model: Type[Referendum] = Referendum) -> None:
        self._model = model

    async def create_referendum(self, session: AsyncSession, referendum: Referendum) -> Referendum:
        """Persist a new referendum."""
        try:
            session.add(referendum)
            await session.flush()
            logger.info("Referendum created successfully", referendum_id=referendum.id)
            return referendum
        except Exception:
            logger.exception("Failed to create referendum")
            raise

    async def get_referendum_by_id(self, session: AsyncSession, referendum_id: UUID) -> Referendum:
        """Get a referendum by its ID."""
        try:
            result = await session.execute(
                select(self._model)
                .options(selectinload(self._model.constituencies))
                .where(self._model.id == referendum_id)
            )
            referendum = result.scalar_one_or_none()
            if not referendum:
                raise NotFoundError("Referendum not found")
            return referendum
        except Exception:
            logger.exception("Failed to get referendum by ID", referendum_id=referendum_id)
            raise

    async def get_all_referendums(self, session: AsyncSession) -> list[Referendum]:
        """Get all referendums ordered by creation date (newest first)."""
        try:
            result = await session.execute(
                select(self._model)
                .options(selectinload(self._model.constituencies))
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get all referendums")
            raise

    async def get_referendums_by_constituency(
        self,
        session: AsyncSession,
        constituency_id: UUID,
    ) -> list[Referendum]:
        """Get referendums for a constituency.

        Returns referendums that include the given constituency plus
        national referendums (those with no constituencies assigned).
        """
        try:
            # Referendum IDs that are linked to this constituency
            has_constituency = (
                select(referendum_constituency.c.referendum_id)
                .where(referendum_constituency.c.constituency_id == constituency_id)
            )

            # Referendum IDs that have no constituency links at all (national)
            has_any_constituency = (
                select(referendum_constituency.c.referendum_id).distinct()
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
                "Failed to get referendums by constituency",
                constituency_id=constituency_id,
            )
            raise

    async def update_referendum(
        self,
        session: AsyncSession,
        referendum_id: UUID,
        update_data: dict,
    ) -> Referendum:
        """Update a referendum's mutable fields."""
        try:
            filtered = {k: v for k, v in update_data.items() if k in self._UPDATABLE_FIELDS and v is not None}
            if not filtered:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == referendum_id)
                .values(**filtered)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()
            if not updated:
                raise NotFoundError("Referendum not found")

            logger.info("Referendum updated successfully", referendum_id=referendum_id)
            return updated
        except Exception:
            logger.exception("Failed to update referendum", referendum_id=referendum_id)
            raise
