# constituency_service.py - Business logic for constituencies (read-only).

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.models.sqlalchemy.constituency import Constituency
from app.repository.constituency_repo import ConstituencyRepository

logger = structlog.get_logger()


class ConstituencyService:
    """Read-only service for constituencies."""

    def __init__(self, constituency_repo: ConstituencyRepository, session: AsyncSession):
        self._repo = constituency_repo
        self._session = session

    async def get_all(self) -> list[Constituency]:
        """Return all active constituencies."""
        return await self._repo.get_all(self._session)

    async def get_by_id(self, constituency_id: UUID) -> Optional[Constituency]:
        """Return a single constituency by ID."""
        return await self._repo.get_by_id(self._session, constituency_id)

    async def get_by_country(self, country: str) -> list[Constituency]:
        """Return all active constituencies for a country."""
        return await self._repo.get_by_country(self._session, country)
