"""Align persisted OPEN/CLOSED with voting_opens / voting_closes when they disagree."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.voting_window import (
    CANCELLED_STATUS,
    status_implied_by_voting_schedule,
)
from app.models.dto.election import UpdateElectionPlainDTO
from app.models.sqlalchemy.election import Election
from app.models.sqlalchemy.referendum import Referendum
from app.repository.election_repo import ElectionRepository
from app.repository.referendum_repo import ReferendumRepository

logger = structlog.get_logger()


async def sync_election_status_with_voting_schedule(
    session: AsyncSession,
    repo: ElectionRepository,
    election: Election,
) -> Election:
    """If schedule implies a different status than stored, persist the update."""
    if election.status == CANCELLED_STATUS:
        return election
    now = datetime.now(timezone.utc)
    desired = status_implied_by_voting_schedule(
        now, election.voting_opens, election.voting_closes
    )
    if desired is None or election.status == desired:
        return election
    updated = await repo.update_election(
        session,
        election.id,
        UpdateElectionPlainDTO(status=desired),
    )
    logger.info(
        "Election status synced with voting schedule",
        election_id=str(election.id),
        previous_status=election.status,
        new_status=desired,
    )
    return updated


async def sync_referendum_status_with_voting_schedule(
    session: AsyncSession,
    repo: ReferendumRepository,
    referendum: Referendum,
) -> Referendum:
    """If schedule implies a different status than stored, persist the update."""
    if referendum.status == CANCELLED_STATUS:
        return referendum
    now = datetime.now(timezone.utc)
    desired = status_implied_by_voting_schedule(
        now, referendum.voting_opens, referendum.voting_closes
    )
    if desired is None or referendum.status == desired:
        return referendum
    updated = await repo.update_referendum(
        session,
        referendum.id,
        {"status": desired},
    )
    logger.info(
        "Referendum status synced with voting schedule",
        referendum_id=str(referendum.id),
        previous_status=referendum.status,
        new_status=desired,
    )
    return updated
