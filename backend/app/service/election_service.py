# election_service.py - Service layer for election-related operations.

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.models.dto.election import (
    CreateElectionPlainDTO,
    CreateElectionEncryptedDTO,
    UpdateElectionPlainDTO,
    ElectionDTO,
)
from app.models.schemas.election import ElectionItem
from app.repository.election_repo import ElectionRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.keys_manager_service import KeysManagerService
from app.service.encryption_mapper_service import EncryptionMapperService
from app.repository.audit_log_repo import AuditLogRepository
from app.models.sqlalchemy.audit_log import AuditLog

logger = structlog.get_logger()


class ElectionService(EncryptionUtilsMixin):
    """Service layer for election-related operations."""

    def __init__(
        self,
        election_repo: ElectionRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
        audit_log_repo: AuditLogRepository | None = None,
    ):
        self.election_repo = election_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper
        self._audit_log_repo = audit_log_repo or AuditLogRepository()

    async def create_election(self, dto: CreateElectionPlainDTO) -> ElectionItem:
        """Create a new election."""
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            enc_row = await self._mapper.encrypt_dto(
                dto, CreateElectionEncryptedDTO, args, self.session
            )
            election = enc_row.to_model()
            election = await self.election_repo.create_election(self.session, election)

            election_dto = await self._mapper.decrypt_model(
                election, ElectionDTO, args, self.session
            )

            # Audit: election created
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="ELECTION_CREATED",
                    action="CREATE",
                    summary=f"Election '{dto.title}' created",
                    resource_type="election",
                    resource_id=election.id,
                    election_id=election.id,
                    actor_type="OFFICIAL",
                    actor_id=dto.created_by if hasattr(dto, "created_by") else None,
                ),
            )

            return election_dto.to_schema()

        except Exception:
            logger.exception("Failed to create election", dto=dto)
            raise

    async def get_election_by_id(self, election_id: UUID) -> ElectionItem:
        """Get an election by its ID."""
        try:
            election = await self.election_repo.get_election_by_id(self.session, election_id)
            return await self.election_model_to_schema_item(election, self.session)

        except Exception:
            logger.exception("Failed to get election by ID", election_id=election_id)
            raise

    async def get_all_elections(self) -> List[ElectionItem]:
        """Get all elections."""
        try:
            elections = await self.election_repo.get_all_elections(self.session)
            return [
                await self.election_model_to_schema_item(e, self.session)
                for e in elections
            ]

        except Exception:
            logger.exception("Failed to get all elections")
            raise

    async def update_election(
        self,
        election_id: UUID,
        dto: UpdateElectionPlainDTO,
    ) -> ElectionItem:
        """Update an election's mutable fields (status, voting_opens, voting_closes)."""
        try:
            updated = await self.election_repo.update_election(
                self.session, election_id, dto
            )

            # Audit: election updated
            summary = f"Election {election_id} updated"
            event_type = "ELECTION_UPDATED"
            if hasattr(dto, "status") and dto.status is not None:
                event_type = "ELECTION_STATUS_CHANGED"
                summary = f"Election {election_id} status changed to {dto.status}"

            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type=event_type,
                    action="UPDATE",
                    summary=summary,
                    resource_type="election",
                    resource_id=election_id,
                    election_id=election_id,
                    actor_type="OFFICIAL",
                ),
            )

            return await self.election_model_to_schema_item(updated, self.session)

        except Exception:
            logger.exception("Failed to update election", election_id=election_id)
            raise
