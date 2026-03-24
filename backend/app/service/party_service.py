# party_service.py - Service layer for party-related operations.

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.models.dto.party import (
    CreatePartyPlainDTO,
    CreatePartyEncryptedDTO,
    PartyDTO,
)
from app.models.schemas.party import PartyItem
from app.repository.party_repo import PartyRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.keys_manager_service import KeysManagerService
from app.service.encryption_mapper_service import EncryptionMapperService

logger = structlog.get_logger()


class PartyService(EncryptionUtilsMixin):
    """Service layer for party-related operations."""

    def __init__(
        self,
        party_repo: PartyRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
    ):
        self.party_repo = party_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper

    async def create_party(self, dto: CreatePartyPlainDTO) -> PartyItem:
        """Create a new party."""
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            enc_row = await self._mapper.encrypt_dto(
                dto, CreatePartyEncryptedDTO, args, self.session
            )
            party = enc_row.to_model()
            party = await self.party_repo.create_party(self.session, party)

            return await self.party_model_to_schema_item(party, self.session)
        except Exception:
            logger.exception("Failed to create party")
            raise

    async def get_party_by_id(self, party_id: UUID) -> PartyItem:
        """Get a party by its ID."""
        try:
            party = await self.party_repo.get_party_by_id(self.session, party_id)
            return await self.party_model_to_schema_item(party, self.session)
        except Exception:
            logger.exception("Failed to get party by ID", party_id=party_id)
            raise

    async def get_all_parties(self) -> List[PartyItem]:
        """Get all parties."""
        try:
            parties = await self.party_repo.get_all_parties(self.session)
            return [
                await self.party_model_to_schema_item(p, self.session)
                for p in parties
            ]
        except Exception:
            logger.exception("Failed to get all parties")
            raise

    async def update_party(self, party_id: UUID, update_data: dict) -> PartyItem:
        """Update a party's mutable fields."""
        try:
            updated = await self.party_repo.update_party(
                self.session, party_id, update_data
            )
            return await self.party_model_to_schema_item(updated, self.session)
        except Exception:
            logger.exception("Failed to update party", party_id=party_id)
            raise

    async def soft_delete_party(self, party_id: UUID) -> PartyItem:
        """Soft delete a party."""
        try:
            deleted = await self.party_repo.soft_delete_party(self.session, party_id)
            return await self.party_model_to_schema_item(deleted, self.session)
        except Exception:
            logger.exception("Failed to soft delete party", party_id=party_id)
            raise

    async def get_deleted_parties(self) -> List[PartyItem]:
        """Get all soft-deleted (inactive) parties."""
        try:
            parties = await self.party_repo.get_deleted_parties(self.session)
            return [
                await self.party_model_to_schema_item(p, self.session)
                for p in parties
            ]
        except Exception:
            logger.exception("Failed to get deleted parties")
            raise

    async def restore_party(self, party_id: UUID) -> PartyItem:
        """Restore a soft-deleted party."""
        try:
            restored = await self.party_repo.restore_party(self.session, party_id)
            return await self.party_model_to_schema_item(restored, self.session)
        except Exception:
            logger.exception("Failed to restore party", party_id=party_id)
            raise
