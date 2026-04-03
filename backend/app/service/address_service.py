from uuid import UUID
from typing import List
from datetime import datetime, timezone, timedelta
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dto.address import AddressDTO, CreateAddressEncryptedDTO, CreateAddressPlainDTO, UpdateAddressPlainDTO, DeleteAddressDTO
from app.models.schemas.address import AddressItem
from app.models.sqlalchemy.address import AddressType
from app.repository.address_repo import AddressRepository
from app.repository.constituency_repo import ConstituencyRepository
from app.repository.audit_log_repo import AuditLogRepository
from app.repository.voter_repo import VoterRepository
from app.models.sqlalchemy.audit_log import AuditLog
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.keys_manager_service import KeysManagerService
from app.application.core.exceptions import ValidationError

logger = structlog.get_logger()


class AddressService(EncryptionUtilsMixin):
    """ Service layer for address-related operations. """

    def __init__(
        self,
        address_repo: AddressRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
        constituency_repo: ConstituencyRepository | None = None,
        voter_repo: VoterRepository | None = None,
        audit_log_repo: AuditLogRepository | None = None,
    ):
        self.address_repo = address_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper
        self._constituency_repo = constituency_repo or ConstituencyRepository()
        self._voter_repo = voter_repo or VoterRepository()
        self._audit_log_repo = audit_log_repo or AuditLogRepository()

    async def _resolve_constituency(self, county: str) -> UUID:
        """Look up a constituency by county name. Raises ValidationError if not found."""
        constituency = await self._constituency_repo.get_by_name(self.session, county)
        if not constituency:
            raise ValidationError(
                f"No constituency found matching county '{county}'. "
                "The county must match a valid UK county name."
            )
        return constituency.id

    async def _resolve_overseas_constituency(self) -> UUID:
        """Return the ID of the 'Overseas' constituency."""
        constituency = await self._constituency_repo.get_by_name(self.session, "Overseas")
        if not constituency:
            raise ValidationError("Overseas constituency not found in the database.")
        return constituency.id

    async def _sync_voter_constituency(self, voter_id: UUID, county: str) -> None:
        """Resolve the constituency from the county name and update the voter record."""
        constituency_id = await self._resolve_constituency(county)
        await self._voter_repo.update_constituency(self.session, voter_id, constituency_id)
        logger.info(
            "Voter constituency synced from current address",
            voter_id=voter_id,
            constituency_id=constituency_id,
            county=county,
        )

    async def _sync_voter_overseas_constituency(self, voter_id: UUID) -> None:
        """Set the voter's constituency to Overseas."""
        constituency_id = await self._resolve_overseas_constituency()
        await self._voter_repo.update_constituency(self.session, voter_id, constituency_id)
        logger.info(
            "Voter constituency set to Overseas",
            voter_id=voter_id,
            constituency_id=constituency_id,
        )

    def _is_type(self, value, address_type: AddressType) -> bool:
        """Check if a value matches an AddressType (handles both str and enum)."""
        return value == address_type.value or value == address_type

    async def create_address(
        self,
        dto: CreateAddressPlainDTO,
    ) -> AddressItem:
        """Create a new address with encrypted fields.

        If the address is LOCAL_CURRENT:
        - Validates that the county matches a known constituency.
        - Demotes any existing LOCAL_CURRENT address to PAST.
        - Updates the voter's constituency_id to match.

        If the address is OVERSEAS:
        - Demotes any existing LOCAL_CURRENT address to PAST.
        - Sets the voter's constituency to the Overseas constituency.
        - County and postcode are not required.
        """
        try:
            dto.renew_by = datetime.now(timezone.utc) + timedelta(days=730)
            # Address always starts as PENDING — only verified via proof of address
            dto.address_status = "PENDING"

            is_current = self._is_type(dto.address_type, AddressType.LOCAL_CURRENT)
            is_overseas = self._is_type(dto.address_type, AddressType.OVERSEAS)

            # Validate county against constituencies before persisting
            if is_current:
                if not dto.county or not dto.county.strip():
                    raise ValidationError("County is required for a current local address.")
                await self._resolve_constituency(dto.county)

            # Both LOCAL_CURRENT and OVERSEAS demote the existing current address
            if is_current or is_overseas:
                await self.address_repo.demote_current_address(self.session, dto.voter_id)

            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            encrypted_dto = await self._mapper.encrypt_dto(
                dto, CreateAddressEncryptedDTO, args, self.session
            )

            address_model = encrypted_dto.to_model()
            address = await self.address_repo.create_address(
                self.session, address_model
            )

            # Sync voter constituency
            if is_current:
                await self._sync_voter_constituency(dto.voter_id, dto.county)
            elif is_overseas:
                await self._sync_voter_overseas_constituency(dto.voter_id)

            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="ADDRESS_CREATED",
                    action="CREATE",
                    summary=f"Address created for voter {dto.voter_id}",
                    resource_type="address",
                    resource_id=address.id,
                    actor_type="VOTER",
                ),
            )

            address_dto = await self._mapper.decrypt_model(
                address, AddressDTO, args, self.session
            )
            return address_dto.to_schema()

        except (ValidationError,):
            raise
        except Exception:
            logger.exception("Failed to create address", dto=dto)
            raise


    async def get_address_by_id(
        self,
        voter_id: UUID,
        address_id: UUID,
    ) -> AddressItem:
        """Get an address by its ID. Validates that the address belongs to the voter."""
        try:
            address = await self.address_repo.get_address_by_id(
                self.session, address_id
            )
            if address.voter_id != voter_id:
                raise ValidationError("Address does not belong to this voter.")
            return await self.address_model_to_schema_item(address, self.session)
        except (ValidationError,):
            raise
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
        """Update an address.

        If updating a LOCAL_CURRENT address and the county changes,
        the voter's constituency is re-resolved and updated.
        If the address_type is being changed TO LOCAL_CURRENT,
        the same constituency resolution applies.
        If the address_type is being changed TO OVERSEAS,
        the current address is demoted and constituency set to Overseas.
        """
        dto.renew_by = datetime.now(timezone.utc) + timedelta(days=730)

        existing = await self.address_repo.get_address_by_id(self.session, dto.address_id)
        becoming_current = self._is_type(dto.address_type, AddressType.LOCAL_CURRENT) if dto.address_type else False
        becoming_overseas = self._is_type(dto.address_type, AddressType.OVERSEAS) if dto.address_type else False
        is_currently_current = existing.address_type == AddressType.LOCAL_CURRENT
        is_currently_overseas = existing.address_type == AddressType.OVERSEAS

        # Switching to LOCAL_CURRENT — validate county and demote old current
        if becoming_current and not is_currently_current:
            if not dto.county or not dto.county.strip():
                raise ValidationError("County is required for a current local address.")
            await self._resolve_constituency(dto.county)
            await self.address_repo.demote_current_address(self.session, dto.voter_id)

        # Switching to OVERSEAS — demote old current
        if becoming_overseas and not is_currently_overseas:
            await self.address_repo.demote_current_address(self.session, dto.voter_id)

        updated = await self.address_repo.update_address(
            self.session,
            dto.address_id,
            dto,
        )

        # Re-sync constituency
        if becoming_current or (is_currently_current and dto.county):
            county = dto.county if dto.county else None
            if county:
                await self._sync_voter_constituency(dto.voter_id, county)
        elif becoming_overseas:
            await self._sync_voter_overseas_constituency(dto.voter_id)

        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="ADDRESS_UPDATED",
                action="UPDATE",
                summary=f"Address {dto.address_id} updated for voter {dto.voter_id}",
                resource_type="address",
                resource_id=dto.address_id,
                actor_type="VOTER",
            ),
        )

        return await self.address_model_to_schema_item(updated, self.session)

    async def delete_address(
        self,
        voter_id: UUID,
        address_id: UUID,
    ) -> None:
        """Delete an address.

        LOCAL_CURRENT and OVERSEAS addresses cannot be deleted directly.
        Create a new address to replace them instead.
        """
        existing = await self.address_repo.get_address_by_id(self.session, address_id)
        if existing.address_type == AddressType.LOCAL_CURRENT:
            raise ValidationError(
                "Cannot delete a current local address. "
                "Create a new current address first, which will demote this one."
            )
        if existing.address_type == AddressType.OVERSEAS:
            raise ValidationError(
                "Cannot delete an overseas address. "
                "Create a new local current address to replace it."
            )
        await self.address_repo.delete_address(
            self.session,
            address_id,
            voter_id,
        )

        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="ADDRESS_DELETED",
                action="DELETE",
                summary=f"Address {address_id} deleted for voter {voter_id}",
                resource_type="address",
                resource_id=address_id,
                actor_type="VOTER",
            ),
        )
