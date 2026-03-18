# voter_service.py - Service layer for voter-related operations.

import structlog
from app.repository.voter_repo import VoterRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import (
    RegisterVoterPlainDTO,
    RegisterVoterEncryptionPlainDTO,
    UpdateVoterPlainDTO,
    RegisterVoterEncryptedDTO,
    VoterDecryptedDTO,
    VoterBaseDTO,
    VoterPersistEncryptedDTO,
    voter_orm_from_persist_encrypted,
)
from app.models.schemas.voter import VoterItem
from app.models.base.sqlalchemy_base import EncryptedDBField
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.keys_manager_service import KeysManagerService
from uuid import UUID

logger = structlog.get_logger()


def _voter_row_has_encrypted_fields(voter: Voter) -> bool:
    """True if any column holds EncryptedDBField (needs DEK + decrypt)."""
    for name in VoterBaseDTO.__encrypted_fields__:
        if isinstance(getattr(voter, name, None), EncryptedDBField):
            return True
    return False


def _voter_orm_to_decrypted_dto_unencrypted_row(voter: Voter) -> VoterDecryptedDTO:
    """Map ORM row when encrypted JSONB columns are NULL (e.g. post-migration)."""

    def enc_plain(name: str) -> Optional[str]:
        v = getattr(voter, name, None)
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, (bytes, bytearray)):
            return v.decode("utf-8", errors="replace") if v else None
        return None

    return VoterDecryptedDTO(
        id=voter.id,
        voter_status=voter.voter_status,
        registration_status=voter.registration_status,
        failed_auth_attempts=voter.failed_auth_attempts,
        national_insurance_number=enc_plain("national_insurance_number"),
        passport_number=enc_plain("passport_number"),
        passport_country=enc_plain("passport_country"),
        first_name=enc_plain("first_name"),
        surname=enc_plain("surname"),
        previous_first_name=enc_plain("previous_first_name"),
        previous_surname=enc_plain("previous_surname"),
        date_of_birth=enc_plain("date_of_birth"),
        email=enc_plain("email"),
        voter_reference=enc_plain("voter_reference"),
        constituency_id=voter.constituency_id,
        locked_until=voter.locked_until,
        registered_at=voter.registered_at,
        renew_by=voter.renew_by,
    )


class VoterService:
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

    async def _voter_orm_to_item(self, voter: Voter) -> VoterItem:
        if _voter_row_has_encrypted_fields(voter):
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)
            dto = await self._mapper.decrypt_model(voter, VoterDecryptedDTO, args, self.session)
        else:
            dto = _voter_orm_to_decrypted_dto_unencrypted_row(voter)
        return dto.to_schema()

    async def register_voter(self, dto: RegisterVoterPlainDTO) -> VoterItem:
        """Create a new voter with encrypted JSONB fields and search tokens."""
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)
            plain = RegisterVoterEncryptionPlainDTO.from_registration(dto)
            enc_row = await self._mapper.encrypt_dto(
                plain, VoterPersistEncryptedDTO, args, self.session
            )
            voter = voter_orm_from_persist_encrypted(enc_row)
            voter = await self.voter_repo.register_voter(self.session, voter)
            return await self._voter_orm_to_item(voter)
        except Exception:
            logger.exception("Failed to register voter", dto=dto)
            raise

    async def _encrypt_dto_for_creation(
        self,
        dto: RegisterVoterEncryptedDTO,
    ) -> RegisterVoterEncryptedDTO:
        """Encrypt the DTO for creation."""
        pass

    async def get_voter_by_id(self, voter_id: UUID) -> VoterItem:
        """Get a voter by their ID."""
        try:
            voter = await self.voter_repo.get_voter_by_id(self.session, voter_id)
            return await self._voter_orm_to_item(voter)
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
        return await self._voter_orm_to_item(updated)

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
