# app/application/api/v1/election_route.py - Election endpoints.

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from app.application.api.dependencies import get_ballot_token_service, get_candidate_service, get_election_service, get_voter_ledger_service
from app.application.api.responses import responses
from app.application.constants import Resource
from app.application.core.exceptions import NotFoundError, ValidationError
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
from app.models.schemas.voter_ledger import ElectionVoterListResponse
from app.service.ballot_service import BallotTokenService
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


# List all voters for an election with voting status
@router.get(
    "/{election_id}/voters",
    responses=election_responses,
    response_model=ElectionVoterListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_election_voters(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    service: VoterLedgerService = Depends(get_voter_ledger_service),
) -> ElectionVoterListResponse:
    """List all voters registered for an election and whether they have voted."""
    return await service.get_election_voters(election_id)


# Get all candidates for an election
@router.get(
    "/{election_id}/candidates",
    responses=candidate_responses,
    response_model=List[CandidateItem],
    status_code=status.HTTP_200_OK,
)
async def get_candidates_by_election(
    election_id: UUID = Path(..., description="The unique identifier for the election."),
    service: CandidateService = Depends(get_candidate_service),
) -> List[CandidateItem]:
    """Get all candidates standing in an election."""
    return await service.get_candidates_by_election(election_id)


# Create a candidate for an election
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
):
    """Create a candidate for an election.

    Only one candidate per party per constituency per election is allowed.
    """
    try:
        dto = CreateCandidatePlainDTO.create_dto(body, election_id)
        return await service.create_candidate(dto)
    except ValidationError as e:
        return JSONResponse(status_code=409, content={"detail": str(e)})


# Update a candidate
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
):
    """Update a candidate's mutable fields (first_name, last_name, is_active)."""
    update_data = body.model_dump(exclude_none=True)
    return await service.update_candidate(candidate_id, update_data)


# ── Ballot tokens ──


# Issue ballot tokens for an election
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
):
    """Issue one-time ballot tokens for an election + constituency.

    Each token can be distributed to an eligible voter. The voter uses the
    ``blind_token_hash`` when casting their vote.
    """
    try:
        body.election_id = str(election_id)
        return await service.issue_election_tokens(body)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Get ballot token status for an election
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
):
    """Get total/used/unused token counts for an election."""
    try:
        return await service.get_election_token_status(election_id, constituency_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all ballot tokens for an election
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
):
    """List all ballot tokens for an election (decrypted)."""
    try:
        return await service.get_election_tokens(election_id, constituency_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
