# investigation_repo.py - Repository layer for investigation operations.

from app.models.sqlalchemy.investigation import Investigation
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
from typing import Type
from uuid import UUID
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()


class InvestigationRepository:
    """Investigation repository operations."""

    _UPDATABLE_FIELDS = frozenset({
        "status", "category", "assigned_to", "notes",
        "resolved_by", "resolved_at",
    })

    def __init__(self, model: Type[Investigation] = Investigation) -> None:
        self._model = model

    async def create_investigation(
        self, session: AsyncSession, investigation: Investigation,
    ) -> Investigation:
        """Persist a new investigation."""
        try:
            session.add(investigation)
            await session.flush()
            logger.info("Investigation created", investigation_id=investigation.id)
            return investigation
        except Exception:
            logger.exception("Failed to create investigation")
            raise

    async def get_investigation_by_id(
        self, session: AsyncSession, investigation_id: UUID,
    ) -> Investigation:
        """Get an investigation by ID."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.id == investigation_id)
            )
            investigation = result.scalar_one_or_none()
            if not investigation:
                raise NotFoundError("Investigation not found")
            return investigation
        except Exception:
            logger.exception("Failed to get investigation", investigation_id=investigation_id)
            raise

    async def get_investigations_by_election(
        self, session: AsyncSession, election_id: UUID,
    ) -> list[Investigation]:
        """Get all investigations for an election."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.election_id == election_id)
                .order_by(self._model.raised_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get investigations by election", election_id=election_id)
            raise

    async def get_investigations_by_error(
        self, session: AsyncSession, error_id: UUID,
    ) -> list[Investigation]:
        """Get all investigations linked to an error report."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.error_id == error_id)
                .order_by(self._model.raised_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get investigations by error", error_id=error_id)
            raise

    async def get_investigations_by_assignee(
        self, session: AsyncSession, official_id: UUID,
    ) -> list[Investigation]:
        """Get all investigations assigned to a specific official."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.assigned_to == official_id)
                .order_by(self._model.raised_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get investigations by assignee", official_id=official_id)
            raise

    async def update_investigation(
        self,
        session: AsyncSession,
        investigation_id: UUID,
        update_data: dict,
    ) -> Investigation:
        """Update an investigation's mutable fields."""
        try:
            filtered = {
                k: v for k, v in update_data.items()
                if k in self._UPDATABLE_FIELDS and v is not None
            }
            if not filtered:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == investigation_id)
                .values(**filtered)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()
            if not updated:
                raise NotFoundError("Investigation not found")

            logger.info(
                "Investigation updated",
                investigation_id=investigation_id,
                updated_fields=list(filtered.keys()),
            )
            return updated
        except Exception:
            logger.exception("Failed to update investigation", investigation_id=investigation_id)
            raise
