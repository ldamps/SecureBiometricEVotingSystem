# voter_service.py - Service layer for voter-related operations.

import uuid as uuid_module
import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.models.sqlalchemy.voter import Voter, VoterStatus
from app.models.dto.voter import (
    RegisterVoterPlainDTO,
    RegisterVoterEncryptedDTO,
    UpdateVoterPlainDTO,
    UpdateVoterEncryptedDTO,
    VoterDTO,
    VoterBaseDTO,
)
from app.models.schemas.voter import VoterItem
from app.models.base.sqlalchemy_base import EncryptedDBField
from app.repository.voter_repo import VoterRepository
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()


def _voter_row_has_encrypted_fields(voter: Voter) -> bool:
    """True if any column holds EncryptedDBField (needs DEK + decrypt)."""
    for name in VoterBaseDTO.__encrypted_fields__:
        if isinstance(getattr(voter, name, None), EncryptedDBField):
            return True
    return False


def _voter_orm_to_dto_unencrypted_row(voter: Voter) -> VoterDTO:
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

    return VoterDTO(
        id=voter.id,
        voter_status=voter.voter_status,
        registration_status=voter.registration_status,
        failed_auth_attempts=voter.failed_auth_attempts,
        national_insurance_number=enc_plain("national_insurance_number"),
        passport_number=enc_plain("passport_number"),
        passport_country=enc_plain("passport_country"),
        passport_expiry_date=enc_plain("passport_expiry_date"),
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
            dto = await self._mapper.decrypt_model(voter, VoterDTO, args, self.session)
        else:
            dto = _voter_orm_to_dto_unencrypted_row(voter)
        return dto.to_schema()

    def _prepare_registration_plain_fields(self, dto: RegisterVoterPlainDTO) -> dict:
        """Prepare plaintext fields for encryption during registration.

        Business logic (voter_reference generation, NI normalization, timestamps)
        lives here in the service, not in the DTO.
        """
        reg_status = str(dto.registration_status or "pending").lower()
        if reg_status.upper() in ("PENDING", "SUSPENDED", "ACTIVE"):
            reg_status = reg_status.lower()
        else:
            reg_status = "pending"

        ni = dto.national_insurance_number
        if not ni or not str(ni).strip():
            ni = f"NONE-{uuid_module.uuid4().hex}"
        else:
            ni = str(ni).strip()

        voter_ref = f"VR-{uuid_module.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        return dict(
            first_name=dto.first_name,
            surname=dto.surname,
            date_of_birth=dto.date_of_birth.isoformat() if dto.date_of_birth else None,
            email=dto.email,
            voter_reference=voter_ref,
            voter_status=reg_status,
            constituency_id=dto.consituency_id,
            registration_status=reg_status,
            failed_auth_attempts=0,
            registered_at=now,
            renew_by=dto.renew_by,
            national_insurance_number=ni,
            passport_number=(
                dto.passport_number.strip()
                if dto.passport_number and dto.passport_number.strip()
                else None
            ),
            passport_country=(
                dto.passport_country.strip()
                if dto.passport_country and dto.passport_country.strip()
                else None
            ),
            passport_expiry_date=(
                dto.passport_expiry_date.isoformat()
                if dto.passport_expiry_date
                else None
            ),
            previous_first_name=dto.previous_first_name,
            previous_surname=dto.previous_surname,
            locked_until=None,
        )

    async def register_voter(self, dto: RegisterVoterPlainDTO) -> VoterItem:
        """Create a new voter with encrypted JSONB fields and search tokens."""
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            plain_fields = self._prepare_registration_plain_fields(dto)

            # Build a temporary plain DTO for the encryption mapper
            from dataclasses import dataclass, fields as dc_fields

            @dataclass
            class _RegPlain(VoterBaseDTO):
                first_name: str = ""
                surname: str = ""
                date_of_birth: Optional[str] = None
                email: str = ""
                voter_reference: str = ""
                voter_status: str = ""
                constituency_id: Optional[UUID] = None
                registration_status: str = ""
                failed_auth_attempts: int = 0
                registered_at: Optional[datetime] = None
                renew_by: Optional[datetime] = None
                national_insurance_number: Optional[str] = None
                passport_number: Optional[str] = None
                passport_country: Optional[str] = None
                passport_expiry_date: Optional[str] = None
                previous_first_name: Optional[str] = None
                previous_surname: Optional[str] = None
                locked_until: Optional[datetime] = None

            plain = _RegPlain(**plain_fields)
            enc_row = await self._mapper.encrypt_dto(
                plain, RegisterVoterEncryptedDTO, args, self.session
            )
            voter = enc_row.to_model()
            voter = await self.voter_repo.register_voter(self.session, voter)
            return await self._voter_orm_to_item(voter)
        except Exception:
            logger.exception("Failed to register voter", dto=dto)
            raise

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
