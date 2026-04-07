# audit_report.py - Schema for the aggregated, privacy-safe election audit report.
# Contains no voter-identifiable information (no individual vote events,
# no ballot tokens, no biometric records linked to voters).

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from app.models.base.pydantic_base import ResponseSchema


class AuditTimelineEvent(ResponseSchema):
    """A single system-level event in the audit timeline (no voter PII)."""
    timestamp: datetime
    event_type: str
    summary: str


class InvestigationSummaryItem(ResponseSchema):
    """Summary of an investigation for the audit report."""
    id: str
    title: str
    status: str
    severity: str
    description: Optional[str] = None
    raised_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class BallotReconciliationItem(ResponseSchema):
    """Per-constituency ballot reconciliation figures."""
    constituency_id: str
    constituency_name: str
    tokens_issued: int
    tokens_used: int
    votes_recorded: int


class ConstituencyTurnoutItem(ResponseSchema):
    """Per-constituency turnout figures."""
    constituency_id: str
    constituency_name: str
    votes_cast: int


class VotingPeriodIntegrity(ResponseSchema):
    """Confirms all votes fell within the scheduled voting window."""
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None
    earliest_vote: Optional[datetime] = None
    latest_vote: Optional[datetime] = None
    all_votes_within_window: bool = True


class BiometricVerificationSummary(ResponseSchema):
    """Aggregate biometric challenge statistics (no voter PII)."""
    challenges_issued: int = 0
    challenges_completed: int = 0
    challenges_expired: int = 0


class BallotReconciliationSummary(ResponseSchema):
    """Top-level ballot reconciliation totals."""
    tokens_issued: int = 0
    tokens_used: int = 0
    votes_recorded: int = 0
    voter_ledger_entries: int = 0
    fully_reconciled: bool = True
    per_constituency: List[BallotReconciliationItem] = Field(default_factory=list)


class ElectionAuditReportResponse(ResponseSchema):
    """Aggregated audit report for an election — privacy-safe, legally produceable."""

    # Election metadata
    election_id: str
    title: str
    election_type: str
    allocation_method: str
    scope: str
    status: str
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # Aggregate turnout
    total_votes_cast: int = 0
    total_constituencies: int = 0
    constituency_turnout: List[ConstituencyTurnoutItem] = Field(default_factory=list)

    # Ballot reconciliation
    ballot_reconciliation: BallotReconciliationSummary = Field(default_factory=BallotReconciliationSummary)

    # Voting period integrity
    voting_period_integrity: VotingPeriodIntegrity = Field(default_factory=VotingPeriodIntegrity)

    # Biometric verification summary
    biometric_summary: BiometricVerificationSummary = Field(default_factory=BiometricVerificationSummary)

    # Result summary
    total_seats: int = 0
    majority_threshold: int = 0
    seat_allocation: Dict[str, int] = Field(default_factory=dict)
    winning_party_id: Optional[str] = None

    # Aggregate event counts (e.g. {"VOTE_CAST": 1500, "OFFICIAL_LOGIN": 12})
    event_counts: Dict[str, int] = Field(default_factory=dict)

    # System timeline (election lifecycle + official actions only)
    timeline: List[AuditTimelineEvent] = Field(default_factory=list)

    # Investigations
    investigations: List[InvestigationSummaryItem] = Field(default_factory=list)

    # Report generation metadata
    generated_at: datetime
    generated_by: Optional[str] = None


class ReferendumAuditReportResponse(ResponseSchema):
    """Aggregated audit report for a referendum — privacy-safe, legally produceable."""

    # Referendum metadata
    referendum_id: str
    title: str
    question: str
    scope: str
    status: str
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # Aggregate turnout
    total_votes_cast: int = 0
    yes_votes: int = 0
    no_votes: int = 0
    outcome: str = ""

    # Ballot reconciliation
    ballot_reconciliation: BallotReconciliationSummary = Field(default_factory=BallotReconciliationSummary)

    # Voting period integrity
    voting_period_integrity: VotingPeriodIntegrity = Field(default_factory=VotingPeriodIntegrity)

    # Biometric verification summary
    biometric_summary: BiometricVerificationSummary = Field(default_factory=BiometricVerificationSummary)

    # Aggregate event counts
    event_counts: Dict[str, int] = Field(default_factory=dict)

    # System timeline
    timeline: List[AuditTimelineEvent] = Field(default_factory=list)

    # Investigations
    investigations: List[InvestigationSummaryItem] = Field(default_factory=list)

    # Report generation metadata
    generated_at: datetime
    generated_by: Optional[str] = None
