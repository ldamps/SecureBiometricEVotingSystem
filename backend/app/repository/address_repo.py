# address_repo.py - Repository layer for address-related operations.

from dataclasses import asdict

from app.models.sqlalchemy.address import Address
from typing import Type, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID
from app.application.core.exceptions import NotFoundError
import structlog
from app.models.dto.address import UpdateAddressPlainDTO

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

    async def update_address(
        self,
        session: AsyncSession,
        address_id: UUID,
        dto: UpdateAddressPlainDTO,
    ) -> Address:
        """
        Update an address.
        Can only update the following fields:
        - address type
        - address line 1
        - address line 2
        - town
        - postcode
        - county
        - country
        - address status
        - renew by date
        - address type
        """
        try:
            exclude = {"address_id", "voter_id"}
            update_data = {
                k: v for k, v in asdict(dto).items()
                if k not in exclude and v is not None
            }

            if not update_data:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == address_id)
                .values(**update_data)
                .returning(self._model)
            )
            result = await session.execute(stmt)

            updated = result.scalar_one_or_none()
            if not updated:
                raise NotFoundError("Address not found")
            
            logger.info(
                "Address updated successfully",
                address_id=address_id
            )
            return updated

        except Exception:
            logger.exception(
                "Failed to update address",
                address_id=address_id,
                dto=dto
            )
            raise

    async def delete_address(
        self,
        session: AsyncSession,
        address_id: UUID,
        voter_id: UUID,
    ) -> None:
        """ Delete an address. """
        try:
            stmt = (
                delete(self._model)
                .where(self._model.id == address_id)
                .where(self._model.voter_id == voter_id)
            )
            result = await session.execute(stmt)

            if result.rowcount == 0:
                raise NotFoundError("Address not found")

            logger.info("Address deleted successfully", address_id=address_id)

        except Exception:
            logger.exception("Failed to delete address", address_id=address_id, voter_id=voter_id)
            raise
    async def get_addresses_by_postcode_token(
        self,
        session: AsyncSession,
        postcode_search_token: str,
    ) -> List[Address]:
        """Get all addresses matching a postcode search token."""
        try:
            result = await session.execute(
                select(self._model).where(
                    self._model.postcode_search_token == postcode_search_token
                )
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception(
                "Failed to get addresses by postcode search token"
            )
            raise

    # ------------------------------------------------------------
