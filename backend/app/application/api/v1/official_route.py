# official_route.py - Election official routes (admins + officers).

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.application.api.dependencies import get_current_user, get_official_service, require_role
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.dto.auth import TokenPayload
from app.models.dto.official import CreateOfficialPlainDTO, UpdateOfficialPlainDTO
from app.models.schemas.official import (
    CreateOfficialRequest,
    OfficialItem,
    UpdateOfficialRequest,
)
from app.models.sqlalchemy.election_official import OfficialRole
from app.service.official_service import OfficialService

official_responses = responses(Resource.OFFICIAL)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/official",
    tags=["official"],
)


# Create an election official (admin-only)
@router.post(
    "",
    responses=official_responses,
    response_model=OfficialItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_official(
    body: CreateOfficialRequest = Body(..., description="The official creation request."),
    service: OfficialService = Depends(get_official_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Create a new election official.

    Only administrators can create officials. The official will be
    required to reset their password on first login.
    """
    dto = CreateOfficialPlainDTO.create_dto(body)
    return await service.create_official(dto)


# Update an election official (admin-only)
@router.patch(
    "/{official_id}",
    responses=official_responses,
    response_model=OfficialItem,
    status_code=status.HTTP_200_OK,
)
async def update_official(
    official_id: UUID = Path(..., description="The unique identifier for the official."),
    body: UpdateOfficialRequest = Body(..., description="The official update request."),
    service: OfficialService = Depends(get_official_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Update an election official's mutable fields.

    Only admins can update official details including role and active status.
    """
    dto = UpdateOfficialPlainDTO.create_dto(body, official_id)
    return await service.update_official(official_id, dto)


# Get all election officials (any official)
@router.get(
    "",
    responses=official_responses,
    response_model=List[OfficialItem],
    status_code=status.HTTP_200_OK,
)
async def get_all_officials(
    role: Optional[OfficialRole] = Query(None, description="Filter by role (ADMIN or OFFICER)."),
    service: OfficialService = Depends(get_official_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[OfficialItem]:
    """Get all election officials, optionally filtered by role."""
    if role:
        return await service.get_officials_by_role(role.value)
    return await service.get_all_officials()


# Get election official by ID (any official)
@router.get(
    "/{official_id}",
    responses=official_responses,
    response_model=OfficialItem,
    status_code=status.HTTP_200_OK,
)
async def get_official_by_id(
    official_id: UUID = Path(..., description="The unique identifier for the official."),
    service: OfficialService = Depends(get_official_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> OfficialItem:
    """Get election official details by ID."""
    return await service.get_official_by_id(official_id)


# Deactivate an election official (admin-only)
@router.patch(
    "/{official_id}/deactivate",
    responses=official_responses,
    response_model=OfficialItem,
    status_code=status.HTTP_200_OK,
)
async def deactivate_official(
    official_id: UUID = Path(..., description="The unique identifier for the official."),
    service: OfficialService = Depends(get_official_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Deactivate an election official (admin-only).

    The official's account is disabled but not deleted, preserving
    audit trail integrity.
    """
    return await service.deactivate_official(official_id)


# Reactivate an election official (admin-only)
@router.patch(
    "/{official_id}/activate",
    responses=official_responses,
    response_model=OfficialItem,
    status_code=status.HTTP_200_OK,
)
async def activate_official(
    official_id: UUID = Path(..., description="The unique identifier for the official."),
    service: OfficialService = Depends(get_official_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Reactivate a previously deactivated election official (admin-only)."""
    return await service.activate_official(official_id)
