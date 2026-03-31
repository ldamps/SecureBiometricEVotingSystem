# tally_service.py - Service layer for querying tally results.

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.models.dto.tally_result import TallyResultDTO
from app.models.schemas.tally_result import TallyResultItem
from app.repository.tally_result_repo import TallyResultRepository

logger = structlog.get_logger()


class TallyService:
    """Read-only service for querying tally results.

    Tally rows are incremented internally by the voting service;
    this service only exposes query endpoints.
    """

    def __init__(
        self,
        tally_result_repo: TallyResultRepository,
        session: AsyncSession,
    ):
        self.tally_result_repo = tally_result_repo
        self.session = session

    async def get_tallies_by_election(self, election_id: UUID) -> List[TallyResultItem]:
        """Get all tallies for an election, ordered by vote count descending."""
        tallies = await self.tally_result_repo.get_tallies_by_election(
            self.session, election_id,
        )
        return [TallyResultDTO.from_model(t).to_schema() for t in tallies]

    async def get_tallies_by_constituency(
        self, election_id: UUID, constituency_id: UUID,
    ) -> List[TallyResultItem]:
        """Get tallies for an election + constituency."""
        tallies = await self.tally_result_repo.get_tallies_by_constituency(
            self.session, election_id, constituency_id,
        )
        return [TallyResultDTO.from_model(t).to_schema() for t in tallies]

    async def get_tallies_by_referendum(self, referendum_id: UUID) -> List[TallyResultItem]:
        """Get tallies for a referendum (YES/NO counts)."""
        tallies = await self.tally_result_repo.get_tallies_by_referendum(
            self.session, referendum_id,
        )
        return [TallyResultDTO.from_model(t).to_schema() for t in tallies]
