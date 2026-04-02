from __future__ import annotations

import uuid as uuid_module
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Optional, TypeVar

import structlog

from app.models.base.sqlalchemy_base import EncryptedDBField
from app.models.dto.audit_log import AuditLogBaseDTO, AuditLogDTO
from app.models.dto.address import AddressBaseDTO, AddressDTO
from app.models.dto.ballot import BallotTokenBaseDTO, BallotTokenDTO
from app.models.dto.candidate import CandidateBaseDTO, CandidateDTO
from app.models.dto.election import ElectionBaseDTO, ElectionDTO
from app.models.dto.error_report import ErrorReportBaseDTO, ErrorReportDTO
from app.models.dto.investigation import InvestigationBaseDTO, InvestigationDTO
from app.models.dto.party import PartyBaseDTO, PartyDTO
from app.models.dto.referendum import ReferendumBaseDTO, ReferendumDTO
from app.models.dto.official import OfficialBaseDTO, OfficialDTO
from app.models.dto.voter import RegisterVoterPlainDTO, VoterBaseDTO, VoterDTO
from app.models.dto.voter_passport import VoterPassportBaseDTO, VoterPassportDTO
from app.models.schemas.audit_log import AuditLogItem
from app.models.schemas.address import AddressItem
from app.models.schemas.ballot_token import BallotTokenItem
from app.models.schemas.candidate import CandidateItem
from app.models.schemas.election import ElectionItem
from app.models.schemas.error_report import ErrorReportItem
from app.models.schemas.investigation import InvestigationItem
from app.models.schemas.official import OfficialItem
from app.models.schemas.party import PartyItem
from app.models.schemas.referendum import ReferendumItem
from app.models.schemas.voter import VoterItem
from app.models.schemas.voter_passport import VoterPassportItem
from app.models.sqlalchemy.audit_log import AuditLog
from app.models.sqlalchemy.address import Address, AddressStatus, AddressType
from app.models.sqlalchemy.ballot_token import BallotToken
from app.models.sqlalchemy.candidate import Candidate
from app.models.sqlalchemy.election import Election
from app.models.sqlalchemy.election_official import ElectionOfficial
from app.models.sqlalchemy.error_report import ErrorReport
from app.models.sqlalchemy.investigation import Investigation
from app.models.sqlalchemy.party import Party
from app.models.sqlalchemy.referendum import Referendum
from app.models.sqlalchemy.voter import Voter
from app.models.sqlalchemy.voter_passport import VoterPassport
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.encryption_service import EncryptionArgs
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()

PlainDTO = TypeVar("PlainDTO")


def orm_row_has_encrypted_fields(orm_model: Any, base_dto_class: type) -> bool:
    """True if any column listed on *base_dto_class* holds EncryptedDBField (needs DEK + decrypt)."""
    for name in base_dto_class.__encrypted_fields__:
        if isinstance(getattr(orm_model, name, None), EncryptedDBField):
            return True
    return False


def prepare_voter_registration_plain_fields(dto: RegisterVoterPlainDTO) -> dict:
    """Prepare plaintext fields for encryption during voter registration.

    Business logic (voter_reference generation, NI normalization, timestamps)
    lives here, not in the DTO.
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
        date_of_birth=dto.date_of_birth
        if isinstance(dto.date_of_birth, str)
        else (dto.date_of_birth.isoformat() if dto.date_of_birth else None),
        email=dto.email,
        voter_reference=voter_ref,
        voter_status=reg_status,
        constituency_id=dto.constituency_id,
        registration_status=reg_status,
        failed_auth_attempts=0,
        registered_at=now,
        renew_by=dto.renew_by,
        national_insurance_number=ni,
        nationality_category=dto.nationality_category,
        immigration_status=dto.immigration_status,
        immigration_status_expiry=dto.immigration_status_expiry,
        previous_first_name=dto.previous_first_name,
        previous_surname=dto.previous_surname,
        locked_until=None,
    )


def voter_orm_to_dto_unencrypted_row(voter: Voter) -> VoterDTO:
    """Map voter ORM row when encrypted JSONB columns are NULL (e.g. post-migration)."""

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
        first_name=enc_plain("first_name"),
        surname=enc_plain("surname"),
        previous_first_name=enc_plain("previous_first_name"),
        previous_surname=enc_plain("previous_surname"),
        date_of_birth=enc_plain("date_of_birth"),
        email=enc_plain("email"),
        voter_reference=enc_plain("voter_reference"),
        constituency_id=voter.constituency_id,
        nationality_category=voter.nationality_category,
        immigration_status=voter.immigration_status,
        immigration_status_expiry=voter.immigration_status_expiry,
        locked_until=voter.locked_until,
        registered_at=voter.registered_at,
        renew_by=voter.renew_by,
    )


def passport_orm_to_dto_unencrypted_row(passport: VoterPassport) -> VoterPassportDTO:
    """Map passport ORM row when encrypted JSONB columns are NULL (e.g. post-migration)."""

    def enc_plain(name: str) -> Optional[str]:
        v = getattr(passport, name, None)
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, (bytes, bytearray)):
            return v.decode("utf-8", errors="replace") if v else None
        return None

    return VoterPassportDTO(
        id=passport.id,
        voter_id=passport.voter_id,
        passport_number=enc_plain("passport_number"),
        issuing_country=enc_plain("issuing_country"),
        expiry_date=enc_plain("expiry_date"),
        is_primary=passport.is_primary,
        created_at=passport.created_at,
        updated_at=passport.updated_at,
    )


def _address_enum_value(v: object | None) -> str | None:
    if v is None:
        return None
    return v.value if isinstance(v, (AddressType, AddressStatus)) else str(v)


def address_orm_to_dto_unencrypted_row(address: Address) -> AddressDTO:
    """Map address ORM row when encrypted JSONB columns are NULL (e.g. post-migration)."""

    def enc_plain(name: str) -> Optional[str]:
        val = getattr(address, name, None)
        if val is None:
            return None
        if isinstance(val, str):
            return val
        if isinstance(val, (bytes, bytearray)):
            return val.decode("utf-8", errors="replace") if val else None
        return None

    return AddressDTO(
        id=address.id,
        voter_id=address.voter_id,
        address_type=_address_enum_value(address.address_type),
        address_line1=enc_plain("address_line1"),
        address_line2=enc_plain("address_line2"),
        town=enc_plain("town"),
        postcode=enc_plain("postcode"),
        county=enc_plain("county"),
        country=enc_plain("country"),
        address_status=_address_enum_value(address.address_status),
        renew_by=address.renew_by,
        created_at=address.created_at,
        updated_at=address.updated_at,
    )


def candidate_orm_to_dto_unencrypted_row(candidate: Candidate) -> CandidateDTO:
    """Map candidate ORM row to a plaintext DTO (candidates have no encrypted fields)."""
    return CandidateDTO(
        id=candidate.id,
        election_id=candidate.election_id,
        constituency_id=candidate.constituency_id,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        party_id=candidate.party_id,
        is_active=candidate.is_active,
    )


def party_orm_to_dto_unencrypted_row(party: Party) -> PartyDTO:
    """Map party ORM row to a plaintext DTO (parties have no encrypted fields)."""
    return PartyDTO(
        id=party.id,
        party_name=party.party_name,
        abbreviation=party.abbreviation,
        is_active=party.is_active,
        created_at=party.created_at,
        updated_at=party.updated_at,
    )


def referendum_orm_to_dto_unencrypted_row(referendum: Referendum) -> ReferendumDTO:
    """Map referendum ORM row to a plaintext DTO (referendums have no encrypted fields)."""
    return ReferendumDTO(
        id=referendum.id,
        title=referendum.title,
        question=referendum.question,
        description=referendum.description,
        scope=referendum.scope,
        status=referendum.status,
        voting_opens=referendum.voting_opens,
        voting_closes=referendum.voting_closes,
        is_active=referendum.is_active,
    )


def official_orm_to_dto_unencrypted_row(official: ElectionOfficial) -> OfficialDTO:
    """Map official ORM row to a plaintext DTO (EncryptedBytes decoded to strings)."""

    def enc_plain(name: str) -> Optional[str]:
        v = getattr(official, name, None)
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, (bytes, bytearray)):
            return v.decode("utf-8", errors="replace") if v else None
        return None

    return OfficialDTO(
        id=official.id,
        username=official.username,
        first_name=enc_plain("first_name"),
        last_name=enc_plain("last_name"),
        email=enc_plain("email_hash"),
        role=official.role,
        is_active=official.is_active,
        must_reset_password=official.must_reset_password,
        failed_login_attempts=official.failed_login_attempts,
        created_by=official.created_by,
        last_login_at=official.last_login_at,
        locked_until=official.locked_until,
    )


def error_report_orm_to_dto_unencrypted_row(report: ErrorReport) -> ErrorReportDTO:
    """Map error report ORM row to a plaintext DTO (no encrypted fields)."""
    return ErrorReportDTO(
        id=report.id,
        election_id=report.election_id,
        reported_by=report.reported_by,
        title=report.title,
        description=report.description,
        severity=report.severity,
        reported_at=report.reported_at,
    )


def investigation_orm_to_dto_unencrypted_row(inv: Investigation) -> InvestigationDTO:
    """Map investigation ORM row to a plaintext DTO (no encrypted fields)."""
    return InvestigationDTO(
        id=inv.id,
        error_id=inv.error_id,
        election_id=inv.election_id,
        raised_by=inv.raised_by,
        title=inv.title,
        description=inv.description,
        severity=inv.severity,
        status=inv.status,
        category=inv.category,
        assigned_to=inv.assigned_to,
        notes=inv.notes,
        resolved_by=inv.resolved_by,
        raised_at=inv.raised_at,
        resolved_at=inv.resolved_at,
    )


def audit_log_orm_to_dto_unencrypted_row(entry: AuditLog) -> AuditLogDTO:
    """Map audit log ORM row to a plaintext DTO (no encrypted fields)."""
    return AuditLogDTO(
        id=entry.id,
        event_type=entry.event_type,
        action=entry.action,
        summary=entry.summary,
        actor_id=entry.actor_id,
        actor_type=entry.actor_type,
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        election_id=entry.election_id,
        event_metadata=entry.event_metadata,
        created_at=entry.created_at,
    )


def election_orm_to_dto_unencrypted_row(election: Election) -> ElectionDTO:
    """Map election ORM row to a plaintext DTO (elections have no encrypted fields)."""
    return ElectionDTO(
        id=election.id,
        title=election.title,
        election_type=election.election_type,
        scope=election.scope,
        allocation_method=election.allocation_method,
        status=election.status,
        voting_opens=election.voting_opens,
        voting_closes=election.voting_closes,
        created_by=election.created_by,
    )


class EncryptionUtilsMixin:
    """Mixin for domain services that need to encrypt/decrypt field data.

    Usage
    -----
    Inherit alongside your service class and inject the required dependencies:

        class VoterService(EncryptionUtilsMixin):
            def __init__(self, ..., mapper: EncryptionMapperService,
                         keys_manager: KeysManagerService):
                self._mapper = mapper
                self._keys_manager = keys_manager

    The mixin resolves the encryption context (system-level or org-scoped)
    and delegates to EncryptionMapperService for the actual crypto work.

    Typical create flow
    -------------------
        args  = await self._build_args(session, org=org)
        enc   = await self._encrypt_dto(plain_dto, EncryptedDTO, args, session)
        model = await repo.create(session, enc)
        return await self._decrypt_and_return(model, PlainDTO, args, session)

    Typical read flow
    -----------------
        model = await repo.get(session, id)
        return await self._decrypt_and_return(model, PlainDTO, args, session)
    """

    # Subclasses must assign these in their __init__
    _mapper: EncryptionMapperService
    _keys_manager: KeysManagerService

    # ------------------------------------------------------------------ #
    #  Context resolution                                                  #
    # ------------------------------------------------------------------ #

    async def _build_args(
        self,
        session: Any,
        org: Optional[Any] = None,
        system_key: bool = False,
    ) -> EncryptionArgs:
        """Resolve the EncryptionArgs for the current operation.

        Pass *org* (an object with a `.id` attribute or a raw UUID) for
        organisation-scoped encryption, or *system_key=True* for system-level
        keys (e.g. admin users, platform-wide data).
        """
        org_id = None
        if org is not None:
            org_id = org.id if hasattr(org, "id") else org
        elif system_key:
            org_id = None  # system keys use org_id=NULL

        return await self._keys_manager.build_encryption_args(session, org_id=org_id)

    # ------------------------------------------------------------------ #
    #  DTO encryption / decryption                                         #
    # ------------------------------------------------------------------ #

    async def _encrypt_dto(
        self,
        plain_dto: Any,
        encrypted_dto_class: type,
        args: EncryptionArgs,
        session: Any,
    ) -> Any:
        """Encrypt all ``__encrypted_fields__`` on *plain_dto*.

        Returns an instance of *encrypted_dto_class* ready for persistence.
        """
        return await self._mapper.encrypt_dto(plain_dto, encrypted_dto_class, args, session)

    async def _decrypt_model(
        self,
        orm_model: Any,
        plain_dto_class: type,
        args: EncryptionArgs,
        session: Any,
    ) -> Any:
        """Decrypt all encrypted fields on *orm_model*, returning a plain DTO."""
        return await self._mapper.decrypt_model(orm_model, plain_dto_class, args, session)

    async def _decrypt_and_return(
        self,
        orm_model: Any,
        plain_dto_class: type,
        args: EncryptionArgs,
        session: Any,
    ) -> Any:
        """Decrypt *orm_model* into a plain DTO and call ``.to_schema()`` on it.

        Convenience wrapper for the common pattern:
            plain = await self._decrypt_model(model, DTO, args, session)
            return plain.to_schema()
        """
        plain = await self._decrypt_model(orm_model, plain_dto_class, args, session)
        return plain.to_schema()

    # ------------------------------------------------------------------ #
    #  Search tokens                                                       #
    # ------------------------------------------------------------------ #

    async def _get_search_token(
        self,
        value: str,
        args: EncryptionArgs,
        session: Any,
    ) -> str:
        """Return an HMAC-SHA256 blind index for querying an encrypted field."""
        return await self._mapper.create_search_token(value, args, session)

    # ------------------------------------------------------------------ #
    #  Stream (blob) encrypt / decrypt                                     #
    # ------------------------------------------------------------------ #

    async def _encrypt_stream(
        self,
        data: bytes,
        args: EncryptionArgs,
        session: Any,
    ) -> bytes:
        """Encrypt a binary blob using the STORAGE DEK."""
        return await self._mapper.encrypt_stream(data, args, session)

    async def _decrypt_stream(
        self,
        data: bytes,
        args: EncryptionArgs,
        session: Any,
    ) -> bytes:
        """Decrypt a blob produced by _encrypt_stream."""
        return await self._mapper.decrypt_stream(data, args, session)

    # ------------------------------------------------------------------ #
    #  ORM row → schema (encrypted JSONB vs legacy/plain columns)        #
    # ------------------------------------------------------------------ #

    async def _orm_to_schema_item(
        self,
        orm_model: Any,
        *,
        plain_dto_class: type,
        base_dto_class: type,
        session: Any,
        map_unencrypted_row: Callable[[Any], Any],
        org: Any = None,
        system_key: bool = False,
    ) -> Any:
        """Decrypt *orm_model* to a plain DTO when encrypted fields are present; else map legacy row.

        *base_dto_class* must define ``__encrypted_fields__`` (same as the plain DTO hierarchy).
        *map_unencrypted_row* builds the plain DTO when columns hold plaintext (e.g. post-migration).
        """
        if orm_row_has_encrypted_fields(orm_model, base_dto_class):
            args = await self._build_args(session, org=org, system_key=system_key)
            dto = await self._decrypt_model(orm_model, plain_dto_class, args, session)
        else:
            dto = map_unencrypted_row(orm_model)
        return dto.to_schema()

    async def voter_model_to_schema_item(self, voter: Voter, session: Any) -> VoterItem:
        """Voter ORM model → API schema (decrypt when JSONB present, else legacy plaintext columns)."""
        return await self._orm_to_schema_item(
            voter,
            plain_dto_class=VoterDTO,
            base_dto_class=VoterBaseDTO,
            session=session,
            map_unencrypted_row=voter_orm_to_dto_unencrypted_row,
        )

    async def address_model_to_schema_item(self, address: Address, session: Any) -> AddressItem:
        """Address ORM model → API schema (decrypt when JSONB present, else legacy plaintext columns)."""
        return await self._orm_to_schema_item(
            address,
            plain_dto_class=AddressDTO,
            base_dto_class=AddressBaseDTO,
            session=session,
            map_unencrypted_row=address_orm_to_dto_unencrypted_row,
        )

    async def passport_model_to_schema_item(self, passport: VoterPassport, session: Any) -> VoterPassportItem:
        """VoterPassport ORM model → API schema (decrypt when JSONB present, else legacy plaintext columns)."""
        return await self._orm_to_schema_item(
            passport,
            plain_dto_class=VoterPassportDTO,
            base_dto_class=VoterPassportBaseDTO,
            session=session,
            map_unencrypted_row=passport_orm_to_dto_unencrypted_row,
        )

    async def election_model_to_schema_item(self, election: Election, session: Any) -> ElectionItem:
        """Election ORM model → API schema (elections have no encrypted fields)."""
        return await self._orm_to_schema_item(
            election,
            plain_dto_class=ElectionDTO,
            base_dto_class=ElectionBaseDTO,
            session=session,
            map_unencrypted_row=election_orm_to_dto_unencrypted_row,
        )

    async def candidate_model_to_schema_item(self, candidate: Candidate, session: Any) -> CandidateItem:
        """Candidate ORM model → API schema (candidates have no encrypted fields)."""
        return await self._orm_to_schema_item(
            candidate,
            plain_dto_class=CandidateDTO,
            base_dto_class=CandidateBaseDTO,
            session=session,
            map_unencrypted_row=candidate_orm_to_dto_unencrypted_row,
        )

    async def party_model_to_schema_item(self, party: Party, session: Any) -> PartyItem:
        """Party ORM model → API schema (parties have no encrypted fields)."""
        return await self._orm_to_schema_item(
            party,
            plain_dto_class=PartyDTO,
            base_dto_class=PartyBaseDTO,
            session=session,
            map_unencrypted_row=party_orm_to_dto_unencrypted_row,
        )

    async def referendum_model_to_schema_item(self, referendum: Referendum, session: Any) -> ReferendumItem:
        """Referendum ORM model → API schema (referendums have no encrypted fields)."""
        return await self._orm_to_schema_item(
            referendum,
            plain_dto_class=ReferendumDTO,
            base_dto_class=ReferendumBaseDTO,
            session=session,
            map_unencrypted_row=referendum_orm_to_dto_unencrypted_row,
        )

    async def official_model_to_schema_item(self, official: ElectionOfficial, session: Any) -> OfficialItem:
        """ElectionOfficial ORM model → API schema (EncryptedBytes at column level)."""
        return await self._orm_to_schema_item(
            official,
            plain_dto_class=OfficialDTO,
            base_dto_class=OfficialBaseDTO,
            session=session,
            map_unencrypted_row=official_orm_to_dto_unencrypted_row,
        )

    async def error_report_model_to_schema_item(self, report: ErrorReport, session: Any) -> ErrorReportItem:
        """ErrorReport ORM model → API schema (no encrypted fields)."""
        return await self._orm_to_schema_item(
            report,
            plain_dto_class=ErrorReportDTO,
            base_dto_class=ErrorReportBaseDTO,
            session=session,
            map_unencrypted_row=error_report_orm_to_dto_unencrypted_row,
        )

    async def investigation_model_to_schema_item(self, inv: Investigation, session: Any) -> InvestigationItem:
        """Investigation ORM model → API schema (no encrypted fields)."""
        return await self._orm_to_schema_item(
            inv,
            plain_dto_class=InvestigationDTO,
            base_dto_class=InvestigationBaseDTO,
            session=session,
            map_unencrypted_row=investigation_orm_to_dto_unencrypted_row,
        )
