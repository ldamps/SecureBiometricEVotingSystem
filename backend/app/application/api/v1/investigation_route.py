# investigation_route.py - Error report + investigation routes.

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.application.api.dependencies import get_current_user, get_error_report_service, get_investigation_service
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.dto.auth import TokenPayload
from app.models.dto.error_report import CreateErrorReportPlainDTO
from app.models.dto.investigation import UpdateInvestigationPlainDTO
from app.models.schemas.error_report import (
    CreateErrorReportRequest,
    ErrorReportItem,
    ErrorReportWithInvestigationItem,
)
from app.models.schemas.investigation import (
    InvestigationItem,
    UpdateInvestigationRequest,
)
from app.service.error_report_service import ErrorReportService
from app.service.investigation_service import InvestigationService

error_report_responses = responses(Resource.ERROR_REPORT)
investigation_responses = responses(Resource.INVESTIGATION)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/errors",
    tags=["errors"],
)


# ── Error Reports ──


# Report an error (any official)
@router.post(
    "/report",
    responses=error_report_responses,
    response_model=ErrorReportWithInvestigationItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_error_report(
    body: CreateErrorReportRequest = Body(..., description="The error report request."),
    service: ErrorReportService = Depends(get_error_report_service),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Report a discrepancy for an election.

    Automatically opens an investigation with status OPEN linked to
    the error report.
    """
    dto = CreateErrorReportPlainDTO.create_dto(body)
    return await service.create_error_report(dto)


# Get error report by ID (any official)
@router.get(
    "/report/{report_id}",
    responses=error_report_responses,
    response_model=ErrorReportItem,
    status_code=status.HTTP_200_OK,
)
async def get_error_report_by_id(
    report_id: UUID = Path(..., description="The unique identifier for the error report."),
    service: ErrorReportService = Depends(get_error_report_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> ErrorReportItem:
    """Get a single error report by ID."""
    return await service.get_error_report_by_id(report_id)


# List error reports for an election (any official)
@router.get(
    "/report/election/{election_id}",
    responses=error_report_responses,
    response_model=List[ErrorReportItem],
    status_code=status.HTTP_200_OK,
)
async def get_reports_by_election(
    election_id: UUID = Path(..., description="The election ID."),
    service: ErrorReportService = Depends(get_error_report_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[ErrorReportItem]:
    """List all error reports for an election."""
    return await service.get_reports_by_election(election_id)


# List error reports filed by an official (any official)
@router.get(
    "/report/official/{official_id}",
    responses=error_report_responses,
    response_model=List[ErrorReportItem],
    status_code=status.HTTP_200_OK,
)
async def get_reports_by_official(
    official_id: UUID = Path(..., description="The official ID."),
    service: ErrorReportService = Depends(get_error_report_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[ErrorReportItem]:
    """List all error reports filed by a specific official."""
    return await service.get_reports_by_official(official_id)


# ── Investigations ──


# Get investigation by ID (any official)
@router.get(
    "/{investigation_id}",
    responses=investigation_responses,
    response_model=InvestigationItem,
    status_code=status.HTTP_200_OK,
)
async def get_investigation_by_id(
    investigation_id: UUID = Path(..., description="The unique identifier for the investigation."),
    service: InvestigationService = Depends(get_investigation_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> InvestigationItem:
    """Get a single investigation by ID."""
    return await service.get_investigation_by_id(investigation_id)


# List investigations for an election (any official)
@router.get(
    "/investigations/{election_id}",
    responses=investigation_responses,
    response_model=List[InvestigationItem],
    status_code=status.HTTP_200_OK,
)
async def get_investigations_by_election(
    election_id: UUID = Path(..., description="The election ID."),
    service: InvestigationService = Depends(get_investigation_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[InvestigationItem]:
    """List all investigations for an election."""
    return await service.get_investigations_by_election(election_id)


# List investigations for an error report (any official)
@router.get(
    "/report/{error_id}/investigations",
    responses=investigation_responses,
    response_model=List[InvestigationItem],
    status_code=status.HTTP_200_OK,
)
async def get_investigations_by_error(
    error_id: UUID = Path(..., description="The error report ID."),
    service: InvestigationService = Depends(get_investigation_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[InvestigationItem]:
    """List all investigations linked to an error report."""
    return await service.get_investigations_by_error(error_id)


# List investigations assigned to an official (any official)
@router.get(
    "/investigation/{official_id}/assigned",
    responses=investigation_responses,
    response_model=List[InvestigationItem],
    status_code=status.HTTP_200_OK,
)
async def get_investigations_by_assignee(
    official_id: UUID = Path(..., description="The official ID."),
    service: InvestigationService = Depends(get_investigation_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[InvestigationItem]:
    """List all investigations assigned to a specific official."""
    return await service.get_investigations_by_assignee(official_id)


# Update an investigation (any official)
@router.patch(
    "/investigation/{investigation_id}",
    responses=investigation_responses,
    response_model=InvestigationItem,
    status_code=status.HTTP_200_OK,
)
async def update_investigation(
    investigation_id: UUID = Path(..., description="The unique identifier for the investigation."),
    body: UpdateInvestigationRequest = Body(..., description="The investigation update request."),
    service: InvestigationService = Depends(get_investigation_service),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Update an investigation.

    Supports assigning to an official, changing status, adding notes,
    and marking as resolved. When status is RESOLVED or CLOSED,
    resolved_at is set automatically.
    """
    dto = UpdateInvestigationPlainDTO.create_dto(body, investigation_id)
    return await service.update_investigation(investigation_id, dto)
