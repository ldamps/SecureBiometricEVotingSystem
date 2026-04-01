# app/models/schemas/vote.py - Pydantic schemas for voting operations.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from datetime import datetime
from typing import List, Optional


# ── Ranked preference item (STV / AV) ──

class RankedPreference(RequestSchema):
    """A single preference in a ranked ballot (STV or Alternative Vote)."""
    candidate_id: str = Field(..., description="The candidate being ranked.")
    preference_rank: int = Field(..., ge=1, description="Rank (1 = first choice, 2 = second, …).")


# ── Election vote requests ──

class CastVoteRequest(RequestSchema):
    """Request to cast a vote in an election.

    Which fields are required depends on the election's allocation method:
    - FPTP: candidate_id required.
    - AMS: candidate_id (constituency vote) and/or party_id (regional list vote).
    - STV / AV: ranked_preferences required (list of candidate + rank).
    """
    voter_id: str = Field(..., description="The voter's unique identifier (used only to check eligibility and create ledger entry, NOT stored on the vote).")
    election_id: str = Field(..., description="The election to vote in.")
    constituency_id: Optional[str] = Field(None, description="The constituency the voter is voting in.")
    candidate_id: Optional[str] = Field(None, description="The candidate to vote for (FPTP / AMS constituency vote).")
    party_id: Optional[str] = Field(None, description="The party to vote for (AMS regional list vote).")
    ranked_preferences: Optional[List[RankedPreference]] = Field(None, description="Ranked candidate preferences (STV / Alternative Vote).")
    blind_token_hash: str = Field(..., description="The blind ballot token hash issued to the voter.")
    send_email_confirmation: bool = Field(False, description="Whether to send an email confirmation of the vote.")


class CastVoteResponse(ResponseSchema):
    """Response after successfully casting a vote."""
    receipt_code: str = Field(..., description="A unique receipt code the voter can use to verify their vote was recorded.")
    election_id: str = Field(..., description="The election the vote was cast in.")
    constituency_id: Optional[str] = Field(None, description="The constituency the vote was cast in.")
    cast_at: Optional[datetime] = Field(None, description="The date and time the vote was cast.")
    message: str = Field(..., description="A confirmation message.")


# ── Referendum voting ──


class CastReferendumVoteRequest(RequestSchema):
    """Request to cast a vote on a referendum (YES or NO)."""
    voter_id: str = Field(..., description="The voter's unique identifier (used only to check eligibility and create ledger entry, NOT stored on the vote).")
    referendum_id: str = Field(..., description="The referendum to vote on.")
    choice: str = Field(..., description="The voter's choice: 'YES' or 'NO'.", pattern="^(YES|NO)$")
    blind_token_hash: str = Field(..., description="The blind ballot token hash issued to the voter.")
    send_email_confirmation: bool = Field(False, description="Whether to send an email confirmation of the vote.")


class CastReferendumVoteResponse(ResponseSchema):
    """Response after successfully casting a referendum vote."""
    receipt_code: str = Field(..., description="A unique receipt code the voter can use to verify their vote was recorded.")
    referendum_id: str = Field(..., description="The referendum the vote was cast on.")
    cast_at: Optional[datetime] = Field(None, description="The date and time the vote was cast.")
    message: str = Field(..., description="A confirmation message.")
