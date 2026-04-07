// audit-report.model.ts - Models for privacy-safe audit reports.

export interface AuditTimelineEvent {
    timestamp: string;
    event_type: string;
    summary: string;
}

export interface InvestigationSummaryItem {
    id: string;
    title: string;
    status: string;
    severity: string;
    description: string | null;
    raised_at: string | null;
    resolved_at: string | null;
}

export interface ConstituencyTurnoutItem {
    constituency_id: string;
    constituency_name: string;
    votes_cast: number;
}

export interface BallotReconciliationItem {
    constituency_id: string;
    constituency_name: string;
    tokens_issued: number;
    tokens_used: number;
    votes_recorded: number;
}

export interface BallotReconciliationSummary {
    tokens_issued: number;
    tokens_used: number;
    votes_recorded: number;
    voter_ledger_entries: number;
    fully_reconciled: boolean;
    per_constituency: BallotReconciliationItem[];
}

export interface VotingPeriodIntegrity {
    voting_opens: string | null;
    voting_closes: string | null;
    earliest_vote: string | null;
    latest_vote: string | null;
    all_votes_within_window: boolean;
}

export interface BiometricVerificationSummary {
    challenges_issued: number;
    challenges_completed: number;
    challenges_expired: number;
}

export interface ElectionAuditReport {
    election_id: string;
    title: string;
    election_type: string;
    allocation_method: string;
    scope: string;
    status: string;
    voting_opens: string | null;
    voting_closes: string | null;
    created_at: string | null;
    total_votes_cast: number;
    total_constituencies: number;
    constituency_turnout: ConstituencyTurnoutItem[];
    ballot_reconciliation: BallotReconciliationSummary;
    voting_period_integrity: VotingPeriodIntegrity;
    biometric_summary: BiometricVerificationSummary;
    total_seats: number;
    majority_threshold: number;
    seat_allocation: Record<string, number>;
    winning_party_id: string | null;
    event_counts: Record<string, number>;
    timeline: AuditTimelineEvent[];
    investigations: InvestigationSummaryItem[];
    generated_at: string;
    generated_by: string | null;
}

export interface ReferendumAuditReport {
    referendum_id: string;
    title: string;
    question: string;
    scope: string;
    status: string;
    voting_opens: string | null;
    voting_closes: string | null;
    created_at: string | null;
    total_votes_cast: number;
    yes_votes: number;
    no_votes: number;
    outcome: string;
    ballot_reconciliation: BallotReconciliationSummary;
    voting_period_integrity: VotingPeriodIntegrity;
    biometric_summary: BiometricVerificationSummary;
    event_counts: Record<string, number>;
    timeline: AuditTimelineEvent[];
    investigations: InvestigationSummaryItem[];
    generated_at: string;
    generated_by: string | null;
}
