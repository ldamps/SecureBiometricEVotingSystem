# voter_service.py - Service layer for voter-related operations.

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import (
    RegisterVoterPlainDTO,
    RegisterVoterEncryptedDTO,
    UpdateVoterPlainDTO,
    UpdateVoterEncryptedDTO,
)
from app.models.schemas.voter import VoterItem
from app.repository.voter_repo import VoterRepository
from app.service.base.encryption_utils_mixin import (
    EncryptionUtilsMixin,
    prepare_voter_registration_plain_fields,
)
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()


class VoterService(EncryptionUtilsMixin):
    """Service layer for voter-related operations."""

    def __init__(
        self,
        voter_repo: VoterRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
        voter: Optional[Voter] = None,
    ):
        self.voter_repo = voter_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper
        self.voter = voter

    async def register_voter(self, dto: RegisterVoterPlainDTO) -> VoterItem:
        """Create a new voter with encrypted JSONB fields and search tokens."""
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            plain_fields = prepare_voter_registration_plain_fields(dto)
            plain = RegisterVoterPlainDTO(**plain_fields)

            enc_row = await self._mapper.encrypt_dto(
                plain, RegisterVoterEncryptedDTO, args, self.session
            )
            voter = enc_row.to_model()
            voter = await self.voter_repo.register_voter(self.session, voter)
            return await self.voter_model_to_schema_item(voter, self.session)
        except Exception:
            logger.exception("Failed to register voter", dto=dto)
            raise

    async def get_voter_by_id(self, voter_id: UUID) -> VoterItem:
        """Get a voter by their ID."""
        try:
            voter = await self.voter_repo.get_voter_by_id(self.session, voter_id)
            return await self.voter_model_to_schema_item(voter, self.session)
        except Exception:
            logger.exception("Failed to get voter by ID", voter_id=voter_id)
            raise

    async def update_voter_details(
        self,
        voter_id: UUID,
        dto: UpdateVoterPlainDTO,
    ) -> VoterItem:
        """Update a voter's details."""
        updated = await self.voter_repo.update_voter_details(
            self.session,
            voter_id,
            dto,
        )
        return await self.voter_model_to_schema_item(updated, self.session)

    async def check_voter_exists(self, voter_id: UUID) -> bool:
        """Check if a voter exists."""
        pass

    async def check_voter_locked(self, voter_id: UUID) -> bool:
        """Check if a voter is locked."""
        pass

    async def check_voter_renewal_needed(self, voter_id: UUID) -> bool:
        """Check if a voter's account needs to be renewed."""
        pass

    async def get_user_addresses(self, voter_id: UUID):
        """Get a voter's addresses."""
        pass

    async def get_user_biometric_templates(self, voter_id: UUID):
        """Get a voter's biometric templates."""
        pass

    async def get_user_voter_ledger(self, voter_id: UUID):
        """Get a voter's voter ledger."""
        pass
