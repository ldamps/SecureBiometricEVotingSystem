# official_service.py - Service layer for election official operations.

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
    ):
        self.official_repo = official_repo
        self.session = session

    # ── Create ──

    async def create_official(self, dto: CreateOfficialPlainDTO) -> OfficialItem:
        """Create a new election official.

        The official is created with ``must_reset_password=True`` so they
        must change their temporary password on first login.
        """
        try:
            # Check for duplicate username
            existing = await self.official_repo.get_official_by_username(
                self.session, dto.username,
            )
            if existing:
                raise ValidationError(f"Username '{dto.username}' is already taken")

            password_hash = _hash_password(dto.password)

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
        self, official_id: UUID, dto: UpdateOfficialPlainDTO,
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
            return official_orm_to_dto_unencrypted_row(updated).to_schema()

        except (ValidationError, NotFoundError):
            raise
        except Exception:
            logger.exception("Failed to update official", official_id=official_id)
            raise

    # ── Activate / Deactivate ──

    async def deactivate_official(self, official_id: UUID) -> OfficialItem:
        """Deactivate an election official (admin-only)."""
        try:
            updated = await self.official_repo.deactivate_official(
                self.session, official_id,
            )
            return official_orm_to_dto_unencrypted_row(updated).to_schema()
        except Exception:
            logger.exception("Failed to deactivate official", official_id=official_id)
            raise

    async def activate_official(self, official_id: UUID) -> OfficialItem:
        """Reactivate an election official (admin-only)."""
        try:
            updated = await self.official_repo.activate_official(
                self.session, official_id,
            )
            return official_orm_to_dto_unencrypted_row(updated).to_schema()
        except Exception:
            logger.exception("Failed to activate official", official_id=official_id)
            raise
