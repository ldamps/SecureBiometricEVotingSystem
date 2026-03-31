# official_repo.py - Repository layer for election official operations.

from app.models.sqlalchemy.election_official import ElectionOfficial, OfficialRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
from typing import Optional, Type
from uuid import UUID
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()


class OfficialRepository:
    """Election official repository operations."""

    _UPDATABLE_FIELDS = frozenset({
        "first_name", "last_name", "email_hash", "password_hash",
        "role", "is_active", "must_reset_password",
        "failed_login_attempts", "locked_until", "last_login_at",
    })

    def __init__(self, model: Type[ElectionOfficial] = ElectionOfficial) -> None:
        self._model = model

    # CRUD ----------

    async def create_official(
        self, session: AsyncSession, official: ElectionOfficial,
    ) -> ElectionOfficial:
        """Persist a new election official."""
        try:
            session.add(official)
            await session.flush()
            logger.info("Official created", official_id=official.id, role=official.role)
            return official
        except Exception:
            logger.exception("Failed to create official")
            raise

    async def get_official_by_id(
        self, session: AsyncSession, official_id: UUID,
    ) -> ElectionOfficial:
        """Get an official by ID."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.id == official_id)
            )
            official = result.scalar_one_or_none()
            if not official:
                raise NotFoundError("Election official not found")
            return official
        except Exception:
            logger.exception("Failed to get official by ID", official_id=official_id)
            raise

    async def get_official_by_username(
        self, session: AsyncSession, username: str,
    ) -> Optional[ElectionOfficial]:
        """Get an official by username (returns None if not found)."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.username == username)
            )
            return result.scalar_one_or_none()
        except Exception:
            logger.exception("Failed to get official by username", username=username)
            raise

    async def get_all_officials(
        self, session: AsyncSession,
    ) -> list[ElectionOfficial]:
        """Get all officials ordered by username."""
        try:
            result = await session.execute(
                select(self._model).order_by(self._model.username.asc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get all officials")
            raise

    async def get_officials_by_role(
        self, session: AsyncSession, role: str,
    ) -> list[ElectionOfficial]:
        """Get all officials with a specific role."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.role == role)
                .order_by(self._model.username.asc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get officials by role", role=role)
            raise

    async def update_official(
        self,
        session: AsyncSession,
        official_id: UUID,
        update_data: dict,
    ) -> ElectionOfficial:
        """Update an official's mutable fields."""
        try:
            filtered = {
                k: v for k, v in update_data.items()
                if k in self._UPDATABLE_FIELDS and v is not None
            }
            if not filtered:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == official_id)
                .values(**filtered)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()
            if not updated:
                raise NotFoundError("Election official not found")

            logger.info(
                "Official updated",
                official_id=official_id,
                updated_fields=list(filtered.keys()),
            )
            return updated
        except Exception:
            logger.exception("Failed to update official", official_id=official_id)
            raise

    async def deactivate_official(
        self, session: AsyncSession, official_id: UUID,
    ) -> ElectionOfficial:
        """Deactivate an official (soft disable)."""
        return await self.update_official(session, official_id, {"is_active": False})

    async def activate_official(
        self, session: AsyncSession, official_id: UUID,
    ) -> ElectionOfficial:
        """Reactivate a deactivated official."""
        return await self.update_official(session, official_id, {"is_active": True})
