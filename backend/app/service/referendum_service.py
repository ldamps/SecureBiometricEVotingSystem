# referendum_service.py - Service layer for referendum-related operations.

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.models.dto.referendum import (
    CreateReferendumPlainDTO,
    CreateReferendumEncryptedDTO,
    ReferendumDTO,
)
from app.models.schemas.referendum import ReferendumItem
from app.repository.referendum_repo import ReferendumRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.keys_manager_service import KeysManagerService
from app.service.encryption_mapper_service import EncryptionMapperService

logger = structlog.get_logger()


class ReferendumService(EncryptionUtilsMixin):
    """Service layer for referendum-related operations."""

    def __init__(
        self,
        referendum_repo: ReferendumRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
    ):
        self.referendum_repo = referendum_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper

    async def create_referendum(self, dto: CreateReferendumPlainDTO) -> ReferendumItem:
        """Create a new referendum."""
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            enc_row = await self._mapper.encrypt_dto(
                dto, CreateReferendumEncryptedDTO, args, self.session
            )
            referendum = enc_row.to_model()
            referendum = await self.referendum_repo.create_referendum(self.session, referendum)

            return await self.referendum_model_to_schema_item(referendum, self.session)
        except Exception:
            logger.exception("Failed to create referendum", dto=dto)
            raise

    async def get_referendum_by_id(self, referendum_id: UUID) -> ReferendumItem:
        """Get a referendum by its ID."""
        try:
            referendum = await self.referendum_repo.get_referendum_by_id(self.session, referendum_id)
            return await self.referendum_model_to_schema_item(referendum, self.session)
        except Exception:
            logger.exception("Failed to get referendum by ID", referendum_id=referendum_id)
            raise

    async def get_all_referendums(self) -> List[ReferendumItem]:
        """Get all referendums."""
        try:
            referendums = await self.referendum_repo.get_all_referendums(self.session)
            return [
                await self.referendum_model_to_schema_item(r, self.session)
                for r in referendums
            ]
        except Exception:
            logger.exception("Failed to get all referendums")
            raise

    async def update_referendum(self, referendum_id: UUID, update_data: dict) -> ReferendumItem:
        """Update a referendum's mutable fields."""
        try:
            updated = await self.referendum_repo.update_referendum(
                self.session, referendum_id, update_data
            )
            return await self.referendum_model_to_schema_item(updated, self.session)
        except Exception:
            logger.exception("Failed to update referendum", referendum_id=referendum_id)
            raise
