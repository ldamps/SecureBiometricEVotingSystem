# app/application/api/v1/election_route.py - Election endpoints.

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.application.api.dependencies import (
    get_ballot_token_service,
    get_candidate_service,
    get_current_user,
    get_election_service,
    get_result_service,
    get_tally_service,
    get_voter_ledger_service,
    require_role,
)
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.dto.auth import TokenPayload
from app.models.dto.candidate import CreateCandidatePlainDTO
from app.models.dto.election import CreateElectionPlainDTO, UpdateElectionPlainDTO
from app.models.schemas.ballot_token import (
    BallotTokenItem,
    BallotTokenStatusResponse,
    IssueBallotTokenRequest,
    IssueBallotTokenResponse,
)
from app.models.schemas.candidate import CandidateItem, CreateCandidateRequest, UpdateCandidateRequest
from app.models.schemas.election import ElectionItem, CreateElectionRequest, UpdateElectionRequest
from app.models.schemas.result import ElectionResultResponse
from app.models.schemas.tally_result import TallyResultItem
from app.models.schemas.voter_ledger import ElectionVoterListResponse
from app.service.ballot_service import BallotTokenService
from app.service.result_service import ResultService
from app.service.tally_service import TallyService
from app.service.voter_ledger_service import VoterLedgerService
from app.service.candidate_service import CandidateService
from app.service.election_service import ElectionService

election_responses = responses(Resource.ELECTION)
candidate_responses = responses(Resource.CANDIDATE)
ballot_responses = responses(Resource.BALLOT_TOKEN)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/election",
    tags=["election"],
)


# get all elections (public – voters browse before authenticating).
# Declared before /{election_id} so GET /election/ is not captured by the path param route.
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


# get election by ID (public – voters browse before authenticating)
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


# create an election (admin-only)
@router.post(
    "/",
    responses=election_responses,
    response_model=ElectionItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_election(
    body: CreateElectionRequest = Body(..., description="The election creation request."),
    service: ElectionService = Depends(get_election_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Create a new election (status is derived from voting window times)."""
    dto = CreateElectionPlainDTO.create_dto(body)
    return await service.create_election(dto)


# update an election (admin-only)
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
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Update an election's mutable fields (status, voting_opens, voting_closes).

    Title, election type, and allocation method are immutable after creation.
    """
    dto = UpdateElectionPlainDTO.create_dto(body, election_id)
    return await service.update_election(election_id, dto)


# List all voters for an election with voting status (any official)
@router.get(
    "/{election_id}/voters",
    responses=election_responses,
    response_model=ElectionVoterListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_election_voters(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    service: VoterLedgerService = Depends(get_voter_ledger_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> ElectionVoterListResponse:
    """List all voters registered for an election and whether they have voted."""
    return await service.get_election_voters(election_id)


# Get all candidates for an election (any official)
@router.get(
    "/{election_id}/candidates",
    responses=candidate_responses,
    response_model=List[CandidateItem],
    status_code=status.HTTP_200_OK,
)
async def get_candidates_by_election(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    service: CandidateService = Depends(get_candidate_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[CandidateItem]:
    """Get all candidates standing in an election."""
    return await service.get_candidates_by_election(election_id)


# Create a candidate for an election (admin-only)
@router.post(
    "/{election_id}/candidates",
    responses=candidate_responses,
    response_model=CandidateItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_candidate(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    body: CreateCandidateRequest = Body(..., description="The candidate creation request."),
    service: CandidateService = Depends(get_candidate_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Create a candidate for an election.

    Only one candidate per party per constituency per election is allowed.
    """
    dto = CreateCandidatePlainDTO.create_dto(body, election_id)
    return await service.create_candidate(dto)


# Update a candidate (admin-only)
@router.patch(
    "/{election_id}/candidates/{candidate_id}",
    responses=candidate_responses,
    response_model=CandidateItem,
    status_code=status.HTTP_200_OK,
)
async def update_candidate(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    candidate_id: UUID = Path(..., description="The unique identifier for the candidate."),
    body: UpdateCandidateRequest = Body(..., description="The candidate update request."),
    service: CandidateService = Depends(get_candidate_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Update a candidate's mutable fields (first_name, last_name, is_active)."""
    update_data = body.model_dump(exclude_none=True)
    return await service.update_candidate(candidate_id, update_data)


# ── Ballot tokens ──


# Issue ballot tokens for an election (admin-only)
@router.post(
    "/{election_id}/ballot-tokens",
    responses=ballot_responses,
    response_model=IssueBallotTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_election_ballot_tokens(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    body: IssueBallotTokenRequest = Body(
        ..., description="Request to issue election ballot tokens."
    ),
    service: BallotTokenService = Depends(get_ballot_token_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """Issue one-time ballot tokens for an election + constituency.

    Each token can be distributed to an eligible voter. The voter uses the
    ``blind_token_hash`` when casting their vote.
    """
    body.election_id = str(election_id)
    return await service.issue_election_tokens(body)


# Get ballot token status for an election (any official)
@router.get(
    "/{election_id}/ballot-tokens/status",
    responses=ballot_responses,
    response_model=BallotTokenStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_election_ballot_token_status(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    constituency_id: Optional[UUID] = Query(
        None, description="Optional constituency filter."
    ),
    service: BallotTokenService = Depends(get_ballot_token_service),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get total/used/unused token counts for an election."""
    return await service.get_election_token_status(election_id, constituency_id)


# List all ballot tokens for an election (admin-only)
@router.get(
    "/{election_id}/ballot-tokens",
    responses=ballot_responses,
    response_model=List[BallotTokenItem],
    status_code=status.HTTP_200_OK,
)
async def get_election_ballot_tokens(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    constituency_id: Optional[UUID] = Query(
        None, description="Optional constituency filter."
    ),
    service: BallotTokenService = Depends(get_ballot_token_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
):
    """List all ballot tokens for an election (decrypted)."""
    return await service.get_election_tokens(election_id, constituency_id)


# ── Results & tallies ──


# Get aggregated election results (any official)
@router.get(
    "/{election_id}/results",
    responses=election_responses,
    response_model=ElectionResultResponse,
    status_code=status.HTTP_200_OK,
)
async def get_election_results(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    service: ResultService = Depends(get_result_service),
    current_user: TokenPayload = Depends(get_current_user),
) -> ElectionResultResponse:
    """Get aggregated results for an election with per-constituency breakdowns and seat allocation."""
    return await service.get_election_results(election_id)


# Get tallies for an election (admin-only)
@router.get(
    "/{election_id}/tallies",
    responses=election_responses,
    response_model=List[TallyResultItem],
    status_code=status.HTTP_200_OK,
)
async def get_election_tallies(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    service: TallyService = Depends(get_tally_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[TallyResultItem]:
    """Get all vote tallies for an election, ordered by vote count."""
    return await service.get_tallies_by_election(election_id)


# Get tallies for an election + constituency (admin-only)
@router.get(
    "/{election_id}/constituency/{constituency_id}/tallies",
    responses=election_responses,
    response_model=List[TallyResultItem],
    status_code=status.HTTP_200_OK,
)
async def get_election_constituency_tallies(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    constituency_id: UUID = Path(..., description="The constituency ID."),
    service: TallyService = Depends(get_tally_service),
    current_user: TokenPayload = Depends(require_role("ADMIN")),
) -> List[TallyResultItem]:
    """Get vote tallies for a specific constituency within an election."""
    return await service.get_tallies_by_constituency(election_id, constituency_id)
