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
from app.application.core.exceptions import ValidationError
from app.models.schemas.referendum import ReferendumItem
from app.models.sqlalchemy.audit_log import AuditLog
from app.models.sqlalchemy.referendum import ReferendumStatus
from app.repository.audit_log_repo import AuditLogRepository
from app.repository.referendum_repo import ReferendumRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.keys_manager_service import KeysManagerService
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.voting_schedule_status_sync import sync_referendum_status_with_voting_schedule

logger = structlog.get_logger()

_VALID_REFERENDUM_STATUS_TRANSITIONS: dict[str, set[str]] = {
    ReferendumStatus.OPEN.value: {
        ReferendumStatus.CLOSED.value,
        ReferendumStatus.CANCELLED.value,
    },
    ReferendumStatus.CLOSED.value: {ReferendumStatus.CANCELLED.value},
}


class ReferendumService(EncryptionUtilsMixin):
    """Service layer for referendum-related operations."""

    def __init__(
        self,
        referendum_repo: ReferendumRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
        audit_log_repo: AuditLogRepository | None = None,
    ):
        self.referendum_repo = referendum_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper
        self._audit_log_repo = audit_log_repo or AuditLogRepository()

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
            referendum = await sync_referendum_status_with_voting_schedule(
                self.session, self.referendum_repo, referendum
            )

            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="REFERENDUM_CREATED",
                    action="CREATE",
                    summary=f"Referendum '{dto.title}' created",
                    resource_type="referendum",
                    resource_id=referendum.id,
                    actor_type="OFFICIAL",
                ),
            )

            return await self.referendum_model_to_schema_item(referendum, self.session)
        except Exception:
            logger.exception("Failed to create referendum", dto=dto)
            raise

    async def get_referendum_by_id(self, referendum_id: UUID) -> ReferendumItem:
        """Get a referendum by its ID."""
        try:
            referendum = await self.referendum_repo.get_referendum_by_id(self.session, referendum_id)
            referendum = await sync_referendum_status_with_voting_schedule(
                self.session, self.referendum_repo, referendum
            )
            return await self.referendum_model_to_schema_item(referendum, self.session)
        except Exception:
            logger.exception("Failed to get referendum by ID", referendum_id=referendum_id)
            raise

    async def get_all_referendums(self) -> List[ReferendumItem]:
        """Get all referendums."""
        try:
            referendums = await self.referendum_repo.get_all_referendums(self.session)
            synced = []
            for r in referendums:
                synced.append(
                    await sync_referendum_status_with_voting_schedule(
                        self.session, self.referendum_repo, r
                    )
                )
            return [
                await self.referendum_model_to_schema_item(r, self.session)
                for r in synced
            ]
        except Exception:
            logger.exception("Failed to get all referendums")
            raise

    async def update_referendum(self, referendum_id: UUID, update_data: dict) -> ReferendumItem:
        """Update a referendum's mutable fields."""
        try:
            data = dict(update_data)
            if data.get("status") is not None:
                new_status = data["status"]
                if isinstance(new_status, ReferendumStatus):
                    new_status = new_status.value
                data["status"] = new_status
                current = await self.referendum_repo.get_referendum_by_id(
                    self.session, referendum_id
                )
                allowed = _VALID_REFERENDUM_STATUS_TRANSITIONS.get(current.status, set())
                if new_status not in allowed:
                    raise ValidationError(
                        f"Invalid referendum status transition: {current.status} -> {new_status}"
                    )

            updated = await self.referendum_repo.update_referendum(
                self.session, referendum_id, data
            )
            if "status" not in data:
                updated = await sync_referendum_status_with_voting_schedule(
                    self.session, self.referendum_repo, updated
                )

            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="REFERENDUM_UPDATED",
                    action="UPDATE",
                    summary=f"Referendum {referendum_id} updated",
                    resource_type="referendum",
                    resource_id=referendum_id,
                    actor_type="OFFICIAL",
                ),
            )

            return await self.referendum_model_to_schema_item(updated, self.session)
        except Exception:
            logger.exception("Failed to update referendum", referendum_id=referendum_id)
            raise
