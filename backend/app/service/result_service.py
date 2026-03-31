# result_service.py - Service layer for computing aggregated election/referendum results.

from collections import defaultdict
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dto.result import (
    ConstituencyResultDTO,
    ElectionResultDTO,
    ReferendumResultDTO,
)
from app.models.dto.tally_result import TallyResultDTO
from app.models.schemas.result import ElectionResultResponse, ReferendumResultResponse
from app.repository.election_repo import ElectionRepository
from app.repository.tally_result_repo import TallyResultRepository

logger = structlog.get_logger()


class ResultService:
    """Computes aggregated results from tally data.

    Election results use First Past The Post (FPTP):
    the candidate with the most votes in each constituency wins the seat.
    """

    def __init__(
        self,
        tally_result_repo: TallyResultRepository,
        election_repo: ElectionRepository,
        session: AsyncSession,
    ):
        self.tally_result_repo = tally_result_repo
        self.election_repo = election_repo
        self.session = session

    async def get_election_results(self, election_id: UUID) -> ElectionResultResponse:
        """Aggregate tallies into a full election result with seat allocation."""
        election = await self.election_repo.get_election_by_id(self.session, election_id)

        tallies = await self.tally_result_repo.get_tallies_by_election(
            self.session, election_id,
        )

        # Group tallies by constituency
        by_constituency: dict[UUID, list] = defaultdict(list)
        for t in tallies:
            if t.constituency_id:
                by_constituency[t.constituency_id].append(t)

        # Build per-constituency results (FPTP: highest vote count wins)
        constituency_results = []
        seat_allocation: dict[str, int] = defaultdict(int)
        total_votes = 0

        for cid, constituency_tallies in by_constituency.items():
            tally_dtos = [TallyResultDTO.from_model(t) for t in constituency_tallies]
            constituency_total = sum(t.vote_count for t in tally_dtos)
            total_votes += constituency_total

            # Winner = candidate with most votes in this constituency
            winner_dto = max(tally_dtos, key=lambda t: t.vote_count) if tally_dtos else None

            cr = ConstituencyResultDTO(
                constituency_id=cid,
                winner_candidate_id=winner_dto.candidate_id if winner_dto else None,
                total_votes=constituency_total,
                tallies=tally_dtos,
            )
            constituency_results.append(cr)

            # Allocate seat to winner's party (looked up from candidate)
            if winner_dto and winner_dto.candidate_id:
                # We don't have party_id on tally; this maps candidate -> seat
                seat_allocation[str(winner_dto.candidate_id)] = (
                    seat_allocation.get(str(winner_dto.candidate_id), 0) + 1
                )

        result = ElectionResultDTO(
            election_id=election_id,
            election_title=getattr(election, "title", None),
            status=election.status,
            total_votes=total_votes,
            constituencies=constituency_results,
            seat_allocation=dict(seat_allocation),
        )
        return result.to_schema()

    async def get_referendum_results(self, referendum_id: UUID) -> ReferendumResultResponse:
        """Aggregate YES/NO tallies into a referendum result."""
        tallies = await self.tally_result_repo.get_tallies_by_referendum(
            self.session, referendum_id,
        )

        yes_votes = 0
        no_votes = 0
        for t in tallies:
            if t.choice == "YES":
                yes_votes += t.vote_count
            elif t.choice == "NO":
                no_votes += t.vote_count

        total = yes_votes + no_votes
        if yes_votes > no_votes:
            outcome = "YES"
        elif no_votes > yes_votes:
            outcome = "NO"
        else:
            outcome = "TIE"

        result = ReferendumResultDTO(
            referendum_id=referendum_id,
            yes_votes=yes_votes,
            no_votes=no_votes,
            total_votes=total,
            outcome=outcome,
        )
        return result.to_schema()
