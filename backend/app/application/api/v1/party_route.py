# party_route.py - Party endpoints for the e-voting system.

from fastapi import APIRouter, Path, Depends, Body, status
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.schemas.party import PartyItem, CreateParty, UpdateParty
from app.models.schemas.candidate import CandidateItem
from app.models.dto.party import CreatePartyPlainDTO
from app.service.party_service import PartyService
from app.service.candidate_service import CandidateService
from app.application.api.dependencies import get_party_service, get_candidate_service
from typing import List
from uuid import UUID
import structlog

party_responses = responses(Resource.PARTY)
candidate_responses = responses(Resource.CANDIDATE)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/party",
    tags=["party"],
)


# Get all parties
@router.get(
    "/",
    responses=party_responses,
    response_model=List[PartyItem],
    status_code=status.HTTP_200_OK,
)
async def get_all_parties(
    service: PartyService = Depends(get_party_service),
) -> List[PartyItem]:
    """Get all parties."""
    return await service.get_all_parties()


# Get party by ID
@router.get(
    "/{party_id}",
    responses=party_responses,
    response_model=PartyItem,
    status_code=status.HTTP_200_OK,
)
async def get_party_by_id(
    party_id: UUID = Path(..., description="The unique identifier for the party."),
    service: PartyService = Depends(get_party_service),
) -> PartyItem:
    """Get party details by party ID."""
    return await service.get_party_by_id(party_id)


# Create party
@router.post(
    "/",
    responses=party_responses,
    response_model=PartyItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_party(
    body: CreateParty = Body(..., description="The party creation request."),
    service: PartyService = Depends(get_party_service),
):
    """Create a new party."""
    dto = CreatePartyPlainDTO.create_dto(body)
    return await service.create_party(dto)


# Update party
@router.patch(
    "/{party_id}",
    responses=party_responses,
    response_model=PartyItem,
    status_code=status.HTTP_200_OK,
)
async def update_party(
    party_id: UUID = Path(..., description="The unique identifier for the party."),
    body: UpdateParty = Body(..., description="The party update request."),
    service: PartyService = Depends(get_party_service),
):
    """Update a party's mutable fields."""
    update_data = body.model_dump(exclude_none=True)
    return await service.update_party(party_id, update_data)


# Delete party (soft delete)
@router.delete(
    "/{party_id}",
    responses=party_responses,
    response_model=PartyItem,
    status_code=status.HTTP_200_OK,
)
async def soft_delete_party(
    party_id: UUID = Path(..., description="The unique identifier for the party."),
    service: PartyService = Depends(get_party_service),
):
    """Soft delete a party (sets is_active to False)."""
    return await service.soft_delete_party(party_id)


# Get all deleted (inactive) parties
@router.get(
    "/deleted/all",
    responses=party_responses,
    response_model=List[PartyItem],
    status_code=status.HTTP_200_OK,
)
async def get_deleted_parties(
    service: PartyService = Depends(get_party_service),
) -> List[PartyItem]:
    """Get all soft-deleted (inactive) parties."""
    return await service.get_deleted_parties()


# Restore a soft-deleted party
@router.patch(
    "/{party_id}/restore",
    responses=party_responses,
    response_model=PartyItem,
    status_code=status.HTTP_200_OK,
)
async def restore_party(
    party_id: UUID = Path(..., description="The unique identifier for the party."),
    service: PartyService = Depends(get_party_service),
):
    """Restore a soft-deleted party (sets is_active back to True)."""
    return await service.restore_party(party_id)


# Get all candidates by party
@router.get(
    "/{party_id}/candidates",
    responses=candidate_responses,
    response_model=List[CandidateItem],
    status_code=status.HTTP_200_OK,
)
async def get_candidates_by_party(
    party_id: UUID = Path(..., description="The unique identifier for the party."),
    service: CandidateService = Depends(get_candidate_service),
) -> List[CandidateItem]:
    """Get all candidates belonging to a party."""
    return await service.get_candidates_by_party(party_id)
