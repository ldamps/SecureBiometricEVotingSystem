from uuid import UUID
from typing import List
from datetime import datetime, timezone, timedelta
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dto.address import AddressDTO, CreateAddressEncryptedDTO, CreateAddressPlainDTO, UpdateAddressPlainDTO, DeleteAddressDTO
from app.models.schemas.address import AddressItem
from app.repository.address_repo import AddressRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()


class AddressService(EncryptionUtilsMixin):
    """ Service layer for address-related operations. """

    def __init__(
        self,
        address_repo: AddressRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
    ):
        self.address_repo = address_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper

    async def create_address(
        self,
        dto: CreateAddressPlainDTO,
    ) -> AddressItem:
        """Create a new address with encrypted fields."""
        try:
            dto.renew_by = datetime.now(timezone.utc) + timedelta(days=730)

            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            encrypted_dto = await self._mapper.encrypt_dto(
                dto, CreateAddressEncryptedDTO, args, self.session
            )

            address_model = encrypted_dto.to_model()
            address = await self.address_repo.create_address(
                self.session, address_model
            )

            address_dto = await self._mapper.decrypt_model(
                address, AddressDTO, args, self.session
            )
            return address_dto.to_schema()

        except Exception:
            logger.exception("Failed to create address", dto=dto)
            raise


    async def get_address_by_id(
        self,
        voter_id: UUID,
        address_id: UUID,
    ) -> AddressItem:
        """Get an address by its ID."""
        try:
            address = await self.address_repo.get_address_by_id(
                self.session, address_id
            )
            return await self.address_model_to_schema_item(address, self.session)
        except Exception:
            logger.exception("Failed to get address by ID", address_id=address_id)
            raise

    async def get_all_addresses_by_voter_id(
        self,
        voter_id: UUID,
    ) -> List[AddressItem]:
        """Get all addresses by voter ID."""
        try:
            addresses = await self.address_repo.get_all_addresses_by_voter_id(
                self.session, voter_id
            )
            return [await self.address_model_to_schema_item(address, self.session) for address in addresses]
        except Exception:
            logger.exception("Failed to get all addresses by voter ID", voter_id=voter_id)
            raise

    async def update_address(
        self,
        dto: UpdateAddressPlainDTO,
    ) -> AddressItem:
        """Update an address."""
        dto.renew_by = datetime.now(timezone.utc) + timedelta(days=730)
        updated = await self.address_repo.update_address(
            self.session,
            dto.address_id,
            dto,
        )
        return await self.address_model_to_schema_item(updated, self.session)

    async def delete_address(
        self,
        voter_id: UUID,
        address_id: UUID,
    ) -> None:
        """Delete an address."""
        await self.address_repo.delete_address(
            self.session,
            address_id,
            voter_id,
        )

        
