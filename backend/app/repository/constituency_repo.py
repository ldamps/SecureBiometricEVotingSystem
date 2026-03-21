# constituency_repo.py - Data access layer for constituencies (read-only).

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.models.sqlalchemy.constituency import Constituency

logger = structlog.get_logger()


class ConstituencyRepository:
    """Read-only repository for constituencies."""

    async def get_all(self, session: AsyncSession) -> list[Constituency]:
        """Return all active constituencies ordered by country then name."""
        result = await session.execute(
            select(Constituency)
            .where(Constituency.is_active.is_(True))
            .order_by(Constituency.country, Constituency.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, session: AsyncSession, constituency_id: UUID) -> Optional[Constituency]:
        """Return a single constituency by ID, or None."""
        result = await session.execute(
            select(Constituency).where(Constituency.id == constituency_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[Constituency]:
        """Return a single active constituency by exact name match (case-insensitive)."""
        from sqlalchemy import func as sa_func
        result = await session.execute(
            select(Constituency)
            .where(
                sa_func.lower(Constituency.name) == name.strip().lower(),
                Constituency.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_country(self, session: AsyncSession, country: str) -> list[Constituency]:
        """Return all active constituencies for a given country."""
        result = await session.execute(
            select(Constituency)
            .where(Constituency.country == country, Constituency.is_active.is_(True))
            .order_by(Constituency.name)
        )
        return list(result.scalars().all())
