"""Unit tests for election status transitions and the voting_window module."""

from datetime import datetime, timedelta, timezone

import pytest

from app.application.core.exceptions import ValidationError
from app.application.core.voting_window import (
    is_within_scheduled_voting_window,
    status_implied_by_voting_schedule,
    initial_status_from_voting_schedule,
)
from app.models.sqlalchemy.election import ElectionStatus


# ---------------------------------------------------------------------------
# is_within_scheduled_voting_window
# ---------------------------------------------------------------------------

class TestVotingWindow:
    def test_within_window_returns_true(self):
        now = datetime.now(timezone.utc)
        opens = now - timedelta(hours=1)
        closes = now + timedelta(hours=23)
        assert is_within_scheduled_voting_window(now, opens, closes) is True

    def test_before_window_opens_returns_false(self):
        now = datetime.now(timezone.utc)
        opens = now + timedelta(hours=1)
        closes = now + timedelta(hours=25)
        assert is_within_scheduled_voting_window(now, opens, closes) is False

    def test_after_window_closes_returns_false(self):
        now = datetime.now(timezone.utc)
        opens = now - timedelta(hours=25)
        closes = now - timedelta(hours=1)
        assert is_within_scheduled_voting_window(now, opens, closes) is False

    def test_no_opens_bound_only_closes(self):
        now = datetime.now(timezone.utc)
        closes = now + timedelta(hours=1)
        assert is_within_scheduled_voting_window(now, None, closes) is True

    def test_no_closes_bound_only_opens(self):
        now = datetime.now(timezone.utc)
        opens = now - timedelta(hours=1)
        assert is_within_scheduled_voting_window(now, opens, None) is True

    def test_no_bounds_at_all_returns_true(self):
        now = datetime.now(timezone.utc)
        assert is_within_scheduled_voting_window(now, None, None) is True

    def test_exactly_at_opens_returns_true(self):
        now = datetime.now(timezone.utc)
        assert is_within_scheduled_voting_window(now, now, now + timedelta(hours=1)) is True

    def test_exactly_at_closes_returns_true(self):
        now = datetime.now(timezone.utc)
        assert is_within_scheduled_voting_window(now, now - timedelta(hours=1), now) is True


# ---------------------------------------------------------------------------
# status_implied_by_voting_schedule
# ---------------------------------------------------------------------------

class TestStatusImpliedBySchedule:
    def test_within_window_implies_open(self):
        now = datetime.now(timezone.utc)
        opens = now - timedelta(hours=1)
        closes = now + timedelta(hours=1)
        assert status_implied_by_voting_schedule(now, opens, closes) == "OPEN"

    def test_after_window_implies_closed(self):
        now = datetime.now(timezone.utc)
        opens = now - timedelta(hours=2)
        closes = now - timedelta(hours=1)
        assert status_implied_by_voting_schedule(now, opens, closes) == "CLOSED"

    def test_before_window_implies_closed(self):
        now = datetime.now(timezone.utc)
        opens = now + timedelta(hours=1)
        closes = now + timedelta(hours=2)
        assert status_implied_by_voting_schedule(now, opens, closes) == "CLOSED"

    def test_no_schedule_returns_none(self):
        now = datetime.now(timezone.utc)
        assert status_implied_by_voting_schedule(now, None, None) is None


# ---------------------------------------------------------------------------
# initial_status_from_voting_schedule
# ---------------------------------------------------------------------------

class TestInitialStatus:
    def test_within_window_starts_open(self):
        now = datetime.now(timezone.utc)
        opens = now - timedelta(hours=1)
        closes = now + timedelta(hours=1)
        assert initial_status_from_voting_schedule(now, opens, closes) == "OPEN"

    def test_no_schedule_starts_closed(self):
        now = datetime.now(timezone.utc)
        assert initial_status_from_voting_schedule(now, None, None) == "CLOSED"


# ---------------------------------------------------------------------------
# Election status transition validation (testing the rules directly)
# ---------------------------------------------------------------------------

# Import the transition map from the service
from app.service.election_service import _VALID_TRANSITIONS


class TestElectionStatusTransitions:
    """Verify the status transition rules for elections."""

    def test_draft_can_go_to_open(self):
        assert ElectionStatus.OPEN.value in _VALID_TRANSITIONS[ElectionStatus.DRAFT.value]

    def test_draft_can_go_to_cancelled(self):
        assert ElectionStatus.CANCELLED.value in _VALID_TRANSITIONS[ElectionStatus.DRAFT.value]

    def test_draft_cannot_go_to_closed(self):
        assert ElectionStatus.CLOSED.value not in _VALID_TRANSITIONS[ElectionStatus.DRAFT.value]

    def test_open_can_go_to_closed(self):
        assert ElectionStatus.CLOSED.value in _VALID_TRANSITIONS[ElectionStatus.OPEN.value]

    def test_open_can_go_to_draft(self):
        assert ElectionStatus.DRAFT.value in _VALID_TRANSITIONS[ElectionStatus.OPEN.value]

    def test_open_can_go_to_cancelled(self):
        assert ElectionStatus.CANCELLED.value in _VALID_TRANSITIONS[ElectionStatus.OPEN.value]

    def test_closed_can_reopen(self):
        assert ElectionStatus.OPEN.value in _VALID_TRANSITIONS[ElectionStatus.CLOSED.value]

    def test_closed_can_go_to_cancelled(self):
        assert ElectionStatus.CANCELLED.value in _VALID_TRANSITIONS[ElectionStatus.CLOSED.value]

    def test_cancelled_is_terminal(self):
        assert ElectionStatus.CANCELLED.value not in _VALID_TRANSITIONS

    def test_invalid_transition_not_in_allowed_set(self):
        # DRAFT -> CLOSED is not allowed
        allowed = _VALID_TRANSITIONS.get(ElectionStatus.DRAFT.value, set())
        assert ElectionStatus.CLOSED.value not in allowed
