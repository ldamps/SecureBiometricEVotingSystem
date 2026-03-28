# app/models/schemas/ballot_token.py - Pydantic schemas for ballot token operations.

from datetime import datetime
from typing import Optional, List

from pydantic import Field

from app.models.base.pydantic_base import RequestSchema, ResponseSchema


# ── Issue tokens ──


class IssueBallotTokenRequest(RequestSchema):
    """Request to issue ballot tokens for an election."""
    election_id: Optional[str] = Field(None, description="The election to issue tokens for (set from path if omitted).")
    constituency_id: str = Field(..., description="The constituency to issue tokens for.")
    count: int = Field(..., ge=1, le=10000, description="Number of tokens to generate (1–10 000).")


class IssueBallotTokenResponse(ResponseSchema):
    """Response after successfully issuing ballot tokens."""
    election_id: str = Field(..., description="The election the tokens were issued for.")
    constituency_id: str = Field(..., description="The constituency the tokens were issued for.")
    tokens_issued: int = Field(..., description="Number of tokens successfully created.")
    blind_token_hashes: List[str] = Field(..., description="The generated blind token hashes (distribute to eligible voters).")


class IssueReferendumBallotTokenRequest(RequestSchema):
    """Request to issue ballot tokens for a referendum."""
    referendum_id: Optional[str] = Field(None, description="The referendum to issue tokens for (set from path if omitted).")
    count: int = Field(..., ge=1, le=10000, description="Number of tokens to generate (1–10 000).")


class IssueReferendumBallotTokenResponse(ResponseSchema):
    """Response after successfully issuing referendum ballot tokens."""
    referendum_id: str = Field(..., description="The referendum the tokens were issued for.")
    tokens_issued: int = Field(..., description="Number of tokens successfully created.")
    blind_token_hashes: List[str] = Field(..., description="The generated blind token hashes (distribute to eligible voters).")


# ── Query tokens ──


class BallotTokenItem(ResponseSchema):
    """A single ballot token record."""
    id: str = Field(..., description="Token primary key.")
    election_id: Optional[str] = Field(None, description="Election ID (null for referendum tokens).")
    constituency_id: Optional[str] = Field(None, description="Constituency ID (null for referendum tokens).")
    referendum_id: Optional[str] = Field(None, description="Referendum ID (null for election tokens).")
    blind_token_hash: str = Field(..., description="The blind token hash.")
    is_used: bool = Field(..., description="Whether the token has been consumed.")
    issued_at: Optional[datetime] = Field(None, description="When the token was issued.")
    used_at: Optional[datetime] = Field(None, description="When the token was consumed (null if unused).")


class BallotTokenStatusResponse(ResponseSchema):
    """Summary of ballot token status for an election or referendum."""
    total: int = Field(..., description="Total tokens issued.")
    used: int = Field(..., description="Tokens that have been used.")
    unused: int = Field(..., description="Tokens still available.")
