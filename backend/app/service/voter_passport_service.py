# voter_passport_service.py - Service layer for voter passport operations.

from uuid import UUID
from typing import List
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dto.voter_passport import (
    VoterPassportDTO,
    CreateVoterPassportEncryptedDTO,
    CreateVoterPassportPlainDTO,
    UpdateVoterPassportPlainDTO,
)
from app.models.schemas.voter_passport import VoterPassportItem
from app.repository.voter_passport_repo import VoterPassportRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()


class VoterPassportService(EncryptionUtilsMixin):
    """Service layer for voter passport operations."""

    def __init__(
        self,
        passport_repo: VoterPassportRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
    ):
        self.passport_repo = passport_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper

    async def create_passport(
        self,
        dto: CreateVoterPassportPlainDTO,
    ) -> VoterPassportItem:
        """Create a new voter passport entry with encrypted fields."""
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            encrypted_dto = await self._mapper.encrypt_dto(
                dto, CreateVoterPassportEncryptedDTO, args, self.session
            )

            passport_model = encrypted_dto.to_model()
            passport = await self.passport_repo.create_passport(
                self.session, passport_model
            )

            passport_dto = await self._mapper.decrypt_model(
                passport, VoterPassportDTO, args, self.session
            )
            return passport_dto.to_schema()

        except Exception:
            logger.exception("Failed to create voter passport", dto=dto)
            raise

    async def get_passport_by_id(
        self,
        voter_id: UUID,
        passport_id: UUID,
    ) -> VoterPassportItem:
        """Get a passport entry by its ID."""
        try:
            passport = await self.passport_repo.get_passport_by_id(
                self.session, passport_id
            )
            return await self.passport_model_to_schema_item(passport, self.session)
        except Exception:
            logger.exception("Failed to get voter passport by ID", passport_id=passport_id)
            raise

    async def get_all_passports_by_voter_id(
        self,
        voter_id: UUID,
    ) -> List[VoterPassportItem]:
        """Get all passport entries for a voter."""
        try:
            passports = await self.passport_repo.get_all_passports_by_voter_id(
                self.session, voter_id
            )
            return [
                await self.passport_model_to_schema_item(p, self.session)
                for p in passports
            ]
        except Exception:
            logger.exception("Failed to get passports for voter", voter_id=voter_id)
            raise

    async def update_passport(
        self,
        dto: UpdateVoterPassportPlainDTO,
    ) -> VoterPassportItem:
        """Update a voter passport entry."""
        updated = await self.passport_repo.update_passport(
            self.session,
            dto.passport_id,
            dto,
        )
        return await self.passport_model_to_schema_item(updated, self.session)

    async def delete_passport(
        self,
        voter_id: UUID,
        passport_id: UUID,
    ) -> None:
        """Delete a voter passport entry."""
        await self.passport_repo.delete_passport(
            self.session,
            passport_id,
            voter_id,
        )
