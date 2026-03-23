# app/application/api/v1/election_route.py - Election endpoints.

from fastapi import APIRouter, Path, Depends, Body, status
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.schemas.election import ElectionItem, CreateElectionRequest, UpdateElectionRequest
from app.models.dto.election import CreateElectionPlainDTO, UpdateElectionPlainDTO
from app.service.election_service import ElectionService
from app.application.api.dependencies import get_election_service
from typing import List
from uuid import UUID
import structlog


election_responses = responses(Resource.ELECTION)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/election",
    tags=["election"],
)


# get election by ID
@router.get(
    "/{election_id}",
    responses=election_responses,
    status_code=status.HTTP_200_OK,
)
async def get_election_by_id(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    service: ElectionService = Depends(get_election_service),
) -> ElectionItem:
    """Get election details by election ID."""
    return await service.get_election_by_id(election_id)


# get all elections
@router.get(
    "/",
    responses=election_responses,
    response_model=List[ElectionItem],
    status_code=status.HTTP_200_OK,
)
async def get_all_elections(
    service: ElectionService = Depends(get_election_service),
) -> List[ElectionItem]:
    """Get all elections."""
    return await service.get_all_elections()


# create an election
@router.post(
    "/",
    responses=election_responses,
    response_model=ElectionItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_election(
    body: CreateElectionRequest = Body(..., description="The election creation request."),
    service: ElectionService = Depends(get_election_service),
):
    """Create a new election."""
    dto = CreateElectionPlainDTO.create_dto(body)
    return await service.create_election(dto)


# update an election (only status, voting_opens, voting_closes)
@router.patch(
    "/{election_id}",
    responses=election_responses,
    response_model=ElectionItem,
    status_code=status.HTTP_200_OK,
)
async def update_election(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    body: UpdateElectionRequest = Body(default=None, description="The election update request."),
    service: ElectionService = Depends(get_election_service),
):
    """Update an election's mutable fields (status, voting_opens, voting_closes).

    Title, election type, and allocation method are immutable after creation.
    """
    dto = UpdateElectionPlainDTO.create_dto(body, election_id)
    return await service.update_election(election_id, dto)
