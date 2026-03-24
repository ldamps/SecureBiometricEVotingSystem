# party_repo.py - Repository layer for party-related operations.

from app.models.sqlalchemy.party import Party
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
from typing import Type
from uuid import UUID
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()


class PartyRepository:
    """Party-specific repository operations."""

    _UPDATABLE_FIELDS = frozenset({"party_name", "abbreviation", "is_active"})

    def __init__(self, model: Type[Party] = Party) -> None:
        self._model = model

    async def create_party(self, session: AsyncSession, party: Party) -> Party:
        """Persist a new party."""
        try:
            session.add(party)
            await session.flush()
            logger.info("Party created successfully", party_id=party.id)
            return party
        except Exception:
            logger.exception("Failed to create party")
            raise

    async def get_party_by_id(self, session: AsyncSession, party_id: UUID) -> Party:
        """Get a party by its ID."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.id == party_id)
            )
            party = result.scalar_one_or_none()
            if not party:
                raise NotFoundError("Party not found")
            return party
        except Exception:
            logger.exception("Failed to get party by ID", party_id=party_id)
            raise

    async def get_all_parties(self, session: AsyncSession) -> list[Party]:
        """Get all parties ordered by name."""
        try:
            result = await session.execute(
                select(self._model).order_by(self._model.party_name.asc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get all parties")
            raise

    async def update_party(
        self,
        session: AsyncSession,
        party_id: UUID,
        update_data: dict,
    ) -> Party:
        """Update a party's mutable fields."""
        try:
            filtered = {k: v for k, v in update_data.items() if k in self._UPDATABLE_FIELDS and v is not None}
            if not filtered:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == party_id)
                .values(**filtered)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()
            if not updated:
                raise NotFoundError("Party not found")

            logger.info("Party updated successfully", party_id=party_id)
            return updated
        except Exception:
            logger.exception("Failed to update party", party_id=party_id)
            raise

    async def soft_delete_party(self, session: AsyncSession, party_id: UUID) -> Party:
        """Soft delete a party by setting is_active to False."""
        return await self.update_party(session, party_id, {"is_active": False})

    async def get_deleted_parties(self, session: AsyncSession) -> list[Party]:
        """Get all soft-deleted (inactive) parties."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.is_active == False)
                .order_by(self._model.party_name.asc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get deleted parties")
            raise

    async def restore_party(self, session: AsyncSession, party_id: UUID) -> Party:
        """Restore a soft-deleted party by setting is_active to True."""
        return await self.update_party(session, party_id, {"is_active": True})
