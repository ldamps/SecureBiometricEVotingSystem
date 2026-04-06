# audit_report_service.py - Generates aggregated, privacy-safe audit reports.
# These reports contain NO voter-identifiable information — no individual
# vote events, ballot tokens, or biometric records linked to voters.

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas.audit_report import (
    AuditTimelineEvent,
    BallotReconciliationItem,
    BallotReconciliationSummary,
    BiometricVerificationSummary,
    ConstituencyTurnoutItem,
    ElectionAuditReportResponse,
    InvestigationSummaryItem,
    ReferendumAuditReportResponse,
    VotingPeriodIntegrity,
)
from app.models.sqlalchemy.audit_log import AuditLog
from app.models.sqlalchemy.ballot_token import BallotToken
from app.models.sqlalchemy.biometric_credentials import BiometricChallenge
from app.models.sqlalchemy.constituency import Constituency
from app.models.sqlalchemy.election import Election
from app.models.sqlalchemy.investigation import Investigation
from app.models.sqlalchemy.referendum import Referendum
from app.models.sqlalchemy.referendum_vote import ReferendumVote
from app.models.sqlalchemy.tally_result import TallyResult
from app.models.sqlalchemy.vote import Vote
from app.models.sqlalchemy.voter_ledger import VoterLedger
from app.repository.election_repo import ElectionRepository
from app.repository.referendum_repo import ReferendumRepository

logger = structlog.get_logger()

# Event types safe to include in the audit timeline (no voter PII).
_TIMELINE_EVENT_TYPES = frozenset({
    "ELECTION_CREATED",
    "ELECTION_UPDATED",
    "ELECTION_STATUS_CHANGED",
    "CANDIDATE_ADDED",
    "CANDIDATE_REMOVED",
    "OFFICIAL_CREATED",
    "OFFICIAL_LOGIN",
    "OFFICIAL_LOGIN_FAILED",
    "OFFICIAL_LOGOUT",
    "ERROR_REPORT_CREATED",
    "INVESTIGATION_OPENED",
    "INVESTIGATION_UPDATED",
    "INVESTIGATION_RESOLVED",
    "SYSTEM_ERROR",
    "PERMISSION_DENIED",
    "DATA_EXPORT",
})


class AuditReportService:
    """Builds aggregated, privacy-safe audit reports for elections and referendums."""

    def __init__(
        self,
        election_repo: ElectionRepository,
        referendum_repo: ReferendumRepository,
        session: AsyncSession,
    ):
        self.election_repo = election_repo
        self.referendum_repo = referendum_repo
        self.session = session

    async def generate_election_report(
        self, election_id: UUID, generated_by: UUID | None = None,
    ) -> ElectionAuditReportResponse:
        """Build an election audit report with aggregated, privacy-safe data."""
        election = await self.election_repo.get_election_by_id(self.session, election_id)

        # Aggregate event counts
        event_counts = await self._get_event_counts_by_election(election_id)

        # System timeline (non-voter events only)
        timeline = await self._get_timeline_by_election(election_id)

        # Turnout per constituency (from tally_result aggregate, no voter PII)
        constituency_turnout = await self._get_constituency_turnout(election_id)

        # Total votes from voter ledger
        total_votes = await self._count_votes_by_election(election_id)

        # Result summary from tally_result
        seat_allocation, total_seats = await self._get_seat_summary(election_id)
        majority_threshold = total_seats // 2 + 1 if total_seats > 0 else 0

        winning_party_id = None
        for party_id, seats in seat_allocation.items():
            if seats >= majority_threshold:
                winning_party_id = party_id
                break

        # Ballot reconciliation
        ballot_reconciliation = await self._get_ballot_reconciliation_election(
            election_id, total_votes,
        )

        # Voting period integrity
        voting_period = await self._get_voting_period_election(election)

        # Biometric verification aggregates
        biometric_summary = await self._get_biometric_summary()

        # Investigations
        investigations = await self._get_investigations_by_election(election_id)

        return ElectionAuditReportResponse(
            election_id=str(election_id),
            title=election.title,
            election_type=election.election_type,
            allocation_method=election.allocation_method,
            scope=election.scope,
            status=election.status,
            voting_opens=election.voting_opens,
            voting_closes=election.voting_closes,
            created_at=election.created_at,
            total_votes_cast=total_votes,
            total_constituencies=len(constituency_turnout),
            constituency_turnout=constituency_turnout,
            ballot_reconciliation=ballot_reconciliation,
            voting_period_integrity=voting_period,
            biometric_summary=biometric_summary,
            total_seats=total_seats,
            majority_threshold=majority_threshold,
            seat_allocation=seat_allocation,
            winning_party_id=winning_party_id,
            event_counts=event_counts,
            timeline=timeline,
            investigations=investigations,
            generated_at=datetime.now(timezone.utc),
            generated_by=str(generated_by) if generated_by else None,
        )

    async def generate_referendum_report(
        self, referendum_id: UUID, generated_by: UUID | None = None,
    ) -> ReferendumAuditReportResponse:
        """Build a referendum audit report with aggregated, privacy-safe data."""
        referendum = await self.referendum_repo.get_referendum_by_id(
            self.session, referendum_id,
        )

        event_counts = await self._get_event_counts_by_referendum(referendum_id)
        timeline = await self._get_timeline_by_referendum(referendum_id)
        total_votes = await self._count_votes_by_referendum(referendum_id)
        yes_votes, no_votes, outcome = await self._get_referendum_tally(referendum_id)

        # Ballot reconciliation
        ballot_reconciliation = await self._get_ballot_reconciliation_referendum(
            referendum_id, total_votes,
        )

        # Voting period integrity
        voting_period = await self._get_voting_period_referendum(referendum)

        # Biometric verification aggregates
        biometric_summary = await self._get_biometric_summary()

        investigations = await self._get_investigations_by_election(referendum_id)

        return ReferendumAuditReportResponse(
            referendum_id=str(referendum_id),
            title=referendum.title,
            question=referendum.question,
            scope=referendum.scope,
            status=referendum.status,
            voting_opens=referendum.voting_opens,
            voting_closes=referendum.voting_closes,
            created_at=referendum.created_at,
            total_votes_cast=total_votes,
            yes_votes=yes_votes,
            no_votes=no_votes,
            outcome=outcome,
            ballot_reconciliation=ballot_reconciliation,
            voting_period_integrity=voting_period,
            biometric_summary=biometric_summary,
            event_counts=event_counts,
            timeline=timeline,
            investigations=investigations,
            generated_at=datetime.now(timezone.utc),
            generated_by=str(generated_by) if generated_by else None,
        )

    # ------------------------------------------------------------------
    # Private helpers — all queries return aggregated data, never voter PII
    # ------------------------------------------------------------------

    async def _get_event_counts_by_election(self, election_id: UUID) -> dict[str, int]:
        result = await self.session.execute(
            select(AuditLog.event_type, func.count())
            .where(AuditLog.election_id == election_id)
            .group_by(AuditLog.event_type)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _get_event_counts_by_referendum(self, referendum_id: UUID) -> dict[str, int]:
        result = await self.session.execute(
            select(AuditLog.event_type, func.count())
            .where(AuditLog.referendum_id == referendum_id)
            .group_by(AuditLog.event_type)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _get_timeline_by_election(self, election_id: UUID) -> list[AuditTimelineEvent]:
        result = await self.session.execute(
            select(AuditLog.created_at, AuditLog.event_type, AuditLog.summary)
            .where(
                AuditLog.election_id == election_id,
                AuditLog.event_type.in_(_TIMELINE_EVENT_TYPES),
            )
            .order_by(AuditLog.created_at.asc())
        )
        return [
            AuditTimelineEvent(timestamp=row[0], event_type=row[1], summary=row[2])
            for row in result.all()
        ]

    async def _get_timeline_by_referendum(self, referendum_id: UUID) -> list[AuditTimelineEvent]:
        result = await self.session.execute(
            select(AuditLog.created_at, AuditLog.event_type, AuditLog.summary)
            .where(
                AuditLog.referendum_id == referendum_id,
                AuditLog.event_type.in_(_TIMELINE_EVENT_TYPES),
            )
            .order_by(AuditLog.created_at.asc())
        )
        return [
            AuditTimelineEvent(timestamp=row[0], event_type=row[1], summary=row[2])
            for row in result.all()
        ]

    async def _count_votes_by_election(self, election_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(VoterLedger)
            .where(VoterLedger.election_id == election_id)
        )
        return result.scalar_one()

    async def _count_votes_by_referendum(self, referendum_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(VoterLedger)
            .where(VoterLedger.referendum_id == referendum_id)
        )
        return result.scalar_one()

    async def _get_constituency_turnout(self, election_id: UUID) -> list[ConstituencyTurnoutItem]:
        result = await self.session.execute(
            select(
                TallyResult.constituency_id,
                func.sum(TallyResult.vote_count),
            )
            .where(
                TallyResult.election_id == election_id,
                TallyResult.constituency_id.isnot(None),
            )
            .group_by(TallyResult.constituency_id)
        )
        rows = result.all()
        if not rows:
            return []

        # Batch-load constituency names
        cids = [row[0] for row in rows]
        name_result = await self.session.execute(
            select(Constituency.id, Constituency.name).where(Constituency.id.in_(cids))
        )
        name_map = {r[0]: r[1] for r in name_result.all()}

        return [
            ConstituencyTurnoutItem(
                constituency_id=str(cid),
                constituency_name=name_map.get(cid, str(cid)[:8]),
                votes_cast=int(total),
            )
            for cid, total in rows
        ]

    async def _get_seat_summary(self, election_id: UUID) -> tuple[dict[str, int], int]:
        """Return (seat_allocation, total_seats) from tally data.

        Uses simple max-vote-per-constituency logic (FPTP).
        For full electoral-system-aware results, use the ResultService.
        This is a simplified summary for the audit report.
        """
        result = await self.session.execute(
            select(TallyResult)
            .where(
                TallyResult.election_id == election_id,
                TallyResult.constituency_id.isnot(None),
                TallyResult.candidate_id.isnot(None),
            )
            .order_by(TallyResult.vote_count.desc())
        )
        tallies = result.scalars().all()

        # Group by constituency, pick winner
        by_constituency: dict[UUID, list] = defaultdict(list)
        for t in tallies:
            by_constituency[t.constituency_id].append(t)

        seat_allocation: dict[str, int] = defaultdict(int)
        for cid, ctallies in by_constituency.items():
            winner = ctallies[0]  # already sorted desc
            if winner.party_id:
                seat_allocation[str(winner.party_id)] += 1
            elif winner.candidate_id:
                # Try to get party from candidate (already in tally)
                seat_allocation[str(winner.candidate_id)] += 1

        return dict(seat_allocation), len(by_constituency)

    async def _get_referendum_tally(self, referendum_id: UUID) -> tuple[int, int, str]:
        result = await self.session.execute(
            select(TallyResult.choice, TallyResult.vote_count)
            .where(TallyResult.referendum_id == referendum_id)
        )
        yes_votes = 0
        no_votes = 0
        for choice, count in result.all():
            if choice == "YES":
                yes_votes += count
            elif choice == "NO":
                no_votes += count

        if yes_votes > no_votes:
            outcome = "YES"
        elif no_votes > yes_votes:
            outcome = "NO"
        else:
            outcome = "TIE"

        return yes_votes, no_votes, outcome

    async def _get_investigations_by_election(
        self, election_id: UUID,
    ) -> list[InvestigationSummaryItem]:
        result = await self.session.execute(
            select(
                Investigation.id,
                Investigation.title,
                Investigation.status,
                Investigation.severity,
                Investigation.description,
                Investigation.raised_at,
                Investigation.resolved_at,
            )
            .where(Investigation.election_id == election_id)
            .order_by(Investigation.raised_at.desc())
        )
        return [
            InvestigationSummaryItem(
                id=str(row[0]),
                title=row[1],
                status=row[2],
                severity=row[3],
                description=row[4],
                raised_at=row[5],
                resolved_at=row[6],
            )
            for row in result.all()
        ]

    # ------------------------------------------------------------------
    # Ballot reconciliation
    # ------------------------------------------------------------------

    async def _get_ballot_reconciliation_election(
        self, election_id: UUID, voter_ledger_count: int,
    ) -> BallotReconciliationSummary:
        """Compare tokens issued, tokens used, votes recorded, and ledger entries."""
        # Total tokens issued / used
        total_q = select(func.count()).select_from(BallotToken).where(
            BallotToken.election_id == election_id,
        )
        used_q = select(func.count()).select_from(BallotToken).where(
            BallotToken.election_id == election_id, BallotToken.is_used.is_(True),
        )
        tokens_issued = (await self.session.execute(total_q)).scalar_one()
        tokens_used = (await self.session.execute(used_q)).scalar_one()

        # Votes recorded (from vote table, not tally — actual row count)
        votes_q = select(func.count()).select_from(Vote).where(
            Vote.election_id == election_id,
        )
        votes_recorded = (await self.session.execute(votes_q)).scalar_one()

        # Per-constituency breakdown
        per_constituency = await self._get_per_constituency_reconciliation(election_id)

        fully_reconciled = (
            tokens_used == voter_ledger_count
            and tokens_used <= tokens_issued
        )

        return BallotReconciliationSummary(
            tokens_issued=tokens_issued,
            tokens_used=tokens_used,
            votes_recorded=votes_recorded,
            voter_ledger_entries=voter_ledger_count,
            fully_reconciled=fully_reconciled,
            per_constituency=per_constituency,
        )

    async def _get_per_constituency_reconciliation(
        self, election_id: UUID,
    ) -> list[BallotReconciliationItem]:
        """Per-constituency: tokens issued vs used vs votes recorded."""
        # Tokens per constituency
        token_q = (
            select(
                BallotToken.constituency_id,
                func.count(),
                func.count().filter(BallotToken.is_used.is_(True)),
            )
            .where(
                BallotToken.election_id == election_id,
                BallotToken.constituency_id.isnot(None),
            )
            .group_by(BallotToken.constituency_id)
        )
        token_rows = (await self.session.execute(token_q)).all()

        # Votes per constituency
        vote_q = (
            select(Vote.constituency_id, func.count())
            .where(
                Vote.election_id == election_id,
                Vote.constituency_id.isnot(None),
            )
            .group_by(Vote.constituency_id)
        )
        vote_rows = (await self.session.execute(vote_q)).all()
        vote_map = {row[0]: row[1] for row in vote_rows}

        # Constituency names
        all_cids = [row[0] for row in token_rows]
        name_map: dict[UUID, str] = {}
        if all_cids:
            name_result = await self.session.execute(
                select(Constituency.id, Constituency.name).where(
                    Constituency.id.in_(all_cids)
                )
            )
            name_map = {r[0]: r[1] for r in name_result.all()}

        return [
            BallotReconciliationItem(
                constituency_id=str(cid),
                constituency_name=name_map.get(cid, str(cid)[:8]),
                tokens_issued=issued,
                tokens_used=used,
                votes_recorded=vote_map.get(cid, 0),
            )
            for cid, issued, used in token_rows
        ]

    async def _get_ballot_reconciliation_referendum(
        self, referendum_id: UUID, voter_ledger_count: int,
    ) -> BallotReconciliationSummary:
        total_q = select(func.count()).select_from(BallotToken).where(
            BallotToken.referendum_id == referendum_id,
        )
        used_q = select(func.count()).select_from(BallotToken).where(
            BallotToken.referendum_id == referendum_id, BallotToken.is_used.is_(True),
        )
        tokens_issued = (await self.session.execute(total_q)).scalar_one()
        tokens_used = (await self.session.execute(used_q)).scalar_one()

        votes_q = select(func.count()).select_from(ReferendumVote).where(
            ReferendumVote.referendum_id == referendum_id,
        )
        votes_recorded = (await self.session.execute(votes_q)).scalar_one()

        fully_reconciled = (
            tokens_used == voter_ledger_count
            and tokens_used <= tokens_issued
        )

        return BallotReconciliationSummary(
            tokens_issued=tokens_issued,
            tokens_used=tokens_used,
            votes_recorded=votes_recorded,
            voter_ledger_entries=voter_ledger_count,
            fully_reconciled=fully_reconciled,
        )

    # ------------------------------------------------------------------
    # Voting period integrity
    # ------------------------------------------------------------------

    async def _get_voting_period_election(self, election) -> VotingPeriodIntegrity:
        """Check that all votes were cast within the voting window."""
        result = await self.session.execute(
            select(func.min(Vote.cast_at), func.max(Vote.cast_at))
            .where(Vote.election_id == election.id)
        )
        row = result.one()
        earliest, latest = row[0], row[1]

        within_window = True
        if earliest and election.voting_opens:
            if earliest < election.voting_opens:
                within_window = False
        if latest and election.voting_closes:
            if latest > election.voting_closes:
                within_window = False

        return VotingPeriodIntegrity(
            voting_opens=election.voting_opens,
            voting_closes=election.voting_closes,
            earliest_vote=earliest,
            latest_vote=latest,
            all_votes_within_window=within_window,
        )

    async def _get_voting_period_referendum(self, referendum) -> VotingPeriodIntegrity:
        result = await self.session.execute(
            select(func.min(ReferendumVote.cast_at), func.max(ReferendumVote.cast_at))
            .where(ReferendumVote.referendum_id == referendum.id)
        )
        row = result.one()
        earliest, latest = row[0], row[1]

        within_window = True
        if earliest and referendum.voting_opens:
            if earliest < referendum.voting_opens:
                within_window = False
        if latest and referendum.voting_closes:
            if latest > referendum.voting_closes:
                within_window = False

        return VotingPeriodIntegrity(
            voting_opens=referendum.voting_opens,
            voting_closes=referendum.voting_closes,
            earliest_vote=earliest,
            latest_vote=latest,
            all_votes_within_window=within_window,
        )

    # ------------------------------------------------------------------
    # Biometric verification aggregates
    # ------------------------------------------------------------------

    async def _get_biometric_summary(self) -> BiometricVerificationSummary:
        """Aggregate biometric challenge statistics (system-wide, no voter PII)."""
        total_q = select(func.count()).select_from(BiometricChallenge)
        completed_q = select(func.count()).select_from(BiometricChallenge).where(
            BiometricChallenge.is_used.is_(True),
        )
        expired_q = select(func.count()).select_from(BiometricChallenge).where(
            BiometricChallenge.is_used.is_(False),
            BiometricChallenge.expires_at < func.now(),
        )

        issued = (await self.session.execute(total_q)).scalar_one()
        completed = (await self.session.execute(completed_q)).scalar_one()
        expired = (await self.session.execute(expired_q)).scalar_one()

        return BiometricVerificationSummary(
            challenges_issued=issued,
            challenges_completed=completed,
            challenges_expired=expired,
        )
