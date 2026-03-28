# referendum_route.py - Referendum endpoints for the e-voting system.

from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from app.application.api.dependencies import get_ballot_token_service, get_referendum_service
from app.application.api.responses import responses
from app.application.constants import Resource
from app.application.core.exceptions import NotFoundError, ValidationError
from app.models.dto.referendum import CreateReferendumPlainDTO
from app.models.schemas.ballot_token import (
    BallotTokenItem,
    BallotTokenStatusResponse,
    IssueReferendumBallotTokenRequest,
    IssueReferendumBallotTokenResponse,
)
from app.models.schemas.referendum import ReferendumItem, CreateReferendumRequest, UpdateReferendumRequest
from app.service.ballot_service import BallotTokenService
from app.service.referendum_service import ReferendumService

referendum_responses = responses(Resource.REFERENDUM)
ballot_responses = responses(Resource.BALLOT_TOKEN)
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


# ── Ballot tokens ──


# Issue ballot tokens for a referendum
@router.post(
    "/{referendum_id}/ballot-tokens",
    responses=ballot_responses,
    response_model=IssueReferendumBallotTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_referendum_ballot_tokens(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    body: IssueReferendumBallotTokenRequest = Body(
        ..., description="Request to issue referendum ballot tokens."
    ),
    service: BallotTokenService = Depends(get_ballot_token_service),
):
    """Issue one-time ballot tokens for a referendum.

    Each token can be distributed to an eligible voter. The voter uses the
    ``blind_token_hash`` when casting their referendum vote.
    """
    try:
        body.referendum_id = str(referendum_id)
        return await service.issue_referendum_tokens(body)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Get ballot token status for a referendum
@router.get(
    "/{referendum_id}/ballot-tokens/status",
    responses=ballot_responses,
    response_model=BallotTokenStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_referendum_ballot_token_status(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    service: BallotTokenService = Depends(get_ballot_token_service),
):
    """Get total/used/unused token counts for a referendum."""
    try:
        return await service.get_referendum_token_status(referendum_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all ballot tokens for a referendum
@router.get(
    "/{referendum_id}/ballot-tokens",
    responses=ballot_responses,
    response_model=List[BallotTokenItem],
    status_code=status.HTTP_200_OK,
)
async def get_referendum_ballot_tokens(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    service: BallotTokenService = Depends(get_ballot_token_service),
):
    """List all ballot tokens for a referendum (decrypted)."""
    try:
        return await service.get_referendum_tokens(referendum_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
