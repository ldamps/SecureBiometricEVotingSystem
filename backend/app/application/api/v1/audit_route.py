# audit_route.py - Audit log routes (read-only — events are logged automatically by services).

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Path, Query, status

from app.application.api.dependencies import get_audit_log_service, require_role
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.dto.auth import TokenPayload
from app.models.schemas.audit_log import AuditLogItem
from app.service.audit_log_service import AuditLogService

audit_responses = responses(Resource.AUDIT_LOG)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/audit",
    tags=["audit"],
)


# List recent audit logs (admin-only)
@router.get(
    "/",
    responses=audit_responses,
    response_model=List[AuditLogItem],
    status_code=status.HTTP_200_OK,
)
async def get_recent_audit_logs(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of entries to return."),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[AuditLogItem]:
    """Get the most recent audit log entries."""
    return await service.get_recent_audit_logs(limit)


# List audit logs by date range (admin-only)
@router.get(
    "/date-range",
    responses=audit_responses,
    response_model=List[AuditLogItem],
    status_code=status.HTTP_200_OK,
)
async def get_audit_logs_by_date_range(
    start: Optional[datetime] = Query(None, description="Start of date range (ISO 8601). Defaults to 24 hours ago."),
    end: Optional[datetime] = Query(None, description="End of date range (ISO 8601). Defaults to now."),
    election_id: Optional[UUID] = Query(None, description="Optional election scope."),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[AuditLogItem]:
    """List audit log entries within a date range, optionally scoped to an election.

    Defaults to the last 24 hours if start/end are not provided.
    """
    now = datetime.now(timezone.utc)
    resolved_end = end or now
    resolved_start = start or (now - timedelta(hours=24))
    return await service.get_audit_logs_by_date_range(resolved_start, resolved_end, election_id)


# List audit logs by election (admin-only)
@router.get(
    "/election/{election_id}",
    responses=audit_responses,
    response_model=List[AuditLogItem],
    status_code=status.HTTP_200_OK,
)
async def get_audit_logs_by_election(
    election_id: UUID = Path(..., description="The election ID."),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[AuditLogItem]:
    """List all audit log entries for a specific election."""
    return await service.get_audit_logs_by_election(election_id)


# List audit logs by actor (admin-only)
@router.get(
    "/actor/{actor_id}",
    responses=audit_responses,
    response_model=List[AuditLogItem],
    status_code=status.HTTP_200_OK,
)
async def get_audit_logs_by_actor(
    actor_id: UUID = Path(..., description="The actor (user) ID."),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[AuditLogItem]:
    """List all audit log entries for a specific actor."""
    return await service.get_audit_logs_by_actor(actor_id)


# List audit logs by actor type (admin-only)
@router.get(
    "/actor-type/{actor_type}",
    responses=audit_responses,
    response_model=List[AuditLogItem],
    status_code=status.HTTP_200_OK,
)
async def get_audit_logs_by_actor_type(
    actor_type: str = Path(..., description="The actor type (OFFICIAL, VOTER, SYSTEM)."),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[AuditLogItem]:
    """List all audit log entries for a specific actor type."""
    return await service.get_audit_logs_by_actor_type(actor_type.upper())


# List audit logs by resource (admin-only)
@router.get(
    "/resource/{resource_type}/{resource_id}",
    responses=audit_responses,
    response_model=List[AuditLogItem],
    status_code=status.HTTP_200_OK,
)
async def get_audit_logs_by_resource(
    resource_type: str = Path(..., description="The resource type (e.g. voter, election)."),
    resource_id: UUID = Path(..., description="The resource ID."),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[AuditLogItem]:
    """List all audit log entries for a specific resource."""
    return await service.get_audit_logs_by_resource(resource_type, resource_id)


# List audit logs by event type (admin-only)
@router.get(
    "/event-type/{event_type}",
    responses=audit_responses,
    response_model=List[AuditLogItem],
    status_code=status.HTTP_200_OK,
)
async def get_audit_logs_by_event_type(
    event_type: str = Path(..., description="The event type (e.g. VOTER_REGISTERED, VOTE_CAST)."),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[AuditLogItem]:
    """List all audit log entries of a specific event type."""
    return await service.get_audit_logs_by_event_type(event_type)


# Get audit log by ID (admin-only, must be last — wildcard path)
@router.get(
    "/{audit_id}",
    responses=audit_responses,
    response_model=AuditLogItem,
    status_code=status.HTTP_200_OK,
)
async def get_audit_log_by_id(
    audit_id: UUID = Path(..., description="The audit log entry ID."),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> AuditLogItem:
    """Get a single audit log entry by ID."""
    return await service.get_audit_log_by_id(audit_id)
