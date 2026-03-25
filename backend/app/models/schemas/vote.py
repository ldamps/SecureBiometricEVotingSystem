# app/models/schemas/vote.py - Pydantic schemas for voting operations.

from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from datetime import datetime
from typing import Optional


class CastVoteRequest(RequestSchema):
    """Request to cast a vote in an election."""
    voter_id: str = Field(..., description="The voter's unique identifier (used only to check eligibility and create ledger entry, NOT stored on the vote).")
    election_id: str = Field(..., description="The election to vote in.")
    constituency_id: str = Field(..., description="The constituency the voter is voting in.")
    candidate_id: str = Field(..., description="The candidate to vote for.")
    blind_token_hash: str = Field(..., description="The blind ballot token hash issued to the voter.")
    send_email_confirmation: bool = Field(False, description="Whether to send an email confirmation of the vote.")


class CastVoteResponse(ResponseSchema):
    """Response after successfully casting a vote."""
    receipt_code: str = Field(..., description="A unique receipt code the voter can use to verify their vote was recorded.")
    election_id: str = Field(..., description="The election the vote was cast in.")
    constituency_id: str = Field(..., description="The constituency the vote was cast in.")
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
