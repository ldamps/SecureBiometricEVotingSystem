# app/application/api/v1/voter_route.py - Voter route definitions

from fastapi import APIRouter, status, Path, Depends, Body
from app.application.api.responses import responses
from app.application.constants import Resource
from uuid import UUID
import structlog
from app.service.voter_service import VoterService
from app.application.api.dependencies import get_voter_service
from app.models.schemas.voter import VoterItem, VoterRegistrationRequest, VoterUpdateRequest
from app.models.dto.voter import RegisterVoterPlainDTO, UpdateVoterPlainDTO

voter_responses = responses(Resource.VOTER)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/voter",
    tags=["voter"],
)

# Get voter details by voter ID
@router.get(
    "/{voter_id}", 
    responses=voter_responses, 
    status_code=status.HTTP_200_OK
)
async def get_voter_by_voter_id(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    service: VoterService = Depends(get_voter_service),
) -> VoterItem:
    """
    Get voter details by voter ID
    """
    return await service.get_voter_by_id(voter_id)


# Register a new voter
@router.post(
    "/register",
    responses=voter_responses,
    response_model=VoterItem,
    status_code=status.HTTP_201_CREATED
)
async def register_voter(
    body: VoterRegistrationRequest = Body(..., description="The voter registration request."),
    service: VoterService = Depends(get_voter_service),
):
    """
    Register a new voter
    """
    dto = RegisterVoterPlainDTO.create_dto(body)
    return await service.register_voter(dto)


# Update a voter's (registration) details
@router.patch(
    "/{voter_id}",
    responses=voter_responses,
    response_model=VoterItem,
    status_code=status.HTTP_200_OK
)
async def update_voter(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    body: VoterUpdateRequest = Body(..., description="The voter update request."),
    service: VoterService = Depends(get_voter_service),
):
    """
    Update a voter's (registration) details
    """
    dto = UpdateVoterPlainDTO.create_dto(body)
    return await service.update_voter_details(voter_id, dto)



