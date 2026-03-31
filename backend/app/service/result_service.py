# result_service.py - Service layer for computing aggregated election/referendum results.
# UK FPTP: each constituency elects one MP. The party winning 326+/650 seats
# forms the government; fewer than that is a hung parliament.

from collections import defaultdict
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dto.result import (
    ConstituencyResultDTO,
    ElectionResultDTO,
    ReferendumResultDTO,
)
from app.models.dto.tally_result import TallyResultDTO
from app.models.schemas.result import ElectionResultResponse, ReferendumResultResponse
from app.models.sqlalchemy.candidate import Candidate
from app.repository.election_repo import ElectionRepository
from app.repository.tally_result_repo import TallyResultRepository

logger = structlog.get_logger()


class ResultService:
    """Computes aggregated results from tally data.

    Uses First Past The Post (FPTP): the candidate with the most votes
    in each constituency wins that seat for their party.
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

    async def _load_candidate_party_map(
        self, candidate_ids: set[UUID],
    ) -> dict[UUID, UUID]:
        """Batch-load candidate -> party_id mapping."""
        if not candidate_ids:
            return {}
        result = await self.session.execute(
            select(Candidate.id, Candidate.party_id).where(
                Candidate.id.in_(candidate_ids)
            )
        )
        return {row.id: row.party_id for row in result.all()}

    async def get_election_results(self, election_id: UUID) -> ElectionResultResponse:
        """Aggregate tallies into a full election result with FPTP seat allocation."""
        election = await self.election_repo.get_election_by_id(self.session, election_id)

        tallies = await self.tally_result_repo.get_tallies_by_election(
            self.session, election_id,
        )

        # Group tallies by constituency
        by_constituency: dict[UUID, list] = defaultdict(list)
        for t in tallies:
            if t.constituency_id:
                by_constituency[t.constituency_id].append(t)

        # First pass: find the winning candidate in each constituency
        constituency_winners: dict[UUID, TallyResultDTO] = {}
        for cid, constituency_tallies in by_constituency.items():
            tally_dtos = [TallyResultDTO.from_model(t) for t in constituency_tallies]
            if tally_dtos:
                constituency_winners[cid] = max(tally_dtos, key=lambda t: t.vote_count)

        # Batch-load all winning candidates' party IDs
        winner_candidate_ids = {
            w.candidate_id for w in constituency_winners.values() if w.candidate_id
        }
        candidate_party_map = await self._load_candidate_party_map(winner_candidate_ids)

        # Second pass: build per-constituency results and allocate seats to parties
        constituency_results = []
        seat_allocation: dict[str, int] = defaultdict(int)
        total_votes = 0

        for cid, constituency_tallies in by_constituency.items():
            tally_dtos = [TallyResultDTO.from_model(t) for t in constituency_tallies]
            constituency_total = sum(t.vote_count for t in tally_dtos)
            total_votes += constituency_total

            winner = constituency_winners.get(cid)
            winner_party_id = (
                candidate_party_map.get(winner.candidate_id)
                if winner and winner.candidate_id
                else None
            )

            cr = ConstituencyResultDTO(
                constituency_id=cid,
                winner_candidate_id=winner.candidate_id if winner else None,
                winner_party_id=winner_party_id,
                total_votes=constituency_total,
                tallies=tally_dtos,
            )
            constituency_results.append(cr)

            # FPTP: one seat per constituency, awarded to the winner's party
            if winner_party_id:
                seat_allocation[str(winner_party_id)] += 1

        total_seats = len(by_constituency)
        majority_threshold = total_seats // 2 + 1

        # Determine if any party has a majority
        winning_party_id = None
        for party_id, seats in seat_allocation.items():
            if seats >= majority_threshold:
                winning_party_id = party_id
                break

        result = ElectionResultDTO(
            election_id=election_id,
            election_title=getattr(election, "title", None),
            status=election.status,
            total_votes=total_votes,
            total_seats=total_seats,
            majority_threshold=majority_threshold,
            constituencies=constituency_results,
            seat_allocation=dict(seat_allocation),
            winning_party_id=winning_party_id,
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
