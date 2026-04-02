# referendum_route.py - Referendum endpoints for the e-voting system.

from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, Path, status

from app.application.api.dependencies import (
    get_ballot_token_service,
    get_current_user,
    get_referendum_service,
    get_result_service,
    get_tally_service,
    get_voter_ledger_service,
    require_role,
)
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.dto.auth import TokenPayload
from app.models.dto.referendum import CreateReferendumPlainDTO
from app.models.schemas.ballot_token import (
    BallotTokenItem,
    BallotTokenStatusResponse,
    IssueReferendumBallotTokenRequest,
    IssueReferendumBallotTokenResponse,
)
from app.models.schemas.referendum import ReferendumItem, CreateReferendumRequest, UpdateReferendumRequest
from app.models.schemas.result import ReferendumResultResponse
from app.models.schemas.tally_result import TallyResultItem
from app.models.schemas.voter_ledger import ReferendumVoterListResponse
from app.service.ballot_service import BallotTokenService
from app.service.referendum_service import ReferendumService
from app.service.result_service import ResultService
from app.service.tally_service import TallyService
from app.service.voter_ledger_service import VoterLedgerService

referendum_responses = responses(Resource.REFERENDUM)
ballot_responses = responses(Resource.BALLOT_TOKEN)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/referendum",
    tags=["referendum"],
)


# Get all referendums (public – voters browse before authenticating)
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


# Get referendum by ID (public – voters browse before authenticating)
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


# Create referendum (admin-only)
@router.post(
    "/",
    responses=referendum_responses,
    response_model=ReferendumItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_referendum(
    body: CreateReferendumRequest = Body(..., description="The referendum creation request."),
    service: ReferendumService = Depends(get_referendum_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Create a new referendum (status is derived from voting window times)."""
    dto = CreateReferendumPlainDTO.create_dto(body)
    return await service.create_referendum(dto)


# Update referendum (admin-only)
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
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Update a referendum's mutable fields."""
    update_data = body.model_dump(exclude_none=True)
    return await service.update_referendum(referendum_id, update_data)


# List all voters for a referendum with voting status (any official)
@router.get(
    "/{referendum_id}/voters",
    responses=referendum_responses,
    response_model=ReferendumVoterListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_referendum_voters(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    service: VoterLedgerService = Depends(get_voter_ledger_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> ReferendumVoterListResponse:
    """List all voters registered for a referendum and whether they have voted."""
    return await service.get_referendum_voters(referendum_id)


# ── Ballot tokens ──


# Issue ballot tokens for a referendum (admin-only)
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
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Issue one-time ballot tokens for a referendum.

    Each token can be distributed to an eligible voter. The voter uses the
    ``blind_token_hash`` when casting their referendum vote.
    """
    body.referendum_id = str(referendum_id)
    return await service.issue_referendum_tokens(body)


# Get ballot token status for a referendum (any official)
@router.get(
    "/{referendum_id}/ballot-tokens/status",
    responses=ballot_responses,
    response_model=BallotTokenStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_referendum_ballot_token_status(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    service: BallotTokenService = Depends(get_ballot_token_service),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get total/used/unused token counts for a referendum."""
    return await service.get_referendum_token_status(referendum_id)


# List all ballot tokens for a referendum (admin-only)
@router.get(
    "/{referendum_id}/ballot-tokens",
    responses=ballot_responses,
    response_model=List[BallotTokenItem],
    status_code=status.HTTP_200_OK,
)
async def get_referendum_ballot_tokens(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    service: BallotTokenService = Depends(get_ballot_token_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """List all ballot tokens for a referendum (decrypted)."""
    return await service.get_referendum_tokens(referendum_id)


# ── Results & tallies ──


# Get aggregated referendum results (any official)
@router.get(
    "/{referendum_id}/results",
    responses=referendum_responses,
    response_model=ReferendumResultResponse,
    status_code=status.HTTP_200_OK,
)
async def get_referendum_results(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    service: ResultService = Depends(get_result_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> ReferendumResultResponse:
    """Get aggregated YES/NO results for a referendum."""
    return await service.get_referendum_results(referendum_id)


# Get tallies for a referendum (admin-only)
@router.get(
    "/{referendum_id}/tallies",
    responses=referendum_responses,
    response_model=List[TallyResultItem],
    status_code=status.HTTP_200_OK,
)
async def get_referendum_tallies(
    referendum_id: UUID = Path(..., description="The unique identifier for the referendum."),
    service: TallyService = Depends(get_tally_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[TallyResultItem]:
    """Get YES/NO tallies for a referendum."""
    return await service.get_tallies_by_referendum(referendum_id)
