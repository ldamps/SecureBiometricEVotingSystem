// result-api.repository.ts - Result API repository

import { ApiClient } from "../../../services/api-client.service";
import {
    ConstituencyResult,
    ElectionResult,
    ReferendumResult,
    TallyResult,
} from "../model/result.model";

const ELECTION_ROOT = "/election";
const REFERENDUM_ROOT = "/referendum";

interface BackendTallyResultItem {
    id: string;
    election_id?: string | null;
    constituency_id?: string | null;
    candidate_id?: string | null;
    party_id?: string | null;
    referendum_id?: string | null;
    choice?: string | null;
    vote_count: number;
    tallied_at?: string | null;
}

interface BackendConstituencyResultItem {
    id?: string;
    constituency_id: string;
    winner_candidate_id?: string | null;
    winner_name?: string | null;
    winner_party_id?: string | null;
    total_votes: number;
    tallies: BackendTallyResultItem[];
}

interface BackendElectionResultItem {
    id?: string;
    election_id: string;
    election_title?: string | null;
    status: string;
    total_votes: number;
    total_seats: number;
    majority_threshold: number;
    constituencies: BackendConstituencyResultItem[];
    seat_allocation: Record<string, number>;
    winning_party_id?: string | null;
}

interface BackendReferendumResultItem {
    id?: string;
    referendum_id: string;
    yes_votes: number;
    no_votes: number;
    total_votes: number;
    outcome: string;
}

function mapTallyResult(b: BackendTallyResultItem): TallyResult {
    return {
        id: b.id,
        election_id: b.election_id ?? "",
        constituency_id: b.constituency_id ?? "",
        candidate_id: b.candidate_id ?? "",
        party_id: b.party_id ?? "",
        referendum_id: b.referendum_id ?? "",
        choice: b.choice ?? "",
        vote_count: b.vote_count,
        tallied_at: b.tallied_at ?? "",
    };
}

function mapConstituencyResult(b: BackendConstituencyResultItem): ConstituencyResult {
    return {
        id: b.id ?? b.constituency_id,
        constituency_id: b.constituency_id,
        winner_candidate_id: b.winner_candidate_id ?? "",
        winner_name: b.winner_name ?? "",
        winner_party_id: b.winner_party_id ?? "",
        total_votes: b.total_votes,
        tallies: (b.tallies ?? []).map(mapTallyResult),
    };
}

function mapElectionResult(b: BackendElectionResultItem): ElectionResult {
    return {
        id: b.id ?? b.election_id,
        election_id: b.election_id,
        election_title: b.election_title ?? "",
        status: b.status,
        total_votes: b.total_votes,
        total_seats: b.total_seats,
        majority_threshold: b.majority_threshold,
        constituencies: (b.constituencies ?? []).map(mapConstituencyResult),
        seat_allocation: b.seat_allocation ?? {},
        winning_party_id: b.winning_party_id ?? "",
    };
}

function mapReferendumResult(b: BackendReferendumResultItem): ReferendumResult {
    return {
        id: b.id ?? b.referendum_id,
        referendum_id: b.referendum_id,
        yes_votes: b.yes_votes,
        no_votes: b.no_votes,
        total_votes: b.total_votes,
        outcome: b.outcome,
    };
}

export class ResultApiRepository {
    /** Aggregated election results (authenticated official). */
    async getElectionResults(electionId: string): Promise<ElectionResult> {
        const raw = await ApiClient.get<BackendElectionResultItem>(
            `${ELECTION_ROOT}/${electionId}/results`,
        );
        return mapElectionResult(raw);
    }

    /** Aggregated referendum results (authenticated official). */
    async getReferendumResults(referendumId: string): Promise<ReferendumResult> {
        const raw = await ApiClient.get<BackendReferendumResultItem>(
            `${REFERENDUM_ROOT}/${referendumId}/results`,
        );
        return mapReferendumResult(raw);
    }

    /** All vote tallies for an election (admin). */
    async getElectionTallies(electionId: string): Promise<TallyResult[]> {
        const rows = await ApiClient.get<BackendTallyResultItem[]>(
            `${ELECTION_ROOT}/${electionId}/tallies`,
        );
        return rows.map(mapTallyResult);
    }

    /** Tallies for one constituency within an election (admin). */
    async getElectionConstituencyTallies(
        electionId: string,
        constituencyId: string,
    ): Promise<TallyResult[]> {
        const rows = await ApiClient.get<BackendTallyResultItem[]>(
            `${ELECTION_ROOT}/${electionId}/constituency/${constituencyId}/tallies`,
        );
        return rows.map(mapTallyResult);
    }

    /** YES/NO tallies for a referendum (admin). */
    async getReferendumTallies(referendumId: string): Promise<TallyResult[]> {
        const rows = await ApiClient.get<BackendTallyResultItem[]>(
            `${REFERENDUM_ROOT}/${referendumId}/tallies`,
        );
        return rows.map(mapTallyResult);
    }
}
