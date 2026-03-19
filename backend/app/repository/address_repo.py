# address_repo.py - Repository layer for address-related operations.

from app.models.sqlalchemy.address import Address
from typing import Type, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.application.core.exceptions import NotFoundError
import structlog

logger = structlog.get_logger()

class AddressRepository:
    """Address-specific repository operations."""

    def __init__(self, model: Type[Address] = Address) -> None:
        self._model = model

    # CRUD METHODS ----------
    async def create_address(
        self,
        session: AsyncSession,
        address: Address,
    ) -> Address:
        """Create a new address."""
        try:
            session.add(address)
            await session.flush()
            return address
        except Exception:
            logger.exception("Failed to create address")
            raise

    async def get_address_by_id(
        self,
        session: AsyncSession,
        address_id: UUID,
    ) -> Address:
        """Get an address by its ID."""
        try:
            result = await session.execute(
                select(self._model).where(
                    self._model.id == address_id
                )
            )
            address = result.scalar_one_or_none()
            if not address:
                raise NotFoundError("Address not found")
            return address
        except Exception:
            logger.exception("Failed to get address by ID", address_id=address_id)
            raise

    async def get_all_addresses_by_voter_id(
        self,
        session: AsyncSession,
        voter_id: UUID,
    ) -> List[Address]:
        """Get all addresses by voter ID."""
        try:
            result = await session.execute(
                select(self._model).where(
                    self._model.voter_id == voter_id
                )
            )
            addresses = result.scalars().all()
            return addresses
        except Exception:
            logger.exception("Failed to get all addresses by voter ID", voter_id=voter_id)
            raise
    # ------------------------------------------------------------
