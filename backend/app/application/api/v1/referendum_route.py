# referendum_route.py - Referendum endpoints for the e-voting system.

from fastapi import APIRouter, Path, Depends, Body, status
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.schemas.referendum import ReferendumItem, CreateReferendumRequest, UpdateReferendumRequest
from app.models.dto.referendum import CreateReferendumPlainDTO
from app.service.referendum_service import ReferendumService
from app.application.api.dependencies import get_referendum_service
from typing import List
from uuid import UUID
import structlog

referendum_responses = responses(Resource.REFERENDUM)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/referendum",
    tags=["referendum"],
)


# Get all referendums
@router.get(
    "/",
    responses=referendum_responses,
    response_model=List[ReferendumItem],
    status_code=status.HTTP_200_OK,
)
async def get_all_referendums(
    service: ReferendumService = Depends(get_referendum_service),
) -> List[ReferendumItem]:
    """Get all referendums."""
    return await service.get_all_referendums()


# Get referendum by ID
@router.get(
    "/{referendum_id}",
    responses=referendum_responses,
    response_model=ReferendumItem,
    status_code=status.HTTP_200_OK,
)
async def get_referendum_by_id(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    service: ReferendumService = Depends(get_referendum_service),
) -> ReferendumItem:
    """Get referendum details by ID."""
    return await service.get_referendum_by_id(referendum_id)


# Create referendum
@router.post(
    "/",
    responses=referendum_responses,
    response_model=ReferendumItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_referendum(
    body: CreateReferendumRequest = Body(..., description="The referendum creation request."),
    service: ReferendumService = Depends(get_referendum_service),
):
    """Create a new referendum with a yes/no question for voters."""
    dto = CreateReferendumPlainDTO.create_dto(body)
    return await service.create_referendum(dto)


# Update referendum
@router.patch(
    "/{referendum_id}",
    responses=referendum_responses,
    response_model=ReferendumItem,
    status_code=status.HTTP_200_OK,
)
async def update_referendum(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    body: UpdateReferendumRequest = Body(..., description="The referendum update request."),
    service: ReferendumService = Depends(get_referendum_service),
):
    """Update a referendum's mutable fields."""
    update_data = body.model_dump(exclude_none=True)
    return await service.update_referendum(referendum_id, update_data)
