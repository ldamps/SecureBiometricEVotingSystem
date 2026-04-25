# investigation_service.py - Service layer for investigation operations.

from datetime import datetime, timezone
from typing import List
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import ValidationError
from app.models.dto.investigation import UpdateInvestigationPlainDTO
from app.models.schemas.investigation import InvestigationItem
from app.models.sqlalchemy.investigation import Investigation
from app.repository.investigation_repo import InvestigationRepository
from app.service.base.encryption_utils_mixin import investigation_orm_to_dto_unencrypted_row
from app.repository.audit_log_repo import AuditLogRepository
from app.models.sqlalchemy.audit_log import AuditLog

logger = structlog.get_logger()


class InvestigationService:
    """Service layer for investigation operations."""

    def __init__(
        self,
        investigation_repo: InvestigationRepository,
        session: AsyncSession,
    ):
        self.investigation_repo = investigation_repo
        self.session = session
        self._audit_log_repo = AuditLogRepository()

    # ── Read ──

    async def get_investigation_by_id(self, investigation_id: UUID) -> InvestigationItem:
        """Get a single investigation by ID."""
        try:
            inv = await self.investigation_repo.get_investigation_by_id(
                self.session, investigation_id,
            )
            return investigation_orm_to_dto_unencrypted_row(inv).to_schema()
        except Exception:
            logger.exception("Failed to get investigation", investigation_id=investigation_id)
            raise

    async def get_investigations_by_election(self, election_id: UUID) -> List[InvestigationItem]:
        """Get all investigations for an election."""
        try:
            investigations = await self.investigation_repo.get_investigations_by_election(
                self.session, election_id,
            )
            return [investigation_orm_to_dto_unencrypted_row(i).to_schema() for i in investigations]
        except Exception:
            logger.exception("Failed to get investigations by election", election_id=election_id)
            raise

    async def get_investigations_by_referendum(self, referendum_id: UUID) -> List[InvestigationItem]:
        """Get all investigations for a referendum."""
        try:
            investigations = await self.investigation_repo.get_investigations_by_referendum(
                self.session, referendum_id,
            )
            return [investigation_orm_to_dto_unencrypted_row(i).to_schema() for i in investigations]
        except Exception:
            logger.exception("Failed to get investigations by referendum", referendum_id=referendum_id)
            raise

    async def get_investigations_by_error(self, error_id: UUID) -> List[InvestigationItem]:
        """Get all investigations linked to an error report."""
        try:
            investigations = await self.investigation_repo.get_investigations_by_error(
                self.session, error_id,
            )
            return [investigation_orm_to_dto_unencrypted_row(i).to_schema() for i in investigations]
        except Exception:
            logger.exception("Failed to get investigations by error", error_id=error_id)
            raise

    async def get_investigations_by_assignee(self, official_id: UUID) -> List[InvestigationItem]:
        """Get all investigations assigned to a specific official."""
        try:
            investigations = await self.investigation_repo.get_investigations_by_assignee(
                self.session, official_id,
            )
            return [investigation_orm_to_dto_unencrypted_row(i).to_schema() for i in investigations]
        except Exception:
            logger.exception("Failed to get investigations by assignee", official_id=official_id)
            raise

    # ── Update ──

    async def update_investigation(
        self, investigation_id: UUID, dto: UpdateInvestigationPlainDTO,
    ) -> InvestigationItem:
        """Update an investigation's mutable fields.

        When status is set to RESOLVED or CLOSED, resolved_at is
        automatically set if not already present.
        """
        try:
            update_data: dict = {}

            if dto.status is not None:
                update_data["status"] = dto.status
            if dto.category is not None:
                update_data["category"] = dto.category
            if dto.assigned_to is not None:
                update_data["assigned_to"] = dto.assigned_to
            if dto.notes is not None:
                update_data["notes"] = dto.notes
            if dto.resolved_by is not None:
                update_data["resolved_by"] = dto.resolved_by
            if dto.resolution_summary is not None:
                update_data["resolution_summary"] = dto.resolution_summary

            # Require a resolution summary when resolving/closing
            if dto.status in ("RESOLVED", "CLOSED") and not dto.resolution_summary:
                raise ValidationError(
                    "A resolution summary is required when resolving or closing "
                    "an investigation. Describe the findings and any actions taken."
                )

            # Auto-set resolved_at when resolving/closing
            if dto.status in ("RESOLVED", "CLOSED"):
                update_data["resolved_at"] = datetime.now(timezone.utc)

            if not update_data:
                raise ValidationError("No fields to update")

            updated = await self.investigation_repo.update_investigation(
                self.session, investigation_id, update_data,
            )

            # Audit: investigation updated/resolved
            event_type = "INVESTIGATION_UPDATED"
            summary = f"Investigation {investigation_id} updated"
            if dto.status in ("RESOLVED", "CLOSED"):
                event_type = "INVESTIGATION_RESOLVED"
                summary = f"Investigation {investigation_id} {dto.status.lower()}"

            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type=event_type,
                    action="UPDATE",
                    summary=summary,
                    resource_type="investigation",
                    resource_id=investigation_id,
                    election_id=updated.election_id,
                    referendum_id=updated.referendum_id,
                    actor_type="OFFICIAL",
                    actor_id=dto.assigned_to or dto.resolved_by,
                ),
            )

            return investigation_orm_to_dto_unencrypted_row(updated).to_schema()

        except (ValidationError,):
            raise
        except Exception:
            logger.exception("Failed to update investigation", investigation_id=investigation_id)
            raise
