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
    VoterDTO,
    VoterBaseDTO,
)
from app.models.dto.address import AddressDTO, AddressBaseDTO
from app.models.schemas.voter import VoterItem, VerifyIdentityRequest, VerifyIdentityResponse
from app.repository.voter_repo import VoterRepository
from app.repository.address_repo import AddressRepository
from app.service.base.encryption_utils_mixin import (
    EncryptionUtilsMixin,
    prepare_voter_registration_plain_fields,
    orm_row_has_encrypted_fields,
    voter_orm_to_dto_unencrypted_row,
    address_orm_to_dto_unencrypted_row,
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
        address_repo: Optional[AddressRepository] = None,
    ):
        self.voter_repo = voter_repo
        self.address_repo = address_repo or AddressRepository()
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

    async def verify_voter_identity(
        self,
        request: VerifyIdentityRequest,
    ) -> VerifyIdentityResponse:
        """Verify a voter's identity by matching name and address fields.

        1. HMAC the submitted postcode to produce a search token.
        2. Query addresses by postcode_search_token.
        3. For each matched address, decrypt address + voter fields and compare.
        4. Return verified=True with voter_id on match, or verified=False.
        """
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            # Build postcode search token from the submitted postcode
            normalised_postcode = request.postcode.strip().upper()
            postcode_token = await self._mapper.create_search_token(
                normalised_postcode, args, self.session
            )

            # Find addresses matching this postcode
            candidate_addresses = await self.address_repo.get_addresses_by_postcode_token(
                self.session, postcode_token
            )

            if not candidate_addresses:
                return VerifyIdentityResponse(
                    verified=False,
                    voter_id=None,
                    message="No voter found matching the provided details.",
                )

            submitted_name = request.full_name.strip().lower()
            submitted_addr1 = request.address_line1.strip().lower()
            submitted_addr2 = (request.address_line2 or "").strip().lower()
            submitted_city = request.city.strip().lower()

            for address in candidate_addresses:
                # Decrypt address fields
                if orm_row_has_encrypted_fields(address, AddressBaseDTO):
                    addr_dto = await self._mapper.decrypt_model(
                        address, AddressDTO, args, self.session
                    )
                else:
                    addr_dto = address_orm_to_dto_unencrypted_row(address)

                # Compare address fields
                db_addr1 = (addr_dto.address_line1 or "").strip().lower()
                db_addr2 = (addr_dto.address_line2 or "").strip().lower()
                db_city = (addr_dto.town or "").strip().lower()

                if db_addr1 != submitted_addr1:
                    continue
                if db_addr2 != submitted_addr2:
                    continue
                if db_city != submitted_city:
                    continue

                # Address matches — now decrypt the voter and compare name
                voter = await self.voter_repo.get_voter_by_id(
                    self.session, address.voter_id
                )

                if orm_row_has_encrypted_fields(voter, VoterBaseDTO):
                    voter_dto = await self._mapper.decrypt_model(
                        voter, VoterDTO, args, self.session
                    )
                else:
                    voter_dto = voter_orm_to_dto_unencrypted_row(voter)

                db_full_name = f"{voter_dto.first_name or ''} {voter_dto.surname or ''}".strip().lower()

                if db_full_name == submitted_name:
                    return VerifyIdentityResponse(
                        verified=True,
                        voter_id=str(voter.id),
                        message="Identity verified successfully.",
                    )

            return VerifyIdentityResponse(
                verified=False,
                voter_id=None,
                message="No voter found matching the provided details.",
            )

        except Exception:
            logger.exception("Failed to verify voter identity")
            raise
