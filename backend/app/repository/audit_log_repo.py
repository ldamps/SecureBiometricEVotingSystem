# audit_log_repo.py - Repository layer for audit log operations.

from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import NotFoundError
from app.models.sqlalchemy.audit_log import AuditLog

logger = structlog.get_logger()


class AuditLogRepository:
    """Audit log repository — append-only reads and writes."""

    def __init__(self) -> None:
        self._model = AuditLog

    # ── Write ──

    async def create_audit_log(
        self, session: AsyncSession, entry: AuditLog,
    ) -> AuditLog:
        """Persist a new audit log entry."""
        try:
            session.add(entry)
            await session.flush()
            logger.info("Audit log created", audit_id=entry.id, event_type=entry.event_type)
            return entry
        except Exception:
            logger.exception("Failed to create audit log entry")
            raise

    # ── Read ──

    async def get_audit_log_by_id(
        self, session: AsyncSession, audit_id: UUID,
    ) -> AuditLog:
        """Get a single audit log entry by ID."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.id == audit_id)
            )
            entry = result.scalar_one_or_none()
            if not entry:
                raise NotFoundError("Audit log entry not found")
            return entry
        except Exception:
            logger.exception("Failed to get audit log", audit_id=audit_id)
            raise

    async def get_audit_logs_by_election(
        self, session: AsyncSession, election_id: UUID,
    ) -> list[AuditLog]:
        """Get all audit log entries scoped to an election."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.election_id == election_id)
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get audit logs by election", election_id=election_id)
            raise

    async def get_audit_logs_by_referendum(
        self, session: AsyncSession, referendum_id: UUID,
    ) -> list[AuditLog]:
        """Get all audit log entries scoped to a referendum."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.referendum_id == referendum_id)
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get audit logs by referendum", referendum_id=referendum_id)
            raise

    async def get_audit_logs_by_actor(
        self, session: AsyncSession, actor_id: UUID,
    ) -> list[AuditLog]:
        """Get all audit log entries for a specific actor."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.actor_id == actor_id)
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get audit logs by actor", actor_id=actor_id)
            raise

    async def get_audit_logs_by_actor_type(
        self, session: AsyncSession, actor_type: str,
    ) -> list[AuditLog]:
        """Get all audit log entries for a specific actor type (OFFICIAL, VOTER, SYSTEM)."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.actor_type == actor_type)
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get audit logs by actor type", actor_type=actor_type)
            raise

    async def get_audit_logs_by_resource(
        self, session: AsyncSession, resource_type: str, resource_id: UUID,
    ) -> list[AuditLog]:
        """Get all audit log entries for a specific resource."""
        try:
            result = await session.execute(
                select(self._model)
                .where(
                    self._model.resource_type == resource_type,
                    self._model.resource_id == resource_id,
                )
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception(
                "Failed to get audit logs by resource",
                resource_type=resource_type,
                resource_id=resource_id,
            )
            raise

    async def get_audit_logs_by_event_type(
        self, session: AsyncSession, event_type: str,
    ) -> list[AuditLog]:
        """Get all audit log entries of a specific event type."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.event_type == event_type)
                .order_by(self._model.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get audit logs by event type", event_type=event_type)
            raise

    async def get_audit_logs_by_date_range(
        self,
        session: AsyncSession,
        start: datetime,
        end: datetime,
        election_id: Optional[UUID] = None,
    ) -> list[AuditLog]:
        """Get audit log entries within a date range, optionally scoped to an election."""
        try:
            stmt = (
                select(self._model)
                .where(
                    self._model.created_at >= start,
                    self._model.created_at <= end,
                )
            )
            if election_id:
                stmt = stmt.where(self._model.election_id == election_id)
            stmt = stmt.order_by(self._model.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get audit logs by date range")
            raise

    async def get_recent_audit_logs(
        self, session: AsyncSession, limit: int = 50,
    ) -> list[AuditLog]:
        """Get the most recent audit log entries."""
        try:
            result = await session.execute(
                select(self._model)
                .order_by(self._model.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get recent audit logs")
            raise
