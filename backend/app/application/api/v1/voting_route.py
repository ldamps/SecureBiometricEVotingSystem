# app/application/api/v1/voting_route.py - Voting route definitions

import structlog
from fastapi import APIRouter, Body, Depends, status

from app.application.api.dependencies import get_voting_service
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.schemas.vote import (
    CastReferendumVoteRequest,
    CastReferendumVoteResponse,
    CastVoteRequest,
    CastVoteResponse,
)
from app.service.voting_service import VotingService

voting_responses = responses(Resource.VOTE)
logger = structlog.get_logger()


### ROUTES ###
router = APIRouter(
    prefix="/voting",
    tags=["voting"],
)


# Cast a vote in an election
@router.post(
    "/cast",
    responses=voting_responses,
    response_model=CastVoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def cast_vote(
    body: CastVoteRequest = Body(..., description="The vote casting request."),
    service: VotingService = Depends(get_voting_service),
):
    """Cast a vote in an election.

    Each voter may vote exactly once per election. Votes are anonymous —
    the voter's identity is recorded in the Voter Ledger (participation only),
    but is NOT stored on the vote itself.

    Once submitted, the vote cannot be changed or revoked.
    """
    return await service.cast_vote(body)


# Cast a vote on a referendum
@router.post(
    "/cast-referendum",
    responses=voting_responses,
    response_model=CastReferendumVoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def cast_referendum_vote(
    body: CastReferendumVoteRequest = Body(..., description="The referendum vote casting request."),
    service: VotingService = Depends(get_voting_service),
):
    """Cast a vote on a referendum (YES or NO).

    Each voter may vote exactly once per referendum. Votes are anonymous —
    the voter's identity is recorded in the Voter Ledger (participation only),
    but is NOT stored on the vote itself.

    Once submitted, the vote cannot be changed or revoked.
    """
    return await service.cast_referendum_vote(body)
