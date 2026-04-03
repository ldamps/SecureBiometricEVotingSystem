# voter_service.py - Service layer for voter-related operations.

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.application.core.exceptions import ValidationError
from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import (
    RegisterVoterPlainDTO,
    RegisterVoterEncryptedDTO,
    UpdateVoterPlainDTO,
    UpdateVoterEncryptedDTO,
    VoterDTO,
    VoterBaseDTO,
)
from app.models.dto.voter_passport import (
    CreateVoterPassportPlainDTO,
    CreateVoterPassportEncryptedDTO,
    VoterPassportDTO,
)
from app.models.dto.address import AddressDTO, AddressBaseDTO
from app.models.schemas.voter import VoterItem, VoterRegistrationRequest, VerifyIdentityRequest, VerifyIdentityResponse
from app.models.schemas.voter_passport import PassportEntry
from app.repository.voter_repo import VoterRepository
from app.repository.voter_passport_repo import VoterPassportRepository
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
from app.service.email_service import EmailService
from app.repository.audit_log_repo import AuditLogRepository
from app.repository.biometric_credentials_repo import BiometricCredentialsRepository
from app.models.sqlalchemy.audit_log import AuditLog
from app.models.sqlalchemy.voter import VoterStatus
from app.models.sqlalchemy.address import AddressStatus
from app.service.kyc_service import KYCService

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
        passport_repo: Optional[VoterPassportRepository] = None,
        email_service: Optional[EmailService] = None,
        audit_log_repo: Optional[AuditLogRepository] = None,
        kyc_service: Optional[KYCService] = None,
        biometric_credentials_repo: Optional[BiometricCredentialsRepository] = None,
    ):
        self.voter_repo = voter_repo
        self.address_repo = address_repo or AddressRepository()
        self.passport_repo = passport_repo or VoterPassportRepository()
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper
        self.voter = voter
        self._email_service = email_service
        self._audit_log_repo = audit_log_repo or AuditLogRepository()
        self._kyc_service = kyc_service or KYCService()
        self._biometric_credentials_repo = biometric_credentials_repo or BiometricCredentialsRepository()

    async def register_voter(
        self,
        dto: RegisterVoterPlainDTO,
        passport_entries: List[PassportEntry] | None = None,
        kyc_session_id: str | None = None,
    ) -> VoterItem:
        """Create a new voter with encrypted JSONB fields, search tokens, and passport entries.

        Requires a verified KYC session. The voter is created in PENDING status;
        they must complete address verification and biometric enrollment to become ACTIVE.
        """
        if not kyc_session_id:
            raise ValidationError("A verified KYC session ID is required to register.")

        # Validate KYC — session must be verified and data must match
        dob_str = None
        if dto.date_of_birth:
            from datetime import datetime as dt
            try:
                parsed = dt.fromisoformat(str(dto.date_of_birth).replace("Z", "+00:00"))
                dob_str = parsed.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass

        try:
            await self._kyc_service.validate_kyc_for_registration(
                session_id=kyc_session_id,
                first_name=dto.first_name,
                surname=dto.surname,
                date_of_birth=dob_str,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        # Enforce PENDING status — voter must complete all steps before activation
        dto.registration_status = "pending"
        dto.voter_status = VoterStatus.PENDING.value

        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            plain_fields = prepare_voter_registration_plain_fields(dto)
            plain = RegisterVoterPlainDTO(**plain_fields)

            enc_row = await self._mapper.encrypt_dto(
                plain, RegisterVoterEncryptedDTO, args, self.session
            )
            voter = enc_row.to_model()
            voter.kyc_session_id = kyc_session_id
            voter = await self.voter_repo.register_voter(self.session, voter)

            # Create passport entries if provided
            passport_schemas = []
            if passport_entries:
                for entry in passport_entries:
                    passport_plain = CreateVoterPassportPlainDTO(
                        voter_id=voter.id,
                        passport_number=entry.passport_number,
                        issuing_country=entry.issuing_country,
                        expiry_date=entry.expiry_date.isoformat() if entry.expiry_date else None,
                        is_primary=entry.is_primary,
                    )
                    passport_enc = await self._mapper.encrypt_dto(
                        passport_plain, CreateVoterPassportEncryptedDTO, args, self.session
                    )
                    passport_model = passport_enc.to_model()
                    passport_model = await self.passport_repo.create_passport(
                        self.session, passport_model
                    )
                    passport_dto = await self._mapper.decrypt_model(
                        passport_model, VoterPassportDTO, args, self.session
                    )
                    passport_schemas.append(passport_dto.to_schema())

            voter_item = await self.voter_model_to_schema_item(voter, self.session)
            voter_item.passports = passport_schemas

            # Audit: voter registered
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="VOTER_REGISTERED",
                    action="CREATE",
                    summary=f"Voter registered with reference {plain_fields['voter_reference']}",
                    resource_type="voter",
                    resource_id=voter.id,
                    actor_type="VOTER",
                    actor_id=voter.id,
                ),
            )

            # Send registration confirmation email (non-blocking)
            if self._email_service and dto.email:
                try:
                    self._email_service.send_registration_confirmation(dto.email)
                except Exception:
                    logger.warning(
                        "Failed to send registration confirmation email",
                        voter_id=str(voter.id),
                    )

            return voter_item
        except IntegrityError as exc:
            error_msg = str(exc.orig) if exc.orig else str(exc)
            if "kyc_session_id" in error_msg:
                raise ValidationError(
                    "This KYC verification session has already been used for a registration."
                ) from exc
            if "national_insurance_number_search_token" in error_msg:
                raise ValidationError(
                    "A voter with this national insurance number is already registered."
                ) from exc
            if "email_search_token" in error_msg:
                raise ValidationError(
                    "A voter with this email address is already registered."
                ) from exc
            raise ValidationError(
                "A voter with these details is already registered."
            ) from exc
        except (ValidationError,):
            raise
        except Exception:
            logger.exception("Failed to register voter", dto=dto)
            raise

    async def get_voter_by_id(self, voter_id: UUID) -> VoterItem:
        """Get a voter by their ID, including their passport entries."""
        try:
            voter = await self.voter_repo.get_voter_by_id(self.session, voter_id)
            voter_item = await self.voter_model_to_schema_item(voter, self.session)

            # Fetch and decrypt passport entries
            passports = await self.passport_repo.get_all_passports_by_voter_id(
                self.session, voter_id
            )
            if passports:
                voter_item.passports = [
                    await self.passport_model_to_schema_item(p, self.session)
                    for p in passports
                ]

            return voter_item
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

        # Audit: voter updated
        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="VOTER_UPDATED",
                action="UPDATE",
                summary=f"Voter {voter_id} details updated",
                resource_type="voter",
                resource_id=voter_id,
                actor_type="VOTER",
                actor_id=voter_id,
            ),
        )

        return await self.voter_model_to_schema_item(updated, self.session)

    async def check_voter_exists(self, voter_id: UUID) -> bool:
        """Check if a voter exists."""
        try:
            await self.voter_repo.get_voter_by_id(self.session, voter_id)
            return True
        except Exception:
            return False

    async def check_voter_locked(self, voter_id: UUID) -> bool:
        """Check if a voter is locked."""
        locked_until = await self.voter_repo.check_voter_locked(self.session, voter_id)
        if locked_until is None:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) < locked_until

    async def check_voter_renewal_needed(self, voter_id: UUID) -> bool:
        """Check if a voter's account needs to be renewed."""
        renew_by = await self.voter_repo.check_voter_renewal_needed(self.session, voter_id)
        if renew_by is None:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= renew_by

    async def activate_voter_if_ready(self, voter_id: UUID) -> bool:
        """Check if all registration steps are complete and activate the voter.

        Activation requires:
        1. Voter is currently in PENDING status
        2. At least one address with ACTIVE status
        3. At least one active biometric device credential

        Returns True if the voter was activated, False otherwise.
        """
        # Only activate PENDING voters
        voter = await self.voter_repo.get_voter_by_id(self.session, voter_id)
        if voter.voter_status != VoterStatus.PENDING.value:
            return False

        # Check for an ACTIVE address
        addresses = await self.address_repo.get_all_addresses_by_voter_id(
            self.session, voter_id
        )
        has_active_address = any(
            a.address_status == AddressStatus.ACTIVE for a in addresses
        )
        if not has_active_address:
            logger.info("Voter not ready: no active address", voter_id=str(voter_id))
            return False

        # Check for an active biometric credential
        credentials = await self._biometric_credentials_repo.list_by_voter(
            self.session, voter_id
        )
        has_active_credential = any(c.is_active for c in credentials)
        if not has_active_credential:
            logger.info("Voter not ready: no active biometric credential", voter_id=str(voter_id))
            return False

        # All steps complete — activate
        await self.voter_repo.update_voter_status(
            self.session,
            voter_id,
            voter_status=VoterStatus.ACTIVE.value,
            registration_status="approved",
        )

        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="VOTER_ACTIVATED",
                action="UPDATE",
                summary=f"Voter {voter_id} activated after completing all registration steps",
                resource_type="voter",
                resource_id=voter_id,
                actor_type="SYSTEM",
                actor_id=voter_id,
            ),
        )

        logger.info("Voter activated", voter_id=str(voter_id))
        return True

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
