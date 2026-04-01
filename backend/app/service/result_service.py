# result_service.py - Service layer for computing aggregated election/referendum results.
# Supports UK electoral systems: FPTP, AMS, STV, AV.

from collections import defaultdict
from copy import deepcopy
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
from app.models.sqlalchemy.election import AllocationMethod
from app.models.sqlalchemy.vote import Vote
from app.repository.election_repo import ElectionRepository
from app.repository.tally_result_repo import TallyResultRepository

logger = structlog.get_logger()


class ResultService:
    """Computes aggregated results from tally data.

    Dispatches to the correct counting algorithm based on the
    election's allocation_method.
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

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def get_election_results(self, election_id: UUID) -> ElectionResultResponse:
        """Aggregate tallies into a full election result using the appropriate electoral system."""
        election = await self.election_repo.get_election_by_id(self.session, election_id)
        method = election.allocation_method

        if method == AllocationMethod.AMS.value:
            return await self._results_ams(election)
        elif method == AllocationMethod.STV.value:
            return await self._results_stv(election)
        elif method == AllocationMethod.ALTERNATIVE_VOTE.value:
            return await self._results_av(election)
        else:
            return await self._results_fptp(election)

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

    def _build_constituency_results(
        self,
        by_constituency: dict[UUID, list],
        candidate_party_map: dict[UUID, UUID],
    ) -> tuple[list[ConstituencyResultDTO], dict[str, int], int]:
        """Build per-constituency results and FPTP seat allocation.

        Returns (constituency_results, seat_allocation, total_votes).
        """
        constituency_results = []
        seat_allocation: dict[str, int] = defaultdict(int)
        total_votes = 0

        for cid, constituency_tallies in by_constituency.items():
            tally_dtos = [TallyResultDTO.from_model(t) for t in constituency_tallies]
            constituency_total = sum(t.vote_count for t in tally_dtos)
            total_votes += constituency_total

            winner = max(tally_dtos, key=lambda t: t.vote_count) if tally_dtos else None
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

            if winner_party_id:
                seat_allocation[str(winner_party_id)] += 1

        return constituency_results, dict(seat_allocation), total_votes

    # ------------------------------------------------------------------
    # FPTP — First Past The Post
    # ------------------------------------------------------------------

    async def _results_fptp(self, election) -> ElectionResultResponse:
        """Each constituency elects one seat; candidate with most votes wins."""
        election_id = election.id
        tallies = await self.tally_result_repo.get_tallies_by_election(
            self.session, election_id,
        )

        by_constituency: dict[UUID, list] = defaultdict(list)
        for t in tallies:
            if t.constituency_id:
                by_constituency[t.constituency_id].append(t)

        all_candidate_ids = {t.candidate_id for t in tallies if t.candidate_id}
        candidate_party_map = await self._load_candidate_party_map(all_candidate_ids)

        constituency_results, seat_allocation, total_votes = (
            self._build_constituency_results(by_constituency, candidate_party_map)
        )

        total_seats = len(by_constituency)
        majority_threshold = total_seats // 2 + 1

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
            seat_allocation=seat_allocation,
            winning_party_id=winning_party_id,
        )
        return result.to_schema()

    # ------------------------------------------------------------------
    # AMS — Additional Member System (Scottish Parliament, London Assembly)
    # ------------------------------------------------------------------

    async def _results_ams(self, election) -> ElectionResultResponse:
        """AMS: constituency seats via FPTP + top-up seats via D'Hondt on regional list votes.

        Constituency tallies have candidate_id set; regional tallies have party_id set.
        Top-up seats are allocated using the D'Hondt method to achieve proportionality.
        """
        election_id = election.id
        tallies = await self.tally_result_repo.get_tallies_by_election(
            self.session, election_id,
        )

        # Separate constituency (candidate) tallies from regional (party) tallies
        constituency_tallies: dict[UUID, list] = defaultdict(list)
        regional_party_votes: dict[str, int] = defaultdict(int)

        for t in tallies:
            if t.candidate_id and t.constituency_id:
                constituency_tallies[t.constituency_id].append(t)
            elif t.party_id:
                regional_party_votes[str(t.party_id)] += t.vote_count

        # FPTP constituency seats
        all_candidate_ids = {
            t.candidate_id for ts in constituency_tallies.values() for t in ts if t.candidate_id
        }
        candidate_party_map = await self._load_candidate_party_map(all_candidate_ids)

        constituency_results, fptp_seats, total_votes = (
            self._build_constituency_results(constituency_tallies, candidate_party_map)
        )

        # Add regional vote totals
        total_votes += sum(regional_party_votes.values())

        # D'Hondt top-up allocation
        # Number of top-up seats equals number of constituencies (standard AMS ratio)
        num_constituency_seats = len(constituency_tallies)
        num_topup_seats = num_constituency_seats

        topup_seats: dict[str, int] = defaultdict(int)
        if regional_party_votes and num_topup_seats > 0:
            party_constituency_seats = defaultdict(int, fptp_seats)
            for _ in range(num_topup_seats):
                # D'Hondt divisor: constituency_seats + topup_seats + 1
                best_party = max(
                    regional_party_votes.keys(),
                    key=lambda pid: regional_party_votes[pid] / (
                        party_constituency_seats[pid] + topup_seats[pid] + 1
                    ),
                )
                topup_seats[best_party] += 1

        # Combine seats
        combined_seats: dict[str, int] = defaultdict(int)
        for pid, s in fptp_seats.items():
            combined_seats[pid] += s
        for pid, s in topup_seats.items():
            combined_seats[pid] += s

        total_seats = num_constituency_seats + num_topup_seats
        majority_threshold = total_seats // 2 + 1

        winning_party_id = None
        for party_id, seats in combined_seats.items():
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
            seat_allocation=dict(combined_seats),
            winning_party_id=winning_party_id,
        )
        return result.to_schema()

    # ------------------------------------------------------------------
    # STV — Single Transferable Vote (NI Assembly, Scottish/NI local councils)
    # ------------------------------------------------------------------

    async def _results_stv(self, election) -> ElectionResultResponse:
        """STV: multi-seat constituencies with ranked preferences.

        Seats per constituency are filled by eliminating lowest candidates
        and transferring votes until all seats are allocated.
        The quota is calculated using the Droop quota: (votes / (seats + 1)) + 1.
        """
        election_id = election.id
        # For STV we need the raw ranked votes, not just tallies
        result = await self.session.execute(
            select(Vote).where(Vote.election_id == election_id).order_by(
                Vote.blind_token_hash, Vote.preference_rank
            )
        )
        votes = list(result.scalars().all())

        # Group votes by constituency, then by ballot (blind_token_hash prefix)
        ballots_by_constituency: dict[UUID, list[list[UUID]]] = defaultdict(list)
        ballot_buffer: dict[str, list[tuple[int, UUID]]] = defaultdict(list)

        for v in votes:
            if not v.constituency_id or not v.candidate_id or v.preference_rank is None:
                continue
            # Group by base token (strip :rankN suffix)
            base_token = v.blind_token_hash.split(":rank")[0]
            key = f"{v.constituency_id}:{base_token}"
            ballot_buffer[key].append((v.preference_rank, v.candidate_id))

        for key, prefs in ballot_buffer.items():
            cid_str = key.split(":")[0]
            cid = UUID(cid_str)
            ordered = [cand_id for _, cand_id in sorted(prefs, key=lambda x: x[0])]
            ballots_by_constituency[cid].append(ordered)

        # Load candidate -> party map
        all_candidate_ids = {
            cand_id for ballots in ballots_by_constituency.values()
            for ballot in ballots for cand_id in ballot
        }
        candidate_party_map = await self._load_candidate_party_map(all_candidate_ids)

        # STV counting per constituency
        # Default seats per constituency (configurable per election in future)
        seats_per_constituency = 5
        constituency_results = []
        seat_allocation: dict[str, int] = defaultdict(int)
        total_votes = 0

        for cid, ballots in ballots_by_constituency.items():
            total_votes += len(ballots)
            winners = self._stv_count(ballots, seats_per_constituency)

            # Build tally DTOs for display (first-preference counts)
            first_pref_counts: dict[UUID, int] = defaultdict(int)
            for ballot in ballots:
                if ballot:
                    first_pref_counts[ballot[0]] += 1
            tally_dtos = [
                TallyResultDTO(
                    id=None,
                    election_id=election_id,
                    constituency_id=cid,
                    candidate_id=cand_id,
                    vote_count=count,
                )
                for cand_id, count in sorted(
                    first_pref_counts.items(), key=lambda x: -x[1]
                )
            ]

            winner_candidate = winners[0] if winners else None
            winner_party_id = (
                candidate_party_map.get(winner_candidate) if winner_candidate else None
            )

            cr = ConstituencyResultDTO(
                constituency_id=cid,
                winner_candidate_id=winner_candidate,
                winner_party_id=winner_party_id,
                total_votes=len(ballots),
                tallies=tally_dtos,
            )
            constituency_results.append(cr)

            for w in winners:
                pid = candidate_party_map.get(w)
                if pid:
                    seat_allocation[str(pid)] += 1

        total_seats = sum(seat_allocation.values())
        majority_threshold = total_seats // 2 + 1

        winning_party_id = None
        for party_id, seats in seat_allocation.items():
            if seats >= majority_threshold:
                winning_party_id = party_id
                break

        result_dto = ElectionResultDTO(
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
        return result_dto.to_schema()

    @staticmethod
    def _stv_count(ballots: list[list[UUID]], seats: int) -> list[UUID]:
        """Run STV counting using the Droop quota.

        Returns a list of elected candidate UUIDs (up to ``seats``).
        """
        if not ballots:
            return []

        total_valid = len(ballots)
        quota = (total_valid // (seats + 1)) + 1

        # Each ballot carries a weight (starts at 1.0)
        weighted_ballots: list[tuple[list[UUID], float]] = [
            (list(b), 1.0) for b in ballots
        ]
        elected: list[UUID] = []
        eliminated: set[UUID] = set()

        while len(elected) < seats:
            # Count first-preference votes (weighted)
            counts: dict[UUID, float] = defaultdict(float)
            for prefs, weight in weighted_ballots:
                for cand in prefs:
                    if cand not in eliminated and cand not in elected:
                        counts[cand] += weight
                        break

            if not counts:
                break

            # Check if any candidate meets quota
            newly_elected = [c for c, v in counts.items() if v >= quota]
            if newly_elected:
                for c in newly_elected:
                    elected.append(c)
                    surplus = counts[c] - quota
                    transfer_ratio = surplus / counts[c] if counts[c] > 0 else 0
                    # Transfer surplus
                    for i, (prefs, weight) in enumerate(weighted_ballots):
                        active = [p for p in prefs if p not in eliminated and p not in elected]
                        if active and active[0] == c:
                            weighted_ballots[i] = (prefs, weight * transfer_ratio)
                    if len(elected) >= seats:
                        break
            else:
                # Eliminate lowest candidate
                lowest = min(counts, key=counts.get)
                eliminated.add(lowest)

        return elected[:seats]

    # ------------------------------------------------------------------
    # AV — Alternative Vote (House of Lords hereditary, Scottish Crofting)
    # ------------------------------------------------------------------

    async def _results_av(self, election) -> ElectionResultResponse:
        """Alternative Vote: single-seat constituencies with ranked preferences.

        Votes are counted in rounds. If no candidate has >50%, the lowest
        candidate is eliminated and their votes transferred to next preferences.
        """
        election_id = election.id
        result = await self.session.execute(
            select(Vote).where(Vote.election_id == election_id).order_by(
                Vote.blind_token_hash, Vote.preference_rank
            )
        )
        votes = list(result.scalars().all())

        # Group votes by constituency, then by ballot
        ballots_by_constituency: dict[UUID, list[list[UUID]]] = defaultdict(list)
        ballot_buffer: dict[str, list[tuple[int, UUID]]] = defaultdict(list)

        for v in votes:
            if not v.constituency_id or not v.candidate_id or v.preference_rank is None:
                continue
            base_token = v.blind_token_hash.split(":rank")[0]
            key = f"{v.constituency_id}:{base_token}"
            ballot_buffer[key].append((v.preference_rank, v.candidate_id))

        for key, prefs in ballot_buffer.items():
            cid_str = key.split(":")[0]
            cid = UUID(cid_str)
            ordered = [cand_id for _, cand_id in sorted(prefs, key=lambda x: x[0])]
            ballots_by_constituency[cid].append(ordered)

        all_candidate_ids = {
            cand_id for ballots in ballots_by_constituency.values()
            for ballot in ballots for cand_id in ballot
        }
        candidate_party_map = await self._load_candidate_party_map(all_candidate_ids)

        constituency_results = []
        seat_allocation: dict[str, int] = defaultdict(int)
        total_votes = 0

        for cid, ballots in ballots_by_constituency.items():
            total_votes += len(ballots)
            winner = self._av_count(ballots)

            first_pref_counts: dict[UUID, int] = defaultdict(int)
            for ballot in ballots:
                if ballot:
                    first_pref_counts[ballot[0]] += 1
            tally_dtos = [
                TallyResultDTO(
                    id=None,
                    election_id=election_id,
                    constituency_id=cid,
                    candidate_id=cand_id,
                    vote_count=count,
                )
                for cand_id, count in sorted(
                    first_pref_counts.items(), key=lambda x: -x[1]
                )
            ]

            winner_party_id = (
                candidate_party_map.get(winner) if winner else None
            )

            cr = ConstituencyResultDTO(
                constituency_id=cid,
                winner_candidate_id=winner,
                winner_party_id=winner_party_id,
                total_votes=len(ballots),
                tallies=tally_dtos,
            )
            constituency_results.append(cr)

            if winner_party_id:
                seat_allocation[str(winner_party_id)] += 1

        total_seats = len(ballots_by_constituency)
        majority_threshold = total_seats // 2 + 1

        winning_party_id = None
        for party_id, seats in seat_allocation.items():
            if seats >= majority_threshold:
                winning_party_id = party_id
                break

        result_dto = ElectionResultDTO(
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
        return result_dto.to_schema()

    @staticmethod
    def _av_count(ballots: list[list[UUID]]) -> UUID | None:
        """Run AV counting for a single seat.

        Eliminates the lowest candidate each round and transfers votes
        until a candidate has >50%.
        """
        if not ballots:
            return None

        active_ballots = [list(b) for b in ballots if b]
        eliminated: set[UUID] = set()

        while True:
            counts: dict[UUID, int] = defaultdict(int)
            for prefs in active_ballots:
                for cand in prefs:
                    if cand not in eliminated:
                        counts[cand] += 1
                        break

            if not counts:
                return None

            total = sum(counts.values())
            majority = total / 2

            # Check if any candidate has >50%
            for cand, votes in counts.items():
                if votes > majority:
                    return cand

            # Eliminate lowest
            lowest = min(counts, key=counts.get)
            eliminated.add(lowest)

            # If only one candidate left, they win
            remaining = [c for c in counts if c not in eliminated]
            if len(remaining) <= 1:
                return remaining[0] if remaining else None
