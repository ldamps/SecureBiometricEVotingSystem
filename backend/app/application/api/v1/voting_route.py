# app/application/api/v1/voting_route.py - Voting route definitions

import structlog
from uuid import UUID
from fastapi import APIRouter, Body, Depends, status

from app.application.api.dependencies import get_ballot_token_service, get_voting_service
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.schemas.vote import (
    CastReferendumVoteRequest,
    CastReferendumVoteResponse,
    CastVoteRequest,
    CastVoteResponse,
    VoterCastVoteRequest,
    VoterCastVoteResponse,
    VoterCastReferendumVoteRequest,
    VoterCastReferendumVoteResponse,
)
from app.service.voting_service import VotingService
from app.service.ballot_service import BallotTokenService

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


# ── Voter-facing: auto-issues ballot token + casts vote in one step ──


@router.post(
    "/vote",
    responses=voting_responses,
    response_model=VoterCastVoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def voter_cast_vote(
    body: VoterCastVoteRequest = Body(..., description="Voter-facing vote request."),
    ballot_service: BallotTokenService = Depends(get_ballot_token_service),
    voting_service: VotingService = Depends(get_voting_service),
):
    """Voter-facing endpoint: issues a ballot token and casts the vote in one step."""
    constituency_id = UUID(body.constituency_id) if body.constituency_id else None
    token = await ballot_service.issue_voter_election_token(
        election_id=UUID(body.election_id),
        constituency_id=constituency_id,
    )
    result = await voting_service.cast_vote(CastVoteRequest(
        voter_id=body.voter_id,
        election_id=body.election_id,
        constituency_id=body.constituency_id,
        candidate_id=body.candidate_id,
        party_id=body.party_id,
        ranked_preferences=body.ranked_preferences,
        blind_token_hash=token,
        send_email_confirmation=body.send_email_confirmation,
    ))
    return VoterCastVoteResponse(
        receipt_code=result.receipt_code,
        election_id=result.election_id,
        cast_at=result.cast_at,
        message=result.message,
    )


@router.post(
    "/vote-referendum",
    responses=voting_responses,
    response_model=VoterCastReferendumVoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def voter_cast_referendum_vote(
    body: VoterCastReferendumVoteRequest = Body(..., description="Voter-facing referendum vote request."),
    ballot_service: BallotTokenService = Depends(get_ballot_token_service),
    voting_service: VotingService = Depends(get_voting_service),
):
    """Voter-facing endpoint: issues a ballot token and casts the referendum vote in one step."""
    token = await ballot_service.issue_voter_referendum_token(
        referendum_id=UUID(body.referendum_id),
    )
    result = await voting_service.cast_referendum_vote(CastReferendumVoteRequest(
        voter_id=body.voter_id,
        referendum_id=body.referendum_id,
        choice=body.choice,
        blind_token_hash=token,
        send_email_confirmation=body.send_email_confirmation,
    ))
    return VoterCastReferendumVoteResponse(
        receipt_code=result.receipt_code,
        referendum_id=result.referendum_id,
        cast_at=result.cast_at,
        message=result.message,
    )
