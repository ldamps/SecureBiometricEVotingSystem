"""Shared test fixtures for the Secure Biometric E-Voting System backend."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from argon2 import PasswordHasher

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


# ---------------------------------------------------------------------------
# Common test data factories
# ---------------------------------------------------------------------------

def make_uuid() -> uuid.UUID:
    return uuid.uuid4()


def make_official(
    *,
    official_id: uuid.UUID | None = None,
    username: str = "admin",
    password: str = "SecurePass123!",
    role: str = "ADMIN",
    is_active: bool = True,
    failed_login_attempts: int = 0,
    locked_until: datetime | None = None,
    must_reset_password: bool = False,
):
    """Create a mock ElectionOfficial ORM-like object."""
    obj = MagicMock()
    obj.id = official_id or make_uuid()
    obj.username = username
    obj.password_hash = _ph.hash(password)
    obj.role = role
    obj.is_active = is_active
    obj.failed_login_attempts = failed_login_attempts
    obj.locked_until = locked_until
    obj.must_reset_password = must_reset_password
    obj.last_login_at = None
    return obj


def make_election(
    *,
    election_id: uuid.UUID | None = None,
    title: str = "General Election 2026",
    election_type: str = "GENERAL",
    scope: str = "NATIONAL",
    allocation_method: str = "FPTP",
    status: str = "OPEN",
    voting_opens: datetime | None = None,
    voting_closes: datetime | None = None,
):
    """Create a mock Election ORM-like object."""
    now = datetime.now(timezone.utc)
    obj = MagicMock()
    obj.id = election_id or make_uuid()
    obj.title = title
    obj.election_type = election_type
    obj.scope = scope
    obj.allocation_method = allocation_method
    obj.status = status
    obj.voting_opens = voting_opens or (now - timedelta(hours=1))
    obj.voting_closes = voting_closes or (now + timedelta(hours=23))
    obj.constituencies = []
    return obj


def make_ballot_token(
    *,
    token_id: uuid.UUID | None = None,
    election_id: uuid.UUID | None = None,
    constituency_id: uuid.UUID | None = None,
    referendum_id: uuid.UUID | None = None,
    is_used: bool = False,
):
    """Create a mock BallotToken ORM-like object."""
    obj = MagicMock()
    obj.id = token_id or make_uuid()
    obj.election_id = election_id
    obj.constituency_id = constituency_id
    obj.referendum_id = referendum_id
    obj.is_used = is_used
    return obj


def make_voter(
    *,
    voter_id: uuid.UUID | None = None,
    voter_status: str = "ACTIVE",
):
    """Create a mock Voter ORM-like object."""
    obj = MagicMock()
    obj.id = voter_id or make_uuid()
    obj.voter_status = voter_status
    return obj


# ---------------------------------------------------------------------------
# Async mock session
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    """An AsyncMock that stands in for an AsyncSession."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session
