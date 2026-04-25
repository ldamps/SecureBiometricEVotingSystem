# error_report_repo.py - Repository layer for error report operations.

from app.models.sqlalchemy.error_report import ErrorReport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
from typing import Type
from uuid import UUID
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()


class ErrorReportRepository:
    """Error report repository operations."""

    def __init__(self, model: Type[ErrorReport] = ErrorReport) -> None:
        self._model = model

    async def create_error_report(
        self, session: AsyncSession, report: ErrorReport,
    ) -> ErrorReport:
        """Persist a new error report."""
        try:
            session.add(report)
            await session.flush()
            logger.info("Error report created", report_id=report.id)
            return report
        except Exception:
            logger.exception("Failed to create error report")
            raise

    async def get_error_report_by_id(
        self, session: AsyncSession, report_id: UUID,
    ) -> ErrorReport:
        """Get an error report by ID."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.id == report_id)
            )
            report = result.scalar_one_or_none()
            if not report:
                raise NotFoundError("Error report not found")
            return report
        except Exception:
            logger.exception("Failed to get error report", report_id=report_id)
            raise

    async def get_reports_by_election(
        self, session: AsyncSession, election_id: UUID,
    ) -> list[ErrorReport]:
        """Get all error reports for an election."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.election_id == election_id)
                .order_by(self._model.reported_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get reports by election", election_id=election_id)
            raise

    async def get_reports_by_referendum(
        self, session: AsyncSession, referendum_id: UUID,
    ) -> list[ErrorReport]:
        """Get all error reports for a referendum."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.referendum_id == referendum_id)
                .order_by(self._model.reported_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get reports by referendum", referendum_id=referendum_id)
            raise

    async def get_reports_by_official(
        self, session: AsyncSession, official_id: UUID,
    ) -> list[ErrorReport]:
        """Get all error reports filed by a specific official."""
        try:
            result = await session.execute(
                select(self._model)
                .where(self._model.reported_by == official_id)
                .order_by(self._model.reported_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get reports by official", official_id=official_id)
            raise
