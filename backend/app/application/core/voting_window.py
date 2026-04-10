"""Scheduled voting window helpers (election / referendum)."""

from __future__ import annotations

from datetime import datetime

# Matches ElectionStatus / referendum status string values in the DB.
DRAFT_STATUS = "DRAFT"
OPEN_STATUS = "OPEN"
CLOSED_STATUS = "CLOSED"
CANCELLED_STATUS = "CANCELLED"


def is_within_scheduled_voting_window(
    now: datetime,
    voting_opens: datetime | None,
    voting_closes: datetime | None,
) -> bool:
    """True when ``now`` is inside the configured window.

    - If ``voting_opens`` is set: ``now`` must be >= that instant.
    - If ``voting_closes`` is set: ``now`` must be <= that instant.
    - Unset bounds are treated as no constraint on that side.
    """
    if voting_opens is not None and now < voting_opens:
        return False
    if voting_closes is not None and now > voting_closes:
        return False
    return True


def status_implied_by_voting_schedule(
    now: datetime,
    voting_opens: datetime | None,
    voting_closes: datetime | None,
) -> str | None:
    """OPEN/CLOSED implied by the schedule, or None if there is no schedule to infer from.

    When both ``voting_opens`` and ``voting_closes`` are unset, returns None so callers
    keep the stored status unchanged.
    """
    if voting_opens is None and voting_closes is None:
        return None
    if is_within_scheduled_voting_window(now, voting_opens, voting_closes):
        return OPEN_STATUS
    return CLOSED_STATUS


def initial_status_from_voting_schedule(
    now: datetime,
    voting_opens: datetime | None,
    voting_closes: datetime | None,
) -> str:
    """Status to store on create when the client does not send ``status``.

    Derived from ``voting_opens`` / ``voting_closes`` when at least one is set;
    otherwise ``CLOSED`` (no voting window configured).
    """
    implied = status_implied_by_voting_schedule(now, voting_opens, voting_closes)
    if implied is not None:
        return implied
    return CLOSED_STATUS
