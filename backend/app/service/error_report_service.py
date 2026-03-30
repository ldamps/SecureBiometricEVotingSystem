# error_report_service.py - Service layer for error report operations.

from datetime import datetime, timezone
from typing import List
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dto.error_report import CreateErrorReportPlainDTO
from app.models.schemas.error_report import ErrorReportItem, ErrorReportWithInvestigationItem
from app.models.sqlalchemy.error_report import ErrorReport
from app.models.sqlalchemy.investigation import Investigation
from app.repository.error_report_repo import ErrorReportRepository
from app.repository.investigation_repo import InvestigationRepository
from app.service.base.encryption_utils_mixin import (
    error_report_orm_to_dto_unencrypted_row,
    investigation_orm_to_dto_unencrypted_row,
)
from app.repository.audit_log_repo import AuditLogRepository
from app.models.sqlalchemy.audit_log import AuditLog

logger = structlog.get_logger()


class ErrorReportService:
    """Service layer for error report operations.

    When an error report is created, an investigation is automatically
    opened with status OPEN so it can be assigned and tracked.
    """

    def __init__(
        self,
        error_report_repo: ErrorReportRepository,
        investigation_repo: InvestigationRepository,
        session: AsyncSession,
    ):
        self.error_report_repo = error_report_repo
        self.investigation_repo = investigation_repo
        self.session = session
        self._audit_log_repo = AuditLogRepository()

    # ── Create (report + auto-open investigation) ──

    async def create_error_report(
        self, dto: CreateErrorReportPlainDTO,
    ) -> ErrorReportWithInvestigationItem:
        """Create an error report and automatically open an investigation."""
        try:
            now = datetime.now(timezone.utc)

            # 1. Persist the error report
            report = ErrorReport(
                election_id=dto.election_id,
                reported_by=dto.reported_by,
                title=dto.title,
                description=dto.description,
                severity=dto.severity,
                reported_at=now,
            )
            report = await self.error_report_repo.create_error_report(
                self.session, report,
            )

            # 2. Auto-open an investigation linked to the report
            investigation = Investigation(
                error_id=report.id,
                election_id=report.election_id,
                raised_by=report.reported_by,
                title=report.title,
                description=report.description,
                severity=report.severity,
                status="OPEN",
                raised_at=now,
            )
            investigation = await self.investigation_repo.create_investigation(
                self.session, investigation,
            )

            # Audit: error report created + investigation opened
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="ERROR_REPORT_CREATED",
                    action="CREATE",
                    summary=f"Error report '{report.title}' created for election {report.election_id}",
                    resource_type="error_report",
                    resource_id=report.id,
                    election_id=report.election_id,
                    actor_type="OFFICIAL",
                    actor_id=report.reported_by,
                ),
            )
            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="INVESTIGATION_OPENED",
                    action="CREATE",
                    summary=f"Investigation auto-opened for error report '{report.title}'",
                    resource_type="investigation",
                    resource_id=investigation.id,
                    election_id=report.election_id,
                    actor_type="SYSTEM",
                ),
            )

            return ErrorReportWithInvestigationItem(
                error_report=error_report_orm_to_dto_unencrypted_row(report).to_schema(),
                investigation=investigation_orm_to_dto_unencrypted_row(investigation).to_schema(),
            )

        except Exception:
            logger.exception("Failed to create error report")
            raise

    # ── Read ──

    async def get_error_report_by_id(self, report_id: UUID) -> ErrorReportItem:
        """Get a single error report by ID."""
        try:
            report = await self.error_report_repo.get_error_report_by_id(
                self.session, report_id,
            )
            return error_report_orm_to_dto_unencrypted_row(report).to_schema()
        except Exception:
            logger.exception("Failed to get error report", report_id=report_id)
            raise

    async def get_reports_by_election(self, election_id: UUID) -> List[ErrorReportItem]:
        """Get all error reports for an election."""
        try:
            reports = await self.error_report_repo.get_reports_by_election(
                self.session, election_id,
            )
            return [error_report_orm_to_dto_unencrypted_row(r).to_schema() for r in reports]
        except Exception:
            logger.exception("Failed to get reports by election", election_id=election_id)
            raise

    async def get_reports_by_official(self, official_id: UUID) -> List[ErrorReportItem]:
        """Get all error reports filed by a specific official."""
        try:
            reports = await self.error_report_repo.get_reports_by_official(
                self.session, official_id,
            )
            return [error_report_orm_to_dto_unencrypted_row(r).to_schema() for r in reports]
        except Exception:
            logger.exception("Failed to get reports by official", official_id=official_id)
            raise
