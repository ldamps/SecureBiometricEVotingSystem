# official_service.py - Service layer for election official operations.

import secrets
import string
from typing import List, Optional
from uuid import UUID

import structlog
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import NotFoundError, ValidationError
from app.models.dto.official import (
    CreateOfficialPlainDTO,
    UpdateOfficialPlainDTO,
)
from app.models.schemas.official import OfficialItem
from app.models.sqlalchemy.election_official import ElectionOfficial, OfficialRole
from app.repository.official_repo import OfficialRepository
from app.service.base.encryption_utils_mixin import official_orm_to_dto_unencrypted_row
from app.service.email_service import EmailService
from app.repository.audit_log_repo import AuditLogRepository
from app.models.sqlalchemy.audit_log import AuditLog

logger = structlog.get_logger()

# Argon2id hasher — OWASP-recommended defaults:
#   time_cost=3, memory_cost=65536 (64 MiB), parallelism=4
_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def _hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Returns a PHC-format string containing algorithm, parameters,
    salt, and hash — all in one self-describing value.
    """
    return _ph.hash(password)


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against an Argon2id hash."""
    try:
        return _ph.verify(stored, password)
    except VerifyMismatchError:
        return False


class OfficialService:
    """Service layer for election official operations."""

    def __init__(
        self,
        official_repo: OfficialRepository,
        session: AsyncSession,
        audit_log_repo: AuditLogRepository | None = None,
        email_service: EmailService | None = None,
    ):
        self.official_repo = official_repo
        self.session = session
        self._audit_log_repo = audit_log_repo or AuditLogRepository()
        self._email_service = email_service

    # ── Create ──

    @staticmethod
    def _generate_temp_password(length: int = 16) -> str:
        """Generate a secure temporary password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        while True:
            pwd = "".join(secrets.choice(alphabet) for _ in range(length))
            # Ensure at least one of each required category
            if (any(c.islower() for c in pwd)
                    and any(c.isupper() for c in pwd)
                    and any(c.isdigit() for c in pwd)):
                return pwd

    async def create_official(self, dto: CreateOfficialPlainDTO) -> OfficialItem:
        """Create a new election official.

        If no password is provided, a secure temporary password is generated.
        The official is created with ``must_reset_password=True`` so they
        must change their temporary password on first login.
        A welcome email is sent with their credentials.
        """
        try:
            # Check for duplicate username
            existing = await self.official_repo.get_official_by_username(
                self.session, dto.username,
            )
            if existing:
                raise ValidationError(f"Username '{dto.username}' is already taken")

            # Generate temp password if none provided
            temp_password = dto.password if dto.password else self._generate_temp_password()
            password_hash = _hash_password(temp_password)

            official = ElectionOfficial(
                username=dto.username,
                first_name=dto.first_name.encode() if dto.first_name else None,
                last_name=dto.last_name.encode() if dto.last_name else None,
                email_hash=dto.email.encode() if dto.email else None,
                password_hash=password_hash,
                role=dto.role,
                is_active=True,
                must_reset_password=True,
                failed_login_attempts=0,
                created_by=dto.created_by,
            )

            official = await self.official_repo.create_official(self.session, official)

            # Audit: official created
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="OFFICIAL_CREATED",
                    action="CREATE",
                    summary=f"Election official '{dto.username}' created with role {dto.role}",
                    resource_type="official",
                    resource_id=official.id,
                    actor_type="OFFICIAL",
                    actor_id=dto.created_by,
                ),
            )

            # Send welcome email with credentials (non-blocking)
            if self._email_service and dto.email:
                try:
                    self._email_service.send_official_welcome(
                        to_email=dto.email,
                        first_name=dto.first_name or dto.username,
                        username=dto.username,
                        temporary_password=temp_password,
                    )
                except Exception:
                    logger.warning(
                        "Failed to send welcome email — official was still created",
                        username=dto.username,
                    )

            return official_orm_to_dto_unencrypted_row(official).to_schema()

        except (ValidationError, NotFoundError):
            raise
        except Exception:
            logger.exception("Failed to create official", username=dto.username)
            raise

    # ── Read ──

    async def get_official_by_id(self, official_id: UUID) -> OfficialItem:
        """Get an official by their ID."""
        try:
            official = await self.official_repo.get_official_by_id(
                self.session, official_id,
            )
            return official_orm_to_dto_unencrypted_row(official).to_schema()
        except Exception:
            logger.exception("Failed to get official", official_id=official_id)
            raise

    async def get_all_officials(self) -> List[OfficialItem]:
        """Get all officials."""
        try:
            officials = await self.official_repo.get_all_officials(self.session)
            return [official_orm_to_dto_unencrypted_row(o).to_schema() for o in officials]
        except Exception:
            logger.exception("Failed to get all officials")
            raise

    async def get_officials_by_role(self, role: str) -> List[OfficialItem]:
        """Get all officials with a given role (ADMIN or OFFICER)."""
        try:
            officials = await self.official_repo.get_officials_by_role(
                self.session, role,
            )
            return [official_orm_to_dto_unencrypted_row(o).to_schema() for o in officials]
        except Exception:
            logger.exception("Failed to get officials by role", role=role)
            raise

    # ── Update ──

    async def update_official(
        self,
        official_id: UUID,
        dto: UpdateOfficialPlainDTO,
        actor_id: UUID | None = None,
    ) -> OfficialItem:
        """Update an official's mutable fields."""
        try:
            update_data: dict = {}

            if dto.first_name is not None:
                update_data["first_name"] = dto.first_name.encode()
            if dto.last_name is not None:
                update_data["last_name"] = dto.last_name.encode()
            if dto.email is not None:
                update_data["email_hash"] = dto.email.encode()
            if dto.role is not None:
                update_data["role"] = dto.role
            if dto.is_active is not None:
                update_data["is_active"] = dto.is_active

            if not update_data:
                raise ValidationError("No fields to update")

            updated = await self.official_repo.update_official(
                self.session, official_id, update_data,
            )

            # Audit: official updated
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="OFFICIAL_UPDATED",
                    action="UPDATE",
                    summary=f"Election official {official_id} updated ({', '.join(update_data.keys())})",
                    resource_type="official",
                    resource_id=official_id,
                    actor_type="OFFICIAL",
                    actor_id=actor_id,
                ),
            )

            return official_orm_to_dto_unencrypted_row(updated).to_schema()

        except (ValidationError, NotFoundError):
            raise
        except Exception:
            logger.exception("Failed to update official", official_id=official_id)
            raise

    # ── Activate / Deactivate ──

    async def deactivate_official(
        self, official_id: UUID, actor_id: UUID | None = None,
    ) -> OfficialItem:
        """Deactivate an election official (admin-only)."""
        try:
            updated = await self.official_repo.deactivate_official(
                self.session, official_id,
            )

            # Audit: official deactivated
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="OFFICIAL_DEACTIVATED",
                    action="UPDATE",
                    summary=f"Election official {official_id} deactivated",
                    resource_type="official",
                    resource_id=official_id,
                    actor_type="OFFICIAL",
                    actor_id=actor_id,
                ),
            )

            return official_orm_to_dto_unencrypted_row(updated).to_schema()
        except Exception:
            logger.exception("Failed to deactivate official", official_id=official_id)
            raise

    async def activate_official(
        self, official_id: UUID, actor_id: UUID | None = None,
    ) -> OfficialItem:
        """Reactivate an election official (admin-only)."""
        try:
            updated = await self.official_repo.activate_official(
                self.session, official_id,
            )

            # Audit: official reactivated
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="OFFICIAL_ACTIVATED",
                    action="UPDATE",
                    summary=f"Election official {official_id} reactivated",
                    resource_type="official",
                    resource_id=official_id,
                    actor_type="OFFICIAL",
                    actor_id=actor_id,
                ),
            )

            return official_orm_to_dto_unencrypted_row(updated).to_schema()
        except Exception:
            logger.exception("Failed to activate official", official_id=official_id)
            raise
