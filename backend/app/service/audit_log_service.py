# audit_log_service.py - Service layer for audit log operations.

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dto.audit_log import AuditLogDTO, CreateAuditLogDTO
from app.models.schemas.audit_log import AuditLogItem
from app.models.sqlalchemy.audit_log import AuditLog
from app.repository.audit_log_repo import AuditLogRepository
from app.service.base.encryption_utils_mixin import audit_log_orm_to_dto_unencrypted_row

logger = structlog.get_logger()


class AuditLogService:
    """Service layer for audit log operations.

    Provides both write (log_event) and read (query) capabilities.
    Audit logs are immutable — no update or delete operations.
    """

    def __init__(
        self,
        audit_log_repo: AuditLogRepository,
        session: AsyncSession,
    ):
        self.audit_log_repo = audit_log_repo
        self.session = session

    # ── Write ──

    async def log_event(self, dto: CreateAuditLogDTO) -> AuditLogItem:
        """Record an audit event."""
        try:
            now = datetime.now(timezone.utc)
            entry = AuditLog(
                event_type=dto.event_type,
                action=dto.action,
                summary=dto.summary,
                actor_id=dto.actor_id,
                actor_type=dto.actor_type,
                resource_type=dto.resource_type,
                resource_id=dto.resource_id,
                election_id=dto.election_id,
                ip_address=dto.ip_address,
                event_metadata=dto.event_metadata,
                created_at=now,
            )
            entry = await self.audit_log_repo.create_audit_log(self.session, entry)
            return audit_log_orm_to_dto_unencrypted_row(entry).to_schema()
        except Exception:
            logger.exception("Failed to log audit event")
            raise

    # ── Read ──

    async def get_audit_log_by_id(self, audit_id: UUID) -> AuditLogItem:
        """Get a single audit log entry by ID."""
        try:
            entry = await self.audit_log_repo.get_audit_log_by_id(self.session, audit_id)
            return audit_log_orm_to_dto_unencrypted_row(entry).to_schema()
        except Exception:
            logger.exception("Failed to get audit log", audit_id=audit_id)
            raise

    async def get_audit_logs_by_election(self, election_id: UUID) -> List[AuditLogItem]:
        """Get all audit log entries scoped to an election."""
        try:
            entries = await self.audit_log_repo.get_audit_logs_by_election(
                self.session, election_id,
            )
            return [audit_log_orm_to_dto_unencrypted_row(e).to_schema() for e in entries]
        except Exception:
            logger.exception("Failed to get audit logs by election", election_id=election_id)
            raise

    async def get_audit_logs_by_actor(self, actor_id: UUID) -> List[AuditLogItem]:
        """Get all audit log entries for a specific actor."""
        try:
            entries = await self.audit_log_repo.get_audit_logs_by_actor(
                self.session, actor_id,
            )
            return [audit_log_orm_to_dto_unencrypted_row(e).to_schema() for e in entries]
        except Exception:
            logger.exception("Failed to get audit logs by actor", actor_id=actor_id)
            raise

    async def get_audit_logs_by_actor_type(self, actor_type: str) -> List[AuditLogItem]:
        """Get all audit log entries for a specific actor type (OFFICIAL, VOTER, SYSTEM)."""
        try:
            entries = await self.audit_log_repo.get_audit_logs_by_actor_type(
                self.session, actor_type,
            )
            return [audit_log_orm_to_dto_unencrypted_row(e).to_schema() for e in entries]
        except Exception:
            logger.exception("Failed to get audit logs by actor type", actor_type=actor_type)
            raise

    async def get_audit_logs_by_resource(
        self, resource_type: str, resource_id: UUID,
    ) -> List[AuditLogItem]:
        """Get all audit log entries for a specific resource."""
        try:
            entries = await self.audit_log_repo.get_audit_logs_by_resource(
                self.session, resource_type, resource_id,
            )
            return [audit_log_orm_to_dto_unencrypted_row(e).to_schema() for e in entries]
        except Exception:
            logger.exception(
                "Failed to get audit logs by resource",
                resource_type=resource_type,
                resource_id=resource_id,
            )
            raise

    async def get_audit_logs_by_event_type(self, event_type: str) -> List[AuditLogItem]:
        """Get all audit log entries of a specific event type."""
        try:
            entries = await self.audit_log_repo.get_audit_logs_by_event_type(
                self.session, event_type,
            )
            return [audit_log_orm_to_dto_unencrypted_row(e).to_schema() for e in entries]
        except Exception:
            logger.exception("Failed to get audit logs by event type", event_type=event_type)
            raise

    async def get_audit_logs_by_date_range(
        self,
        start: datetime,
        end: datetime,
        election_id: Optional[UUID] = None,
    ) -> List[AuditLogItem]:
        """Get audit log entries within a date range."""
        try:
            entries = await self.audit_log_repo.get_audit_logs_by_date_range(
                self.session, start, end, election_id,
            )
            return [audit_log_orm_to_dto_unencrypted_row(e).to_schema() for e in entries]
        except Exception:
            logger.exception("Failed to get audit logs by date range")
            raise

    async def get_recent_audit_logs(self, limit: int = 50) -> List[AuditLogItem]:
        """Get the most recent audit log entries."""
        try:
            entries = await self.audit_log_repo.get_recent_audit_logs(self.session, limit)
            return [audit_log_orm_to_dto_unencrypted_row(e).to_schema() for e in entries]
        except Exception:
            logger.exception("Failed to get recent audit logs")
            raise
