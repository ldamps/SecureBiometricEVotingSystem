// voting-api.repository.ts - Voting API repository for casting votes

import { ApiClient } from "../../../services/api-client.service";

const ROOT = "/voting";

export interface RankedPreference {
    candidate_id: string;
    preference_rank: number;
}

export interface CastElectionVoteRequest {
    voter_id: string;
    election_id: string;
    constituency_id?: string;
    candidate_id?: string;
    party_id?: string;
    ranked_preferences?: RankedPreference[];
    send_email_confirmation: boolean;
}

export interface CastElectionVoteResponse {
    receipt_code: string;
    election_id: string;
    cast_at?: string;
    message: string;
}

export interface CastReferendumVoteRequest {
    voter_id: string;
    referendum_id: string;
    choice: string;
    send_email_confirmation: boolean;
}

export interface CastReferendumVoteResponse {
    receipt_code: string;
    referendum_id: string;
    cast_at?: string;
    message: string;
}

export class VotingApiRepository {
    async castElectionVote(body: CastElectionVoteRequest): Promise<CastElectionVoteResponse> {
        return ApiClient.post<CastElectionVoteResponse>(`${ROOT}/vote`, body);
    }

    async castReferendumVote(body: CastReferendumVoteRequest): Promise<CastReferendumVoteResponse> {
        return ApiClient.post<CastReferendumVoteResponse>(`${ROOT}/vote-referendum`, body);
    }
}
